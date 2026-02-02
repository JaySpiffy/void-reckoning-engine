
import os
import sys
import time
import json
import csv
import queue
import shutil
import logging
import traceback
import datetime
import multiprocessing
import multiprocessing.pool
from multiprocessing import Queue, Manager
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Core Imports
from src.core.config import UNIVERSE_ROOT, REPORTS_DIR, set_active_universe, get_universe_config
from src.core.constants import FACTION_ABBREVIATIONS
from universes.base.universe_loader import UniverseLoader
# from datetime import datetime removed to prevent conflict with 'import datetime'
import time

# --- REFACTORED IMPORTS ---
from src.engine.runner.simulation_worker import run_single_campaign_wrapped, worker_init
from src.engine.runner.results_aggregator import ResultsAggregator
from src.engine.runner.progress_dashboard import ProgressDashboard
from src.reporting.cross_universe_reporter import CrossUniverseReporter
from src.reporting.indexer import ReportIndexer
from src.reporting.indexer import ReportIndexer
import sqlite3
from src.managers.fleet_queue_manager import FleetQueueManager # [Item 1.5]
from src.reporting.terminal_dashboard import TerminalDashboard

logger = logging.getLogger(__name__)

# --- Custom Pool for Nested Multiprocessing ---
# Standard multiprocessing.Pool workers are daemon processes and cannot spawn children.
# We need to subclass Process to make it non-daemon to allow _run_universe_batch to spawn its own Pool.

class NoDaemonProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass

class NoDaemonContext(type(multiprocessing.get_context())):
    def Process(self, *args, **kwds):
        proc = NoDaemonProcess(*args, **kwds)
        # Ensure it's not daemon
        proc._config['daemon'] = False 
        return proc

class NoDaemonPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super().__init__(*args, **kwargs)

# ----------------------------------------------

# ----------------------------------------------

# Module-level initializer to ensure picklability on Windows
def pool_worker_init(q, u_name, in_q=None, out_q=None):
    """
    Initializer for simulation worker pools.
    Sets the active universe context and initializes FleetQueueManager.
    """
    # 1. Standard Init (Queue)
    worker_init(q)
    
    # 2. Set Universe
    try:
        from src.core.config import set_active_universe
        set_active_universe(u_name)
    except ImportError:
         pass

    # 3. Set Fleet Queues [Item 1.5]
    if in_q and out_q:
        FleetQueueManager.initialize(in_q, out_q, progress_q=q)

class MultiUniverseRunner:
    """
    Orchestrates parallel execution of different universes on designated CPU cores.
    Each universe runs in its own process, which in turn manages a pool of simulation workers.
    """
    
    def __init__(self, universe_configs: List[Dict[str, Any]], multi_settings: Dict[str, Any] = None):
        """
        Initialize the runner with a list of universe configurations.
        
        Args:
            universe_configs: List of dicts, each containing:
                - universe_name: str
                - processor_affinity: List[int] (CPU cores)
                - num_runs: int
                - game_config: Dict (standard game config)
                - output_subdir: str (optional)
            multi_settings: Optional dict containing global simulation settings like 'sync_turns'.
        """
        self.universe_configs = universe_configs
        self.multi_settings = multi_settings or {}
        self.results = {} # universe_name -> [results]
        self.progress_queues = {} # universe_name -> Queue
        self.universe_queues = {} # universe_name -> {'incoming': Q, 'outgoing': Q}
        self.portal_registry = {} # universe_name -> [portals]
        
        # Validate Universes
        self._validate_universes()
        
        # Shared Manager for Queues
        self.manager = Manager()

        # Phase 22: Portal Registry
        self.portal_registry = self.manager.dict() # universe_name -> [serialized_portal_nodes]
        
        # Phase 23: Queue Registry for Portal Handoffs
        self.universe_queues: Dict[str, Dict[str, Queue]] = {}
        
        # Phase 24: Common Dashboard
        self.dashboard = TerminalDashboard()

    def _validate_universes(self):
        """Ensures all requested universes exist."""
        try:
            loader = UniverseLoader(UNIVERSE_ROOT)
            available = loader.discover_universes()
            available_names = set(available)
            
            for config in self.universe_configs:
                name = config.get("universe_name")
                if not name:
                    raise ValueError("Configuration missing 'universe_name'")
                if name not in available_names:
                    raise ValueError(f"Universe '{name}' not found. Available: {available_names}")
                
        except Exception as e:
            print(f"Universe Validation Failed: {e}")
            raise

    @staticmethod
    def _set_cpu_affinity(affinity_list: List[int]):
        """
        Sets the CPU affinity for the current process.
        Supported on Linux and Windows (via psutil).
        """
        if not affinity_list:
            return

        try:
            if sys.platform.startswith('linux'):
                os.sched_setaffinity(0, affinity_list)
            elif sys.platform == 'win32':
                try:
                    import psutil
                    p = psutil.Process()
                    p.cpu_affinity(affinity_list)
                except ImportError:
                    logger.warning("Warning: 'psutil' module required for CPU affinity on Windows.")
                except Exception as e:
                    logger.warning(f"Warning: CPU affinity not supported on {sys.platform}: {e}")
            else:
                logger.warning(f"Warning: CPU affinity not supported on {sys.platform}")
        except Exception as e:
            logger.error(f"Failed to set CPU affinity to {affinity_list}: {e}")

    @staticmethod
    def _run_universe_batch(universe_name: str, game_config: Dict, num_runs: int, 
                           output_dir: str, progress_queue: Queue, 
                           processor_affinity: Optional[List[int]] = None,
                           incoming_fleet_q: Optional[Queue] = None,
                           outgoing_fleet_q: Optional[Queue] = None) -> List[Dict]:
        """
        Worker function that runs a batch of simulations for a single universe.
        This runs in a child process of MultiUniverseRunner.
        """
        # 1. Set Affinity
        if processor_affinity:
            MultiUniverseRunner._set_cpu_affinity(processor_affinity)
        
        # 2. Set Universe Context
        set_active_universe(universe_name)
        
        # 3. Setup Directories
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        batch_dir = os.path.join(output_dir, universe_name, f"batch_{timestamp}")
        os.makedirs(batch_dir, exist_ok=True)
        
        # 4. Prepare Simulation Params
        # Extract params similar to run_batch_simulation
        sim_conf = game_config.get("simulation", {})
        camp_conf = game_config.get("campaign", {})
        eco_conf = game_config.get("economy", {})
        mech_conf = game_config.get("mechanics", {})
        
        turns = camp_conf.get("turns", 100)
        num_systems = camp_conf.get("num_systems", 20)
        
        # Hardware utilization for THIS universe batch
        # If we are isolated to N cores, we should use N workers
        workers = 1
        if processor_affinity:
            workers = len(processor_affinity)
        else:
            # Fallback if no affinity set, use 1 or modest number
            workers = max(1, multiprocessing.cpu_count() // 2)
            
        # 5. Execute Runs
        # We use a NoDaemonPool here to run the simulations for this universe in parallel across the assigned cores.
        # This allows workers to spawn their own sub-pools (e.g. for galaxy generation).
        pool = NoDaemonPool(
            processes=workers, 
            initializer=pool_worker_init, 
            initargs=(progress_queue, universe_name, incoming_fleet_q, outgoing_fleet_q)
        )
        
        tasks = []
        for i in range(num_runs):
            run_id = i + 1
            # Matches run_single_campaign_wrapped signature
            # run_id, turns_per_run, num_systems, batch_dir, min_p, max_p, combat_rounds, max_fleet, max_land, base_req, game_config
            task = (
                run_id,
                turns,
                num_systems,
                batch_dir,
                camp_conf.get("min_planets", 1),
                camp_conf.get("max_planets", 5),
                camp_conf.get("combat_rounds", 500),
                game_config.get("units", {}).get("max_fleet_size", 50),
                game_config.get("units", {}).get("max_land_army_size", 20),
                eco_conf.get("base_income_req", 1000),
                dict(game_config, universe=universe_name)
            )
            tasks.append(task)
            
        try:
            # We map to the function imported from simulation_runner.
            # NOTE: run_single_campaign_wrapped is not exported in __all__, so we import logic directly
            # and wrap it inside a lambda or helper if needed. 
            # Actually we can import run_single_campaign_wrapped if we make it importable,
            # or replicate the wrapper.
            
            # Using run_single_campaign_logic directly requires unpacking args.
            # simulation_runner has run_single_campaign_wrapped which unpacks.
            
            results_async = pool.map_async(run_single_campaign_wrapped, tasks)
            results = results_async.get()
            
            # Save Batch Stats
            stats_file = os.path.join(output_dir, universe_name, f"{universe_name}_batch_stats.csv")
            # (Saving logic is handled in aggregate, but we can dump here too)
            
            # Phase 23: Process Fleet Queues (Basic Implementation)
            # This batch runner is transient, but while it's running it could handle injection/removal?
            # Actually, the injection/removal needs to happen INSIDE the simulation logic (run_single_campaign_logic).
            # But run_single_campaign_logic is wrapped. 
            # We updated pool_worker_init to set global queues.
            # The CampaignEngine needs to check these globals if passed.
            
            # However, since we are using a Pool, the simulation logic runs in workers.
            # The batch runner itself is just a supervisor.
            # So the queues are passed to workers via initargs -> globals.
            # CampaignEngine will look for these globals or have them injected.
            
            pool.close()
            pool.join()
            
            return results
            
        except Exception as e:
            tb = traceback.format_exc()
            crash_file = os.path.join(output_dir, universe_name, "crash_log.txt")
            try:
                os.makedirs(os.path.dirname(crash_file), exist_ok=True)
                with open(crash_file, "w") as f:
                    f.write(f"CRASH AT {datetime.datetime.now()}\n")
                    f.write(tb)
            except:
                pass
                
            progress_queue.put((0, 0, f"Error: {str(e)[:50]}...", {"full_error": str(e), "traceback": tb}))
            traceback.print_exc() # Still print to stderr just in case
            pool.terminate()
            return []

    def _draw_multi_universe_dashboard(self, output_dir: str):
        """
        Renders the aggregated progress of all running universes.
        """
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=== MULTI-UNIVERSE SIMULATION DASHBOARD ===")
        print(f"Output: {output_dir}")
        print("-" * 60)
        
        all_done = True
        
        for config in self.universe_configs:
            name = config["universe_name"]
            num_runs = config["num_runs"]
            affinity = config.get("processor_affinity", [])
            q = self.progress_queues.get(name)
            
            # Process Queue Updates
            # We don't have a persistent local state here easily unless we store it in self.results or similar.
            # Ideally this method runs in a loop.
            # For simplicity, we just peek/track in the run_parallel loop.
            # Let's defer data collection to run_parallel and keep this strictly for rendering.
            pass

    def run_parallel(self, output_dir: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Main execution entry point.
        """
        # 1. Setup Queues
        for config in self.universe_configs:
            u_name = config["universe_name"]
            self.progress_queues[u_name] = self.manager.Queue()
            
            # Phase 23: Fleet Hand-off Queues
            self.universe_queues[u_name] = {
                "incoming": self.manager.Queue(),
                "outgoing": self.manager.Queue()
            }

        # 1.5 Pre-flight Registry Building (Avoid Race Conditions)
        print("Pre-flight: Building registries for all universes...")
        for config in self.universe_configs:
            u_name = config["universe_name"]
            try:
                from src.utils.registry_builder import build_all_registries
                build_all_registries(universe_name=u_name, verbose=False)
            except Exception as e:
                logger.warning(f"Warning: Failed to build registries for {u_name}: {e}")

        # 2. Setup Process Pool (One per Universe)
        # Using NoDaemonPool to allow children pools
        pool = NoDaemonPool(processes=len(self.universe_configs))
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_dir:
            self.output_dir = output_dir
        else:
            self.output_dir = os.path.join(REPORTS_DIR, f"multi_universe_{timestamp}")
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 3. Submit Tasks
        async_results = {}
        for config in self.universe_configs:
            name = config["universe_name"]
            res = pool.apply_async(
                MultiUniverseRunner._run_universe_batch,
                args=(
                    name,
                    config["game_config"],
                    config["num_runs"],
                    self.output_dir,
                    self.progress_queues[name], # Comment 1: Ensure unique and correct position, removed dup
                    config.get("processor_affinity"),
                    self.universe_queues[name]["incoming"],
                    self.universe_queues[name]["outgoing"]
                )
            )
            async_results[name] = res
            
        print(f"Started parallel execution for {len(self.universe_configs)} universes.")
        
        # 4. Global Topology Phase (Portals)
        # We wait for galaxy generation to finish in all universes before linking.
        # This requires a synchronization point. For now, we add logic to wait 
        # for a specific 'GALAXY_READY' message in the queue.
        # OR we can let universes register portals.
        
        # 4. Monitor Loop
        universe_progress = {
            name: {"completed": 0, "runs": {}} 
            for name in self.progress_queues
        }
        
        ready_universes = set()
        current_sync_turn = 0
        sync_enabled = self.multi_settings.get("sync_turns", False)
        
        try:
            while any(not r.ready() for r in async_results.values()):
                # Drain Queues
                for name, q in self.progress_queues.items():
                    while not q.empty():
                        try:
                            # Msg: (run_id, value, status, optional_stats)
                            # Msg: (run_id, value, status, optional_stats)
                            msg = q.get_nowait()
                            run_id = msg[0]
                            turn = msg[1]
                            status = msg[2]
                            payload = msg[3] if len(msg) > 3 else {}
                            
                            # Phase 22: Portal Sync (Special Event)
                            if status == "GALAXY_READY":
                                portals = payload if isinstance(payload, list) else []
                                self.portal_registry[name] = portals
                                print(f"  > [PORTAL_SYNC] Universe '{name}' registered {len(portals)} portals.")
                                self._attempt_portal_linking()
                                
                                # Track Readiness
                                ready_universes.add(name)
                                if len(ready_universes) >= len(self.progress_queues): # Wait for ALL active
                                     # Broadcast Start
                                     if not getattr(self, '_start_sent', False):
                                          print(f"\n>>> ALL {len(ready_universes)} UNIVERSES READY. STARTING SIMULATION. <<<\n")
                                          for uname, queues in self.universe_queues.items():
                                               queues['incoming'].put({"action": "START_SIMULATION"})
                                          self._start_sent = True

                                # Update UI status only, no stats
                                if run_id not in universe_progress[name]["runs"]:
                                    universe_progress[name]["runs"][run_id] = {}
                                universe_progress[name]["runs"][run_id].update({
                                    "turn": turn,
                                    "status": status,
                                    "stats": {} 
                                })
                                continue

                            # Phase 23: Portal Hand-off Logic (Event)
                            if status == "PORTAL_HANDOFF":
                                package = payload
                                # Validation and Processing
                                src_u = package.get("source_universe") or name
                                dest_u = package.get("portal_destination_universe") # Field name from fleet.py traversal
                                if not dest_u: dest_u = package.get("dest_universe") # Fallback
                                
                                if src_u and dest_u:
                                    self.handle_portal_handoff(package, src_u, dest_u, async_results)
                                else:
                                    logger.error(f"Error: Invalid Portal Handoff Package (Missing src/dest): {package}")
                                continue

                            # Standard Progress Update
                            if run_id not in universe_progress[name]["runs"]:
                                universe_progress[name]["runs"][run_id] = {}
                            
                            
                            current_data = universe_progress[name]["runs"].get(run_id, {})
                            new_stats = payload if payload and isinstance(payload, dict) else current_data.get("stats", {})
                            
                            universe_progress[name]["runs"][run_id] = {
                                "turn": turn,
                                "status": status,
                                "stats": new_stats
                            }

                            # SYNC CHECK
                            if sync_enabled and getattr(self, '_start_sent', False):
                                min_turn = float('inf')
                                all_ready = True
                                
                                for uname in self.progress_queues:
                                    udata = universe_progress.get(uname, {})
                                    uruns = udata.get("runs", {})
                                    if not uruns:
                                        all_ready = False; break
                                    
                                    for rval in uruns.values():
                                        if rval["status"] not in ["Running", "Waiting", "Done"]:
                                             all_ready = False; break
                                        min_turn = min(min_turn, rval["turn"])
                                    if not all_ready: break
                                
                                if all_ready and min_turn >= current_sync_turn:
                                    print(f"  >>> [SYNC] All universes finished Turn {current_sync_turn}. Advancing.")
                                    current_sync_turn += 1
                                    for queues in self.universe_queues.values():
                                        queues['incoming'].put({"action": "NEXT_TURN"})

                            if "Done" in msg[2] or "Error" in msg[2]:
                                # Check if we already counted this run as complete? 
                                # Using sets would be better but simple count is OK for display
                                pass 
                                
                        except queue.Empty:
                            break
                
                # Update Completed Counts
                for name in universe_progress:
                    completed = sum(1 for r in universe_progress[name]["runs"].values() 
                                  if "Done" in r["status"] or "Error" in r["status"])
                    universe_progress[name]["completed"] = completed

                # Draw Dashboard (Throttled)
                current_time = time.time()
                # Initialize last_render_time if not present
                if not hasattr(self, '_last_render_time'):
                    self._last_render_time = 0
                
                if current_time - self._last_render_time > 1.5:  # Render every 1.5 seconds
                    self.dashboard.render(self.output_dir, universe_progress, self.universe_configs)
                    self._last_render_time = current_time
                    
                time.sleep(0.1) # Short sleep to prevent busy loop, but check queues faster
                
            # Final Render to ensure terminal shows the complete state
            self.dashboard.render(self.output_dir, universe_progress, self.universe_configs)
                
            # 5. Collect Results
            for name, res in async_results.items():
                self.results[name] = res.get()
                
            pool.close()
            pool.join()
            
        except KeyboardInterrupt:
            print("\nStopping all simulations...")
            pool.terminate()
            pool.join()
            
        return self.results



    def aggregate_results(self, filename: str = "multi_universe_results.json"):
        """
        Aggregates results from all universes and saves summary and CSVs to output directory.
        """
        if not hasattr(self, 'output_dir'):
            logger.error("Error: simulation has not been run (output_dir undefined).")
            return

        summary_path = os.path.join(self.output_dir, filename)
        
        summary = {
            "timestamp": datetime.datetime.now().isoformat(),
            "universes": {}
        }
        
        for name, run_list in self.results.items():
            if not run_list:
                continue
                
            # Stats
            wins = defaultdict(int)
            turns = []
            durations = []
            
            # Filter None
            valid_runs = [r for r in run_list if r]
            
            for r in valid_runs:
                winner = r.get("Winner", "Draw")
                wins[winner] += 1
                turns.append(r.get("TurnsTaken", 0))
                durations.append(r.get("Duration", 0))
                
            avg_turns = sum(turns) / len(turns) if turns else 0
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            summary["universes"][name] = {
                "total_runs": len(valid_runs),
                "win_rates": dict(wins),
                "avg_turns": round(avg_turns, 2),
                "avg_duration": round(avg_duration, 2)
            }
            
            # Create Universe Subdirectory if it doesn't exist (it should, from batch runs)
            uni_dir = os.path.join(self.output_dir, name)
            os.makedirs(uni_dir, exist_ok=True)
            
            # Write CSV
            csv_path = os.path.join(uni_dir, f"{name}_batch_stats.csv")
            try:
                if valid_runs:
                    # Collect Headers
                    keys = set()
                    for r in valid_runs:
                        keys.update(r.keys())
                    fieldnames = sorted(list(keys))
                    
                    # Prioritize key fields
                    for f in ['Duration', 'TurnsTaken', 'Winner', 'RunID']:
                         if f in fieldnames:
                             fieldnames.remove(f)
                             fieldnames.insert(0, f)
                             
                    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(valid_runs)
            except Exception as e:
                print(f"Failed to write CSV for {name}: {e}")

        # Save Summary
        try:
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"\nAggregated results saved to {summary_path}")
        except Exception as e:
            print(f"Failed to save summary: {e}")

        # Phase 3: Cross-Universe Reporting (Comment 3)
        # Merge individual universe DBs into a shared master DB
        if self.results and hasattr(self, 'output_dir'):
            # Path to master DB
            master_db_path = os.path.join(self.output_dir, "index.db")
            
            try:
                # Initialize Master Schema
                indexer = ReportIndexer(master_db_path)
                
                # Merge logic: Attach and Copy
                # We do this for every universe present in output_dir
                for uni_name in self.results.keys():
                    uni_db_path = os.path.join(self.output_dir, uni_name, "index.db")
                    if os.path.exists(uni_db_path):
                        print(f"Merging DB for {uni_name}...")
                        try:
                            # Attach source DB
                            indexer.conn.execute(f"ATTACH DATABASE ? AS {uni_name}_db", (uni_db_path,))
                            
                            # Copy Runs
                            indexer.conn.execute(f"""
                                INSERT OR IGNORE INTO runs 
                                SELECT * FROM {uni_name}_db.runs
                            """)
                            
                            # Copy Events (Schema match required)
                            indexer.conn.execute(f"""
                                INSERT OR IGNORE INTO events (
                                    batch_id, universe, run_id, turn, timestamp, category, event_type, 
                                    faction, location, entity_type, entity_name, data_json, keywords
                                )
                                SELECT 
                                    batch_id, universe, run_id, turn, timestamp, category, event_type, 
                                    faction, location, entity_type, entity_name, data_json, keywords
                                FROM {uni_name}_db.events
                            """)
                            
                            # Copy Factions
                            indexer.conn.execute(f"""
                                INSERT OR IGNORE INTO factions (
                                    batch_id, universe, run_id, turn, faction, requisition,
                                    planets_controlled, fleets_count, units_recruited, units_lost,
                                    battles_fought, battles_won, damage_dealt, data_json
                                )
                                SELECT 
                                    batch_id, universe, run_id, turn, faction, requisition,
                                    planets_controlled, fleets_count, units_recruited, units_lost,
                                    battles_fought, battles_won, damage_dealt, data_json
                                FROM {uni_name}_db.factions
                            """)
                            
                            # Copy Battles
                            indexer.conn.execute(f"""
                                INSERT OR IGNORE INTO battles (
                                    batch_id, universe, run_id, turn, location, factions_involved,
                                    winner, duration_rounds, total_damage, units_destroyed, data_json
                                )
                                SELECT 
                                    batch_id, universe, run_id, turn, location, factions_involved,
                                    winner, duration_rounds, total_damage, units_destroyed, data_json
                                FROM {uni_name}_db.battles
                            """)
                            
                            indexer.conn.commit()
                            indexer.conn.execute(f"DETACH DATABASE {uni_name}_db")
                            
                        except Exception as e:
                            logger.error(f"Error merging {uni_name}: {e}")
                    else:
                        logger.warning(f"Warning: No DB found for {uni_name} at {uni_db_path}")

                indexer.close()

                # Generate Report
                print("Generating Cross-Universe Comparison Report...")
                # Re-open readable
                indexer = ReportIndexer(master_db_path) 
                reporter = CrossUniverseReporter(indexer)
                # Use the detailed comparison generator, which outputs 'comparison_report.html' and optionally excel
                reporter.generate_detailed_comparison(self.output_dir, formats=["html", "excel"])
                indexer.close()
                print(f"Comparison report generated in {self.output_dir}")

            except Exception as e:
                print(f"Cross-Universe Reporting Failed: {e}")
                traceback.print_exc()

    def _attempt_portal_linking(self):
        """
        Cross-references portal_registry to identify established links (Phase 22).
        """
        universes = list(self.portal_registry.keys())
        if len(universes) < 2:
            return

        established_links = []
        for i, u1_name in enumerate(universes):
            for u2_name in universes[i+1:]:
                u1_portals = self.portal_registry[u1_name]
                u2_portals = self.portal_registry[u2_name]
                
                for p1 in u1_portals:
                    # p1 is a dict from GraphNode.to_dict()
                    meta = p1.get("metadata", {})
                    if meta.get("portal_dest_universe") == u2_name:
                        pid = meta.get("portal_id")
                        # Look for matching portal in U2
                        match = None
                        for p2 in u2_portals:
                            m2 = p2.get("metadata", {})
                            if m2.get("portal_id") == pid and m2.get("portal_dest_universe") == u1_name:
                                match = p2
                                break
                                
                        if match:
                            link_key = tuple(sorted([f"{u1_name}:{pid}", f"{u2_name}:{pid}"]))
                            if link_key not in established_links:
                                established_links.append(link_key)
                                print(f"  > [PORTAL_LINK] Established: {u1_name} <-> {u2_name} via {pid}")
                        else:
                             # Diagnostic for mismatches
                             logger.warning(f"  > [PORTAL_LINK] Warning: Unmatched portal '{pid}' in {u1_name} pointing to {u2_name}. Check {u2_name} config.")

    def handle_portal_handoff(self, package: Dict[str, Any], src_universe: str, dest_universe: str, async_results: Dict) -> bool:
        """
        Orchestrates safe transfer of fleet between universe processes.
        """
        print(f"[PORTAL_HANDOFF] Processing transfer: {package.get('fleet_id')} | {src_universe} -> {dest_universe}")
        
        # 1. Validation
        known_universes = set(c['universe_name'] for c in self.universe_configs)
        if dest_universe not in known_universes and dest_universe not in self.progress_queues:
            logger.error(f"  > Error: Destination universe '{dest_universe}' not found.")
            return False
            
        if dest_universe in async_results and async_results[dest_universe].ready():
            logger.error(f"  > Error: Destination universe '{dest_universe}' has finished execution.")
            return False
            
        # 1.1 Validation (Item 4.2)
        from src.utils.validation_schemas import FleetPackageSchema
        try:
            # We don't have origin_universe in the method args, so we assume it from the package if present
            # or we might need to add it. Let's try to validate what we have.
            FleetPackageSchema(**package)
        except Exception as e:
            logger.error(f"  > [PORTAL] Outgoing Validation Failed: {e}")
            # we might want to fail fast or just warn. Let's fail fast for integrity.
            return False

        # 2. Source De-listing (Request Removal)
        if src_universe in self.universe_queues:
            out_q = self.universe_queues[src_universe]["outgoing"]
            cmd = {"action": "REMOVE_FLEET", "fleet_id": package["fleet_id"]}
            out_q.put(cmd)
            
            # Comment 3: Verify confirmation to avoid duplicate fleets
            # We must wait for "FLEET_REMOVED" confirmation from the source queue.
            # We actively consume the progress_queue for the source universe until we find it,
            # buffering other messages to re-insert them later.
            confirmed = False
            src_prog_q = self.progress_queues.get(src_universe)
            msg_buffer = []

            # Retry Logic Parameters
            max_retries = 3
            timeout_per_try = 2.0
            
            if src_prog_q:
                for attempt in range(max_retries):
                    start_wait = time.time()
                    while time.time() - start_wait < timeout_per_try:
                        try:
                            while not src_prog_q.empty():
                                msg = src_prog_q.get_nowait()
                                # Msg format: (run_id, turn, status, optional_data)
                                if len(msg) >= 3 and msg[2] == "FLEET_REMOVED" and len(msg) > 3 and msg[3] == package["fleet_id"]:
                                    confirmed = True
                                    break
                                else:
                                    msg_buffer.append(msg)
                            
                            if confirmed:
                                break
                            
                            time.sleep(0.1)
                        except queue.Empty:
                            time.sleep(0.1)

                    if confirmed:
                        break
                    
                    print(f"  > [PORTAL_HANDOFF] Retry {attempt+1}/{max_retries} waiting for source confirmation...")
                
                # Re-inject buffered messages (order preserved)
                for buffered_msg in msg_buffer:
                    src_prog_q.put(buffered_msg)
            
            if not confirmed:
                print(f"  > Error: Timed out waiting for FLEET_REMOVED confirmation from {src_universe} after {max_retries} attempts.")
                return False

            print(f"  > [PORTAL_HANDOFF] Source removal confirmed for fleet {package['fleet_id']}.")
            
            # Destination Validation (Re-check)
            if dest_universe not in self.universe_queues or (dest_universe in async_results and async_results[dest_universe].ready()):
                 print(f"  > Error: Destination {dest_universe} became unavailable during handoff.")
                 # RECOVERY: Refund to Source
                 if src_universe in self.universe_queues:
                     print(f"  > [RECOVERY] Refunding fleet {package['fleet_id']} to {src_universe} incoming queue.")
                     refund_q = self.universe_queues[src_universe]["incoming"]
                     # We can re-use INJECT action.
                     # The package source is already set. We might want to set a flag 'is_refund'.
                     package["is_refund"] = True
                     refund_cmd = {
                        "action": "INJECT_FLEET",
                        "package": package,
                        "timestamp": time.time()
                     }
                     refund_q.put(refund_cmd)
                     return False
                 else:
                     print(f"  > CRITICAL ERROR: Could not refund fleet {package['fleet_id']} - Source queue lost.")
                     return False
            
        # 3. DNA Translation
        try:
             from src.core.universe_data import UniverseDataManager
             # Comment 3: Translate each unit
             # We need an instance. The Runner process generally doesn't have an 'active' universe set for data.
             # But we can instantiate the singleton. 
             # We might need to load data? load_universe_data might be needed.
             udm = UniverseDataManager.get_instance()
             
             # We need translation tables from SRC to DEST.
             # UDM loads data for ACTIVE universe.
             # We should probably load SRC universe config to get the table?
             # Or load DEST universe config?
             # rehydrate_for_universe usually assumes we are in the context of the target or have the table.
             # The table is in 'universe_config'.
             # Let's load the DEST object temporarily.
             udm.load_universe_data(dest_universe)
             
             translated_units = []
             raw_units = package.get("units", [])
             
             for u_dna in raw_units:
                 # Translate
                 new_dna = udm.rehydrate_for_universe(u_dna, dest_universe)
                 translated_units.append(new_dna)
                 
             # Update Package
             package["units"] = translated_units
             package["is_translated"] = True
             
        except Exception as e:
             print(f"  > Warning during translation: {e}")
             traceback.print_exc()

        # 4. Destination Injection
        if dest_universe in self.universe_queues:
            in_q = self.universe_queues[dest_universe]["incoming"]
            
            # We add an action wrapper
            injection_cmd = {
                "action": "INJECT_FLEET",
                "package": package,
                "timestamp": time.time()
            }
            in_q.put(injection_cmd)
            print(f"  > [PORTAL_HANDOFF] Fleet injected into {dest_universe} queue.")
            return True
            
        print(f"  > Error: No queue found for {dest_universe}")
        return False

if __name__ == "__main__":
    # Example Usage
    print("MultiUniverseRunner Usage Example:")
    print("This module is designed to be imported and used programmatically.")
    print("Example:")
    print("""
    from src.engine.multi_universe_runner import MultiUniverseRunner

    configs = [
        {
            "universe_name": "void_reckoning",
            "processor_affinity": [0, 1, 2, 3],
            "num_runs": 10,  # Reduced for example
            "game_config": {"campaign": {"turns": 100, "num_systems": 10}, "simulation": {"num_runs": 10}}
        }
        # Add other universes here
    ]

    runner = MultiUniverseRunner(configs)
    results = runner.run_parallel()
    runner.aggregate_results()
    """)


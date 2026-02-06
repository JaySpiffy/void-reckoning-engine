import os
import sys
import time
import json
import csv
import queue
import logging
import traceback
import datetime
from multiprocessing import Queue, Manager
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Core Imports
from src.core.config import UNIVERSE_ROOT, REPORTS_DIR
from src.core.constants import FACTION_ABBREVIATIONS
from universes.base.universe_loader import UniverseLoader

# Runner Imports
from src.engine.runner.lifecycle import NoDaemonPool, run_universe_batch
from src.engine.runner.portal_manager import PortalManager
from src.reporting.terminal import TerminalDashboard
from src.utils.keyboard import get_key
from src.reporting.indexing import ReportIndexer
from src.reporting.cross_universe_reporter import CrossUniverseReporter

logger = logging.getLogger(__name__)

class MultiUniverseRunner:
    """
    Orchestrates parallel execution of different universes on designated CPU cores.
    Each universe runs in its own process, which in turn manages a pool of simulation workers.
    """
    
    def __init__(self, universe_configs: List[Dict[str, Any]], multi_settings: Dict[str, Any] = None):
        """
        Initialize the runner with a list of universe configurations.
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
        
        # Managers
        self.portal_manager = PortalManager(self)

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

        # 1.5 Pre-flight Registry Building
        print("Pre-flight: Building registries for all universes...")
        for config in self.universe_configs:
            u_name = config["universe_name"]
            try:
                from src.utils.registry_builder import build_all_registries
                build_all_registries(universe_name=u_name, verbose=False)
            except Exception as e:
                logger.warning(f"Warning: Failed to build registries for {u_name}: {e}")

        # 2. Setup Process Pool (One per Universe)
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
                run_universe_batch,
                args=(
                    name,
                    config["game_config"],
                    config["num_runs"],
                    self.output_dir,
                    self.progress_queues[name],
                    config.get("processor_affinity"),
                    self.universe_queues[name]["incoming"],
                    self.universe_queues[name]["outgoing"]
                )
            )
            async_results[name] = res
            
        print(f"Started parallel execution for {len(self.universe_configs)} universes.")
        
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
                            msg = q.get_nowait()
                            run_id = msg[0]
                            turn = msg[1]
                            status = msg[2]
                            payload = msg[3] if len(msg) > 3 else {}
                            
                            print(f"DEBUG: [ORCHESTRATOR] Received msg from {name}: {status}")
                            
                            # Phase 22: Portal Sync
                            if status == "GALAXY_READY":
                                portals = payload if isinstance(payload, list) else []
                                self.portal_registry[name] = portals
                                print(f"  > [PORTAL_SYNC] Universe '{name}' registered {len(portals)} portals.")
                                self.portal_manager.attempt_portal_linking()
                                
                                # Track Readiness
                                ready_universes.add(name)
                                if len(ready_universes) >= len(self.progress_queues):
                                     if not getattr(self, '_start_sent', False):
                                          print(f"\n>>> ALL {len(ready_universes)} UNIVERSES READY. STARTING SIMULATION. <<<\n")
                                          for uname, queues in self.universe_queues.items():
                                               queues['incoming'].put({"action": "START_SIMULATION"})
                                          self._start_sent = True

                                if run_id not in universe_progress[name]["runs"]:
                                    universe_progress[name]["runs"][run_id] = {}
                                universe_progress[name]["runs"][run_id].update({
                                    "turn": turn,
                                    "status": status,
                                    "stats": {} 
                                })
                                continue

                            # Phase 23: Portal Hand-off Logic
                            if status == "PORTAL_HANDOFF":
                                package = payload
                                src_u = package.get("source_universe") or name
                                dest_u = package.get("portal_destination_universe") or package.get("dest_universe")
                                
                                if src_u and dest_u:
                                    self.portal_manager.handle_portal_handoff(package, src_u, dest_u, async_results)
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
                                pass 
                                
                        except queue.Empty:
                            break
                
                # Update Completed Counts
                for name in universe_progress:
                    completed = sum(1 for r in universe_progress[name]["runs"].values() 
                                   if "Done" in r["status"] or "Error" in r["status"])
                    universe_progress[name]["completed"] = completed

                # Poll Keyboard Input
                key = get_key()
                if key:
                    self.dashboard.handle_input(key)
                
                # Check for Quit Signal
                if self.dashboard.quit_requested:
                    print("\nQuit requested via keyboard. Stopping simulations...")
                    pool.terminate()
                    break

                # Draw Dashboard (Throttled)
                current_time = time.time()
                if not hasattr(self, '_last_render_time'):
                    self._last_render_time = 0
                
                if current_time - self._last_render_time > 1.5:
                    self.dashboard.render(self.output_dir, universe_progress, self.universe_configs)
                    self._last_render_time = current_time
                    
                time.sleep(0.01)

            # Final Render
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

    def handle_portal_handoff(self, package: Dict[str, Any], src_universe: str, dest_universe: str, async_results: Dict) -> bool:
        """Proxy to portal_manager."""
        return self.portal_manager.handle_portal_handoff(package, src_universe, dest_universe, async_results)

    def _attempt_portal_linking(self):
        """Proxy to portal_manager."""
        return self.portal_manager.attempt_portal_linking()

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
                
            wins = defaultdict(int)
            turns = []
            durations = []
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
            
            uni_dir = os.path.join(self.output_dir, name)
            os.makedirs(uni_dir, exist_ok=True)
            
            csv_path = os.path.join(uni_dir, f"{name}_batch_stats.csv")
            try:
                if valid_runs:
                    keys = set()
                    for r in valid_runs:
                        keys.update(r.keys())
                    fieldnames = sorted(list(keys))
                    
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

        try:
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2)
            print(f"\nAggregated results saved to {summary_path}")
        except Exception as e:
            print(f"Failed to save summary: {e}")

        if self.results and hasattr(self, 'output_dir'):
            master_db_path = os.path.join(self.output_dir, "index.db")
            
            try:
                indexer = ReportIndexer(master_db_path)
                for uni_name in self.results.keys():
                    uni_db_path = os.path.join(self.output_dir, uni_name, "index.db")
                    if os.path.exists(uni_db_path):
                        print(f"Merging DB for {uni_name}...")
                        try:
                            indexer.conn.execute(f"ATTACH DATABASE ? AS {uni_name}_db", (uni_db_path,))
                            indexer.conn.execute(f"INSERT OR IGNORE INTO runs SELECT * FROM {uni_name}_db.runs")
                            indexer.conn.execute(f"""
                                INSERT OR IGNORE INTO events (
                                    batch_id, universe, run_id, turn, timestamp, category, event_type, 
                                    faction, location, entity_type, entity_name, data_json, keywords
                                )
                                SELECT batch_id, universe, run_id, turn, timestamp, category, event_type, 
                                       faction, location, entity_type, entity_name, data_json, keywords
                                FROM {uni_name}_db.events
                            """)
                            indexer.conn.execute(f"""
                                INSERT OR IGNORE INTO factions (
                                    batch_id, universe, run_id, turn, faction, requisition,
                                    planets_controlled, fleets_count, units_recruited, units_lost,
                                    battles_fought, battles_won, damage_dealt, data_json
                                )
                                SELECT batch_id, universe, run_id, turn, faction, requisition,
                                       planets_controlled, fleets_count, units_recruited, units_lost,
                                       battles_fought, battles_won, damage_dealt, data_json
                                FROM {uni_name}_db.factions
                            """)
                            indexer.conn.execute(f"""
                                INSERT OR IGNORE INTO battles (
                                    batch_id, universe, run_id, turn, location, factions_involved,
                                    winner, duration_rounds, total_damage, units_destroyed, data_json
                                )
                                SELECT batch_id, universe, run_id, turn, location, factions_involved,
                                       winner, duration_rounds, total_damage, units_destroyed, data_json
                                FROM {uni_name}_db.battles
                            """)
                            indexer.conn.commit()
                            indexer.conn.execute(f"DETACH DATABASE {uni_name}_db")
                        except Exception as e:
                            logger.error(f"Error merging {uni_name}: {e}")
                indexer.close()

                indexer = ReportIndexer(master_db_path) 
                reporter = CrossUniverseReporter(indexer)
                reporter.generate_detailed_comparison(self.output_dir, formats=["html", "excel"])
                indexer.close()
                print(f"Comparison report generated in {self.output_dir}")

            except Exception as e:
                print(f"Cross-Universe Reporting Failed: {e}")
                traceback.print_exc()

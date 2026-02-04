# src/engine/runner/simulation_worker.py
import sys
import os
import random
import time
import traceback
import gc
import queue  # Ensure queue is imported
from collections import defaultdict

from src.managers.campaign_manager import CampaignEngine
from src.reporting.organizer import ReportOrganizer
from src.reporting.indexer import ReportIndexer

# Global progress queue reference for worker processes
progress_queue = None

def worker_init(q):
    """Initialize global queue for worker processes"""
    global progress_queue
    progress_queue = q

def run_single_campaign_wrapped(args):
    """
    Unpack args and call logic.
    """
    return SimulationWorker.run_single_campaign_logic(*args)

class SimulationWorker:
    """
    Encapsulates logic for running a single simulation instance.
    """
    
    @staticmethod
    def run_single_campaign_logic(run_id, turns_per_run, num_systems, batch_dir, min_p, max_p, combat_rounds, max_fleet, max_land, base_req, game_config):
        
        # Apply Seed if Configured
        seed = game_config.get("seed")
        if seed is not None:
             # Unique seed per run to ensure variation but determinism
             run_seed = seed + run_id
             random.seed(run_seed)
             print(f"DEBUG: Initialized with base seed {seed}, run seed {run_seed}")

        # Setup Report Organizer
        batch_id = os.path.basename(batch_dir)
        run_name = f"run_{run_id:03d}"
        universe_name = game_config.get("universe", "void_reckoning")
        
        organizer = ReportOrganizer(os.path.dirname(batch_dir), batch_id, run_name, universe_name=universe_name)
        organizer.initialize_run(metadata=game_config)

        run_dir = organizer.run_path
        battles_dir = os.path.join(run_dir, "battles")
        economy_dir = os.path.join(run_dir, "economy")
        db_path = os.path.join(os.path.dirname(batch_dir), "index.db")
        indexer = ReportIndexer(db_path)

        # Redirect stdout
        log_file_path = os.path.join(run_dir, "full_campaign_log.txt")
        original_stdout = sys.stdout
        sys.stdout = open(log_file_path, "w", encoding="utf-8")
        
        global progress_queue
        start_time = time.time()

        try:
            # Initial Report
            if progress_queue:
                 progress_queue.put((run_id, 0, "Init"))

            # Initialize Engine
            engine = CampaignEngine(battle_log_dir=battles_dir, game_config=game_config, report_organizer=organizer, universe_name=universe_name)
            engine.max_combat_rounds = combat_rounds 
            engine.max_fleet_size = max_fleet
            engine.max_land_units = max_land
            engine.max_fleet_size = max_fleet
            engine.max_land_units = max_land
            engine.generate_galaxy(num_systems=num_systems, min_planets=min_p, max_planets=max_p, base_req=base_req)
            
            # Dashboard Wrapper
            try:
                from src.reporting.live_dashboard import state
                if hasattr(state, 'active') and state.active:
                    engine.attach_dashboard()
            except (ImportError, AttributeError):
                pass
            
            # Register Portals
            if progress_queue:
                portals_serialized = [p.to_dict() for p in engine.galaxy_generator.portals] if hasattr(engine.galaxy_generator, 'portals') else []
                if not portals_serialized and hasattr(engine, 'generator') and hasattr(engine.generator, 'portals'):
                    portals_serialized = [p.to_dict() for p in engine.generator.portals]
                progress_queue.put((run_id, 0, "GALAXY_READY", portals_serialized))

                if game_config.get("multi_universe_settings", {}).get("sync_turns"):
                    import src.engine.multi_universe_runner as mur
                    in_q = getattr(mur, '_incoming_fleet_q', None)
                    if in_q:
                        while True:
                            try:
                                cmd = in_q.get(timeout=0.5)
                                if isinstance(cmd, dict) and cmd.get("action") == "START_SIMULATION":
                                    break
                            except queue.Empty: # Use queue.Empty
                                pass
                            time.sleep(0.5)
            
            # Use local import for multi-universe to avoid circular imports?
            # Or assume run_single_campaign_wrapped is running in a worker process where this is safe.
            import src.engine.multi_universe_runner as mur
            in_q = getattr(mur, '_incoming_fleet_q', None)
            out_q = getattr(mur, '_outgoing_fleet_q', None)
            
            if progress_queue:
                 engine.set_fleet_queues(in_q, out_q, progress_queue)
            else:
                 engine.set_fleet_queues(in_q, out_q, None)

            engine.spawn_start_fleets()
            
            winner = "Draw"
            turns_taken = turns_per_run
            stats = {}
            
            for t in range(turns_per_run):
                current_turn = t
                engine.process_turn(fast_resolve=False)
                sys.stdout.flush()
                engine.process_fleet_queues(run_id, t)

                # Heartbeat Indexing
                if t > 0 and t % 10 == 0:
                    try:
                        indexer.index_run(run_dir, universe=universe_name)
                    except Exception as e:
                        print(f"Warning: Heartbeat indexing failed: {e}")

                # Finalize Manifests
                turn_id = f"turn_{t:03d}"
                turn_path = os.path.join(run_dir, "turns", turn_id)
                if os.path.exists(turn_path):
                     organizer.finalize_manifest(os.path.join(turn_path, "manifest.json"))
                
                # Update Global Category Manifests occasionally
                if t % 10 == 0:
                    for cat in organizer.categories:
                        cat_path = os.path.join(run_dir, cat)
                        if os.path.exists(cat_path):
                            organizer.finalize_manifest(os.path.join(cat_path, "manifest.json"))

                # Validate
                is_valid, report_errors = organizer.validate_turn_reports(t)
                if not is_valid:
                    print(f"WARNING: Turn {t} reporting integrity check failed!")
                    for err in report_errors:
                        print(f"  - {err}")

                # 1-turn Heartbeat for dashboard
                if t % 1 == 0: 
                     stats = SimulationWorker._collect_stats(engine)
                     if progress_queue:
                         progress_queue.put((run_id, t, "Running", stats))

                     # SYNC BARRIER
                     if game_config.get("multi_universe_settings", {}).get("sync_turns"):
                         sync_q = getattr(mur, '_incoming_fleet_q', None)
                         if sync_q:
                             if progress_queue:
                                  progress_queue.put((run_id, t, "Waiting", {}))
                             next_turn_ready = False
                             while not next_turn_ready:
                                 try:
                                     # Simplified Drain Logic
                                     msgs = []
                                     while not sync_q.empty():
                                         cmd = sync_q.get_nowait()
                                         if isinstance(cmd, dict) and cmd.get("action") == "NEXT_TURN":
                                             next_turn_ready = True
                                             break
                                         else:
                                             msgs.append(cmd)
                                     for m in msgs: sync_q.put(m)
                                     if not next_turn_ready: time.sleep(0.1)
                                 except queue.Empty:
                                     time.sleep(0.1)

                # MEMORY: Periodic GC
                gc_interval = game_config.get("technical", {}).get("gc_interval", 100)
                if t > 0 and t % gc_interval == 0:
                    gc.collect()

                # EARLY EXIT
                owners = set([p.owner for p in engine.all_planets if p.owner != "Neutral"])
                if len(owners) == 1:
                    winner = list(owners)[0]
                    turns_taken = t + 1
                    break
            
            # Finalize report folder
            if hasattr(engine, 'report_organizer') and engine.report_organizer:
                engine.report_organizer.finalize_run(summary={"winner": winner, "turns_taken": turns_taken})
                
            # Auto-indexing
            if game_config.get("reporting", {}).get("auto_index", True):
                try:
                    indexer.index_run(run_dir, universe=universe_name)
                    indexer.close()
                except Exception as e:
                    original_stdout.write(f"Warning: Auto-indexing failed for run {run_id}: {e}\n")

            if hasattr(engine, 'telemetry'):
                engine.telemetry.flush()
            
            duration = time.time() - start_time
            
            if progress_queue:
                progress_queue.put((run_id, turns_taken, f"Done ({winner})", stats))
            
            # Final aggregation relative to worker run
            run_data = SimulationWorker._build_run_data(run_id, winner, turns_taken, duration, engine)
            
            # EXPORT ANALYTICS
            engine.export_analytics(economy_dir, run_id)
            return run_data

        except Exception as e:
            # Capture Traceback
            tb_str = traceback.format_exc()
            with open(os.path.join(run_dir, "error_log.txt"), "w") as f:
                f.write(tb_str)
                f.write("\n")
                f.write(str(e))
                
            try:
                 if 'engine' in locals():
                      if not os.path.exists(economy_dir): os.makedirs(economy_dir)
                      engine.export_analytics(economy_dir, run_id)
                      if hasattr(engine, 'telemetry'):
                          engine.telemetry.flush()
            except: pass

            if progress_queue:
                # Pass the traceback in the stats payload so Dashboard can render it
                # Use current_turn to report where it actually died
                progress_queue.put((run_id, locals().get('current_turn', 0), "Error", {"error_trace": tb_str}))
            return None
        finally:
            sys.stdout = original_stdout

    @staticmethod
    def _collect_stats(engine):
        stats = {}
        try:
             owners = defaultdict(list)
             fleets = defaultdict(int)
             armies = defaultdict(int)
             buildings = defaultdict(int)
             starbases = defaultdict(int)
             systems_owned = defaultdict(set)
             total_ships = defaultdict(int)
             total_ground = defaultdict(int)
             
             cities = defaultdict(int)
             owners_full = defaultdict(int)
             owners_contested = defaultdict(int)
             own_cities_total = defaultdict(int)
             con_cities_total = defaultdict(int)
             
             for p in engine.all_planets:
                 factions_on_planet = set()
                 cities_on_this_planet = defaultdict(int)

                 if p.owner != "Neutral":
                     factions_on_planet.add(p.owner)
                     buildings[p.owner] += len(p.buildings)
                 
                 if hasattr(p, 'provinces'):
                     for n in p.provinces:
                         if n.owner != "Neutral":
                             factions_on_planet.add(n.owner)
                             buildings[n.owner] += len(n.buildings)
                             if getattr(n, 'terrain_type', None) == "City":
                                 cities[n.owner] += 1
                                 cities_on_this_planet[n.owner] += 1
                         
                         for ag in n.armies:
                             if not ag.is_destroyed:
                                 factions_on_planet.add(ag.faction)
                 
                 if hasattr(p, 'armies'):
                     for ag in p.armies:
                         if not ag.is_destroyed:
                             factions_on_planet.add(ag.faction)
                             
                 # Categorize Planet Ownership and accumulate stats
                 if len(factions_on_planet) == 1:
                     sole_owner = list(factions_on_planet)[0]
                     owners_full[sole_owner] += 1
                     own_cities_total[sole_owner] += cities_on_this_planet[sole_owner]
                 elif len(factions_on_planet) > 1:
                     for f in factions_on_planet:
                         owners_contested[f] += 1
                         con_cities_total[f] += cities_on_this_planet[f]

                 if p.owner != "Neutral":
                     if hasattr(p, 'system') and p.system:
                         systems_owned[p.owner].add(p.system)

                 # Army/Fleet counting...
                 p_armies = []
                 if hasattr(p, 'armies'): p_armies.extend(p.armies)
                 if hasattr(p, 'provinces'):
                     for n in p.provinces:
                         if hasattr(n, 'armies'): p_armies.extend(n.armies)
                 for ag in p_armies:
                     if not ag.is_destroyed: 
                         armies[ag.faction] += 1
                         total_ground[ag.faction] += len(ag.units)
                     
             if hasattr(engine, 'systems'):
                 for s in engine.systems:
                     if hasattr(s, 'starbases'):
                         for sb in s.starbases:
                             if sb.is_alive(): starbases[sb.faction] += 1
                             
             for fl in engine.fleets:
                 if not fl.is_destroyed: 
                     fleets[fl.faction] += 1
                     total_ships[fl.faction] += len(fl.units)
                     # Count embarked armies
                     if hasattr(fl, 'cargo_armies'):
                         for ag in fl.cargo_armies:
                             if not ag.is_destroyed:
                                 armies[ag.faction] += 1
                                 total_ground[ag.faction] += len(ag.units)
                 
             for f in engine.factions:
                 if f == "Neutral": continue
                 f_count = fleets[f]
                 b_count = buildings[f]
                 a_count = armies[f]
                 sb_count = starbases[f]
                 cty_count = cities[f]
                 own_count = owners_full[f]
                 con_count = owners_contested[f]
                 
                 req = 0
                 tech_count = 0
                 if f in engine.factions:
                     req = int(engine.factions[f].requisition)
                     tech_count = len(engine.factions[f].unlocked_techs)
                 
                 s_count = len(systems_owned.get(f, set()))
                 
                 f_obj = engine.factions[f]
                 stats[f] = {
                     "OWN": own_count, "CON": con_count, "F": f_count, "B": b_count, "A": a_count, "SB": sb_count,
                     "R": req, "S": s_count, "T": tech_count, "CTY": cty_count,
                     "OWN_CTY": own_cities_total[f], "CON_CTY": con_cities_total[f],
                     "AvgS": total_ships[f] / f_count if f_count > 0 else 0,
                     "AvgG": total_ground[f] / a_count if a_count > 0 else 0,
                     "AvgG": total_ground[f] / a_count if a_count > 0 else 0,
                     "L": f_obj.stats.get("turn_units_lost", 0),
                     "L_Ship": f_obj.stats.get("turn_ships_lost", 0),
                     "L_Ground": f_obj.stats.get("turn_ground_lost", 0),
                     "BW": f_obj.stats.get("battles_won", 0),
                     "BF": f_obj.stats.get("battles_fought", 0),
                     "BD": f_obj.stats.get("battles_drawn", 0),
                     "Post": getattr(f_obj, "strategic_posture", "BALANCED")
                 }
                 
                 init_req = getattr(f_obj, 'initial_requisition', 0)
                 req_score = 0
                 if init_req < 1e12: # Cap for infinite-resource factions
                     req_score = int((req - init_req) / 1000)
                 
                 stats[f]["Score"] = ((own_count + con_count) * 100) + (s_count * 500) + (b_count * 50) + (f_count * 20) + (a_count * 10) + (sb_count * 300) + (tech_count * 1000) + req_score
                 
                 # Phase 5: Inject Theater Info for Dashboard
                 # Path: engine -> strategic_ai -> planner -> theater_manager
                 if hasattr(engine, 'strategic_ai') and hasattr(engine.strategic_ai.planner, 'theater_manager'):
                     tm = engine.strategic_ai.planner.theater_manager
                     # Filter theaters for this faction
                     my_theaters = [t for t in tm.theaters.values() if t.id.startswith(f"THEATER-{f}")]
                     if my_theaters:
                         t_data = []
                         for t in my_theaters:
                             t_data.append({
                                 "name": t.name,
                                 "goal": t.assigned_goal
                             })
                         stats[f]["Theaters"] = t_data

             # Global Stats
             stats['GLOBAL_PLANETS'] = len(engine.all_planets)
             stats['GLOBAL_NEUTRAL'] = sum(1 for p in engine.all_planets if p.owner == "Neutral")
             stats['GLOBAL_STORMS'] = sum(1 for edge in engine.storm_manager.edges if edge.blocked) if hasattr(engine, 'storm_manager') else 0
             
             # Calculate Battles: Active (Pending) + Resolved This Turn
             active_battles = len(engine.battle_manager.active_battles) if hasattr(engine, 'battle_manager') else 0
             resolved_battles = engine.battle_manager.battles_resolved_this_turn if hasattr(engine, 'battle_manager') and hasattr(engine.battle_manager, 'battles_resolved_this_turn') else 0
             stats['GLOBAL_BATTLES'] = active_battles + resolved_battles
             
             # Split Battles (Space / Ground)
             # Active Split
             active_space = 0
             active_ground = 0
             if hasattr(engine, 'battle_manager'):
                 for b in engine.battle_manager.active_battles.values():
                     if getattr(b, 'participating_fleets', None):
                         active_space += 1
                     else:
                         active_ground += 1
             
             resolved_space = engine.battle_manager.battles_resolved_this_turn_space if hasattr(engine, 'battle_manager') and hasattr(engine.battle_manager, 'battles_resolved_this_turn_space') else 0
             resolved_ground = engine.battle_manager.battles_resolved_this_turn_ground if hasattr(engine, 'battle_manager') and hasattr(engine.battle_manager, 'battles_resolved_this_turn_ground') else 0
             
             stats['GLOBAL_SPACE_BATTLES'] = active_space + resolved_space
             stats['GLOBAL_GROUND_BATTLES'] = active_ground + resolved_ground
             
             # Phase 5.5: Inject Diplomacy (Alliances/Trade)
             # Path: engine -> diplomacy -> treaty_coordinator -> treaties
             diplomacy_active = []
             if hasattr(engine, 'diplomacy') and engine.diplomacy:
                 treaties = engine.diplomacy.treaty_coordinator.treaties
                 processed_pairs = set()
                 
                 for f1, targets in treaties.items():
                     for f2, state in targets.items():
                         if state in ["Alliance", "Trade", "War", "Vassal"]:
                             # Avoid duplicates (A-B and B-A)
                             pair = tuple(sorted([f1, f2]))
                             if pair in processed_pairs: continue
                             processed_pairs.add(pair)
                             
                             diplomacy_active.append({
                                 "members": pair,
                                 "type": state
                             })
             stats['GLOBAL_DIPLOMACY'] = diplomacy_active

        except Exception as e: 
            print(f"STATS ERROR: {e}")
            traceback.print_exc()
        return stats

    @staticmethod
    def _build_run_data(run_id, winner, turns_taken, duration, engine):
        planet_counts = defaultdict(int)
        for p in engine.all_planets:
            if p.owner != "Neutral":
                planet_counts[p.owner] += 1
        
        run_data = {
            'RunID': run_id, 
            'Winner': winner, 
            'TurnsTaken': turns_taken,
            'Duration': round(duration, 2)
        }
        for f in engine.factions:
             if f == "Neutral": continue
             run_data[f"{f}_Planets"] = planet_counts.get(f, 0)
        return run_data

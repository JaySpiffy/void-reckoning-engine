
import sys
import time
from src.managers.campaign_manager import CampaignEngine

from src.core.config import REPORTS_DIR, set_active_universe, ACTIVE_UNIVERSE
from src.core.game_config import GameConfig
from src.reporting.organizer import ReportOrganizer
from src.managers.galaxy_generator import init_galaxy_rng # Ensure we can seed mapizer
import json
import os

def run_campaign_simulation(turns=50, planets=40, game_config=None, universe_name=None, run_id=None, telemetry_collector=None, delay_seconds=0.0, manual_mode=False):
    print(f"=== CAMPAIGN SIMULATION: {turns} TURNS ===")
    
    # Step 9: Propagate Universe Parameter
    universe = universe_name or ACTIVE_UNIVERSE or "void_reckoning"
    set_active_universe(universe)
    
    # Initialize GameConfig
    if isinstance(game_config, GameConfig):
        config = game_config
    else:
        # Create from dict or defaults
        config_data = game_config or {}
        
        # Phase 3 Determinism: Load defaults from simulation_config.json if not provided
        if not config_data:
            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "simulation_config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        print(f"DEBUG: Loaded defaults from {config_path}")
                except Exception as e:
                    print(f"Warning: Could not load simulation_config.json: {e}")

        # Apply CLI overrides if not present in config
        if "campaign" not in config_data: config_data["campaign"] = {}
        if "turns" not in config_data["campaign"]: config_data["campaign"]["turns"] = turns
        if "num_systems" not in config_data["campaign"]: config_data["campaign"]["num_systems"] = planets
        
        config = GameConfig.from_dict(config_data)
        
        # Handle case where config is actually MultiUniverseConfig
        from src.core.game_config import MultiUniverseConfig
        if isinstance(config, MultiUniverseConfig):
            print(f"DEBUG: Detected MultiUniverseConfig, extracting config for {universe}")
            found = False
            for u_conf in config.universes:
                if u_conf.name == universe:
                    # found matching universe config
                    config = GameConfig.from_dict(u_conf.game_config)
                    found = True
                    break
            
            if not found:
                 print(f"Warning: Universe {universe} not found in config. Using defaults.")
                 # Fallback to default by creating empty GameConfig + raw
                 config = GameConfig.from_dict(config_data.get("defaults", {})) # or just new

    # Initialize Report Organizer
    timestamp = int(time.time())
    
    # Ensure map is unique for this run
    init_galaxy_rng(timestamp)
    
    batch_id = f"batch_{time.strftime('%Y%m%d_%H%M%S')}"
    if not run_id:
        run_id = f"run_{timestamp}"
    
    organizer = ReportOrganizer(REPORTS_DIR, batch_id, run_id, universe_name=universe)
    organizer.initialize_run({"turns": config.max_turns, "planets": config.num_systems, "type": "quick_campaign", "config": config.raw_config})
    
    print(f"Reports initialized at: {organizer.run_path}")
    
    # FIX: Explicitly initialize TelemetryCollector to ensure JSON logs are generated
    # This is required for the Dashboard to consume data.
    from src.reporting.telemetry import TelemetryCollector
    if not telemetry_collector:
        print(f"[SIM] Initializing TelemetryCollector at {organizer.run_path}")
        telemetry_collector = TelemetryCollector(
            log_dir=organizer.run_path, 
            verbosity="summary", 
            universe_name=universe
        )
    
    engine = CampaignEngine(
        report_organizer=organizer, 
        game_config=config, 
        universe_name=universe,
        telemetry_collector=telemetry_collector
    )
    
    # FIX: Initialize Run-Scoped ReportIndexer for Live DB Flushing
    # This places campaign_data.db INSIDE the run folder
    from src.reporting.indexing import ReportIndexer
    if hasattr(organizer, 'run_path'):
        db_path = os.path.join(organizer.run_path, "campaign_data.db")
        print(f"[SIM] Initializing Run-Scoped DB: {db_path}")
        engine.indexer = ReportIndexer(db_path=db_path)
        if telemetry_collector:
            telemetry_collector.set_indexer(engine.indexer)
            telemetry_collector.set_batch_id(batch_id)
            telemetry_collector.set_run_id(run_id)
    else:
        engine.indexer = None
    # engine.generate_galaxy(num_systems, min_p, max_p)
    # Mapping "planets" arg to num_systems for now
    engine.generate_galaxy(num_systems=config.num_systems, min_planets=config.min_planets_per_system, max_planets=config.max_planets_per_system)
    
    # [NATIVE PULSE] Sync Topology to Rust
    if hasattr(engine, 'pathfinder') and hasattr(engine.pathfinder, 'sync_topology'):
        print("[NATIVE PULSE] Syncing galaxy topology to Rust Pathfinder...")
        engine.pathfinder.sync_topology(engine.systems)
        
    engine.spawn_start_fleets(num_fleets_per_faction=config.starting_fleets)
    
    # [NATIVE PULSE] Initialize Rust Auditor
    try:
        from src.utils.rust_auditor import RustAuditorWrapper
        print("[NATIVE PULSE] Initializing Global Auditor...")
        auditor = RustAuditorWrapper()
        
        # Load Registries from GameConfig
        # Assuming config.raw_config contains these keys or accessed via properties
        # We use raw_config to get the dict structure
        if auditor.load_registry("technology", config.raw_config.get("technology", {})):
            print("  - Technology registry loaded")
        if auditor.load_registry("buildings", config.raw_config.get("buildings", {})):
            print("  - Buildings registry loaded")
            
        if auditor.initialize():
            print("[NATIVE PULSE] Global Auditor Active")
            engine.auditor = auditor # Attach to engine for potential use
        else:
             print("[NATIVE PULSE] Global Auditor Failed to Initialize")
             
    except Exception as e:
        print(f"[NATIVE PULSE] Auditor Integration Failed: {e}")

    # Validation
    engine.validate_asset_cache()
    
    # Phase 2: Live Dashboard Attachment
    try:
        from src.reporting.live_dashboard import state
        if hasattr(state, 'active') and state.active:
            print("[SIM] Attempting to attach to Live Dashboard...")
            if engine.attach_dashboard():
                print("[SIM] Successfully attached to dashboard.")
    except Exception as e:
        print(f"[SIM] Dashboard attachment skipped: {e}")
    
    conquest_log = []
    
    print("\nStarting Simulation...\n")
    try:
        for i in range(turns):
            # Check for Dashboard Pause
            try:
                if hasattr(state, 'initialized') and state.initialized:
                    # Initial Pause for Manual Mode
                    if i == 0 and manual_mode:
                        print("[SIM] Manual mode enabled. Pausing at start.")
                        state.pause_simulation()
                    
                    # Wait for Permission (Play/Step)
                    state.wait_for_turn_authorization()
                    
                    while state.paused:
                        time.sleep(0.5)
            except Exception as e:
                # print(f"Pause check failed: {e}")
                pass

            print(f"--- Processing Turn {i+1} ---")
            engine.process_turn()
            
            # Phase 11: Check for Victory Termination
            winner = engine.check_victory_conditions()
            if winner:
                print(f"\n[VICTORY] {winner} has achieved victory! Terminating simulation at Turn {i+1}.")
                break
            
            # --- DASHBOARD UPDATE ---
            # Calculate basics for dashboard
            stats = {}
            p_counts = {}
            for p in engine.get_all_planets():
                if p.owner not in p_counts: p_counts[p.owner] = 0
                p_counts[p.owner] += 1
            
            # Requisitions
            reqs = {f.name: f.requisition for f in engine.get_all_factions()}
            
            # Compose status
            stats = {f.name: {"P": p_counts.get(f.name, 0), "R": reqs.get(f.name, 0)} for f in engine.get_all_factions()}
            
                # Detailed Planet Data for Table
            planet_data = []
            for p in engine.get_all_planets():
                # Map is_sieged to status string
                status = "Siege" if getattr(p, 'is_sieged', False) else "Stable"
                # Get system name
                sys_name = p.system.name if hasattr(p, 'system') and p.system else "Unknown"
                
                planet_data.append({
                    "name": p.name,
                    "system": sys_name, 
                    "owner": p.owner,
                    "status": status,
                    "is_sieged": getattr(p, 'is_sieged', False)
                })

            if hasattr(engine, 'telemetry') and engine.telemetry:
                 from src.reporting.telemetry import EventCategory
                 engine.telemetry.log_event(EventCategory.CAMPAIGN, "turn_status", stats, turn=i+1)
                 engine.telemetry.log_event(EventCategory.SYSTEM, "planet_update", {"planets": planet_data}, turn=i+1)
                  
                  # Phase 42: Detailed Faction Stats for Indexer compatibility
                 for f_name, f_mgr in engine.factions.items():
                     if f_name == "Neutral": continue
                     econ_cache = engine.economy_manager.faction_econ_cache.get(f_name, {})
                     
                     faction_report = {
                         "faction": f_name,
                         "economy": {
                             "upkeep_total": econ_cache.get("total_upkeep", 0),
                             "gross_income": econ_cache.get("income", 0),
                             "net_profit": econ_cache.get("income", 0) - econ_cache.get("total_upkeep", 0),
                             "research_points": getattr(f_mgr, 'budgets', {}).get("research", 0),
                             "idle_construction_slots": 0, 
                             "idle_research_slots": 0,
                             "promethium": econ_cache.get("income_by_category", {}).get("Mining", 0)
                         },
                         "territory": {
                             "total_controlled": p_counts.get(f_name, 0)
                         },
                         "military": {
                             "units_recruited": 0,
                             "units_lost": 0,
                             "battles_fought": 0,
                             "battles_won": 0,
                             "damage_dealt": 0
                         },
                         "deltas": {
                             "requisition": f_mgr.requisition,
                             "fleets_count": len([fl for fl in engine.fleets_by_faction.get(f_name, []) if not fl.is_destroyed])
                         }
                     }
                     # Phase 5: Inject Theater Stats
                     # Path: engine -> strategic_ai -> planner -> theater_manager
                     if hasattr(engine, 'strategic_ai') and hasattr(engine.strategic_ai.planner, 'theater_manager'):
                         tm = engine.strategic_ai.planner.theater_manager
                         my_theaters = [t for t in tm.theaters.values() if t.id.startswith(f"THEATER-{f_name}")]
                         
                         theater_list = []
                         for t in my_theaters:
                             theater_list.append({
                                 "name": t.name,
                                 "goal": t.assigned_goal,
                                 "threat": t.threat_score
                             })
                         theater_list.sort(key=lambda x: x["threat"], reverse=True)
                         faction_report["Theaters"] = theater_list
                         
                     engine.telemetry.log_event(EventCategory.CAMPAIGN, "faction_stats", faction_report, turn=i+1, faction=f_name)

                  # Phase 42: Flush Categorized Economic Data to Indexer
                 if hasattr(engine, 'indexer') and engine.indexer:
                     engine.telemetry.flush_economic_data(
                         engine.indexer, 
                         batch_id, 
                         run_id, 
                         universe, 
                         i+1
                     )
                     engine.telemetry.flush_battle_performance_data(
                         engine.indexer,
                         batch_id,
                         run_id,
                         universe,
                         i+1
                     )
            # ------------------------
            
            if i % 10 == 0:
                print(f"\n--- Turn {i+1} Status ---")
                for f_name, faction in engine.factions.items():
                    print(f"{f_name}: {faction.requisition} Req")
                
                print("Fleet Sizes:")
                for fleet in engine.fleets:
                    if not fleet.is_destroyed:
                        state = f"Moving to {fleet.destination.name}" if fleet.destination else "Orbiting"
                        print(f"  - {fleet.id}: {len(fleet.units)} units at {fleet.location.name} ({state})")
            
            if delay_seconds > 0:
                time.sleep(delay_seconds)
            # time.sleep(0.1)
            
    except KeyboardInterrupt:
        print(f"\n[SIM] Simulation interrupted by user at Turn {i+1}.")
        print("Simulation aborted.")
        
    print("\n=== END SIMULATION ===")
    
    # TELEMETRY FLUSH
    if hasattr(engine, 'telemetry') and engine.telemetry:
        from src.reporting.telemetry import EventCategory
        print("[SIM] Flushing telemetry and sending completion event...")
        engine.telemetry.log_event(EventCategory.SYSTEM, "simulation_complete", {
            "turns": turns,
            "final_state": "completed"
        })
        engine.telemetry.flush()
    
    print("Final Galaxy State:")
    
    # Tally up planets
    tally = {}
    for p in engine.all_planets:
        if p.owner not in tally: tally[p.owner] = 0
        tally[p.owner] += 1
        
    for faction, count in sorted(tally.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {faction}: {count} planets")

    # Tally fleets
    fleets_alive = len([f for f in engine.fleets if not f.is_destroyed])
    fleets_total = len(engine.fleets)
    print(f"\nFleets Operational: {fleets_alive}/{fleets_total}")
    
    # Log performance and cache stats
    engine.log_performance_metrics()
    
    return engine

if __name__ == "__main__":
    run_campaign_simulation(turns=30, planets=15)

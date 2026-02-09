import os
import csv
from typing import TYPE_CHECKING
from src.reporting.telemetry import EventCategory
from src.utils.profiler import profile_method, log_system_telemetry
from src.core.config import REPORTS_DIR
from src.config import logging_config

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine

class TurnProcessor:
    """
    Handles the sequential execution of the game turn loop, including:
    - Global phase (diplomacy, storms, cleanup)
    - Faction turns (economy, movement, combat)
    - End of turn stats and reporting
    """
    def __init__(self, engine: 'CampaignEngine'):
        self.engine = engine

    def process_faction_turns(self, fast_resolve: bool = False) -> None:
        """Sequential faction turn loop. Pruned of global logic now in TurnManager."""
        # --- SEQUENTIAL FACTION TURNS ---
        import time
        econ_start = time.time()
        
        ordered_factions = sorted([f.name for f in self.engine.get_all_factions() if f.name != "Neutral"])
        # Global pre-calculation for economy
        self.engine.economy_manager.faction_econ_cache = self.engine.economy_manager.resource_handler.precalculate_economics()
        
        # Phase 6: Capture living factions before they process their turn
        prior_living = [f.name for f in self.engine.get_all_factions() if f.is_alive and f.name != "Neutral"]

        for f_name in ordered_factions:
            # [TOTAL WAR STYLE] Refresh AI Caches for current world state
            if hasattr(self.engine, 'strategic_ai'):
                self.engine.strategic_ai.build_turn_cache()
            # [TOTAL WAR STYLE] Faction Window Isolation
            if self.engine.telemetry:
                self.engine.telemetry.log_event(EventCategory.CAMPAIGN, 'faction_turn_start', {
                    'faction': f_name, 
                    'turn': self.engine.turn_counter
                })

            self.process_faction_turn(f_name, fast_resolve=fast_resolve)
            
            if self.engine.telemetry:
                self.engine.telemetry.log_event(EventCategory.CAMPAIGN, 'faction_turn_end', {
                    'faction': f_name, 
                    'turn': self.engine.turn_counter
                })

        # --- WORLD PHASE (Global Logic & Cleanup) ---
        if self.engine.logger:
            self.engine.logger.system("<<< WORLD PHASE >>>")

        # Phase 6: Check for eliminations after all faction turns
        if logging_config.LOGGING_FEATURES.get('faction_elimination_analysis', False):
            post_living = [f.name for f in self.engine.get_all_factions() if f.is_alive and f.name != "Neutral"]
            for f_name in prior_living:
                if f_name not in post_living:
                    if self.engine.logger:
                        self.engine.logger.campaign(f"!!! [PHASE 6] Faction Eliminated: {f_name} !!!")
                    self.engine._log_faction_elimination(f_name)

        econ_total = time.time() - econ_start
        if hasattr(self.engine, 'performance_metrics'):
            self.engine.performance_metrics.setdefault('economy_phase_total', []).append(econ_total)
            
        # Feature 110: Periodic Telemetry Export
            
        # Feature 110: Periodic Telemetry Flush
        if self.engine.turn_counter % 10 == 0:
            if hasattr(self.engine, 'telemetry') and self.engine.telemetry:
                 log_system_telemetry(self.engine)
                 
                 # Log Tech Progress for all factions
                 if hasattr(self.engine, 'tech_manager'):
                     for f in self.engine.factions:
                         if f != "Neutral":
                             self.engine.tech_manager.log_tech_tree_progress(self.engine, f)

                 # Log Error Patterns
                 if self.engine.logger:
                     self.engine.logger.log_error_telemetry(self.engine)

                 # Phase 10: Lifecycle Metrics
                 if hasattr(self.engine, 'strategic_ai') and self.engine.strategic_ai:
                     ai = self.engine.strategic_ai
                     # Doctrine Effectiveness (Every 20 turns)
                     if self.engine.turn_counter % 20 == 0 and hasattr(ai, 'tech_doctrine_manager'):
                         for f_name in self.engine.factions:
                             if f_name != "Neutral":
                                 ai.tech_doctrine_manager.log_doctrine_effectiveness(f_name)
                     
                     # Tech ROI (Analyze techs unlocked 15 turns ago)
                     if hasattr(self.engine, 'tech_manager'):
                         roi_lookback = 15
                         target_turn = self.engine.turn_counter - roi_lookback
                         if target_turn >= 0:
                             for f_name, f_obj in self.engine.factions.items():
                                 if f_name == "Neutral" or not hasattr(f_obj, 'tech_unlocked_turns'): continue
                                 for tech_id, unlock_turn in f_obj.tech_unlocked_turns.items():
                                     if unlock_turn == target_turn:
                                         self.engine.tech_manager.log_tech_roi(self.engine, f_name, tech_id)


                 self.engine.telemetry.flush()
                 
                 # [REPORTING] Interim Reporting (Phase 5)
                 if hasattr(self.engine, 'generate_run_summary'):
                     self.engine.generate_run_summary()
                 if hasattr(self.engine.telemetry, 'generate_index'):
                     self.engine.telemetry.generate_index()
        # Phase 104: Production Advancement
        # Moved to Faction Turn Start (Total War Style)
        # for p in self.engine.all_planets:
        #     p.process_queue(self.engine)
            
        # Phase 16: Starbase Production Advancement
        # Moved to Faction Turn Start (Total War Style)
        # for s in self.engine.systems:
        #     for sb in s.starbases:
        #         if sb.is_alive():
        #             sb.process_queue(self.engine)
            
        if self.engine.logger:
             self.engine.logger.system(f"=== END OF TURN {self.engine.turn_counter} ===")
             
        # [TOTAL WAR STYLE] Final World Resolution
        # Handling everything that isn't specific to a single faction's agency phase
        # Moved to Faction Turn (Total War Style)
        # if hasattr(self.engine.battle_manager, 'process_active_battles'):
        #    self.engine.battle_manager.process_active_battles()
            
        # self.engine.battle_manager.resolve_ground_war()

        # 5. Cleanup Destroyed Fleets
        destroyed = [f for f in self.engine.fleets if f.is_destroyed]
        for f in destroyed:
            # MEMORY: Explicitly clear references
            f.location = None
            f.units.clear()
            f.cargo_armies.clear()
            f.destination = None
            self.engine.unregister_fleet(f)

        # 6. Collect Statistics
        turn_snapshot = {
            "Turn": self.engine.turn_counter,
            "Global_Fleets": len(self.engine.fleets),
            "Global_Battles": len(self.engine.battle_manager.active_battles) 
        }
        for faction_mgr in self.engine.get_all_factions():
            f_name = faction_mgr.name
            if f_name == "Neutral": continue
            turn_snapshot[f"{f_name}_Req"] = faction_mgr.requisition
            turn_snapshot[f"{f_name}_Income"] = faction_mgr.stats.get("turn_req_income", 0)
            turn_snapshot[f"{f_name}_Expense"] = faction_mgr.stats.get("turn_req_expense", 0)
        
        self.engine.stats_history.append(turn_snapshot)
        
        # MEMORY OPTIMIZATION: Flush stats history to disk periodically
        if len(self.engine.stats_history) >= 100:
             if self.engine.report_organizer:
                 self.flush_analytics(self.engine.report_organizer.run_path, self.engine.report_organizer.run_id)
             else:
                 # Even without organizer, clear to prevent memory leak
                 self.engine.stats_history = []
        
        # Phase 9: Narrative Turning Points
        self.engine.detect_narrative_turning_points()
        
        # [AUDIT] State Consistency Check
        if hasattr(self.engine, 'audit_scheduler') and self.engine.audit_scheduler:
             from src.core.config import ACTIVE_UNIVERSE
             self.engine.audit_scheduler.run_audit_cycle(ACTIVE_UNIVERSE, self.engine.turn_counter)
        
        self.engine.faction_reporter.finalize_turn()
        if self.engine.turn_counter > 0 and self.engine.turn_counter % self.engine.config.performance_log_interval == 0:
             self.engine.log_performance_metrics()
             
        if self.engine.telemetry:
            self.engine.telemetry.flush()
            
        # [PHASE 8] Deterministic Replay Snapshot
        # Create a snapshot at the end of the turn (after all processing)
        if hasattr(self.engine, 'snapshot_manager'):
             self.engine.snapshot_manager.create_snapshot(label=f"turn_{self.engine.turn_counter}")
            
        # Check Victory Conditions and Update Progress Telemetry
        winner = self.engine.check_victory_conditions()
        if winner:
            if self.engine.logger:
                self.engine.logger.campaign(f"!!! WINNER DECIDED: {winner} !!!")


    def _execute_mechanics_hook(self, faction_name, hook_name, context):
        if hasattr(self.engine, 'mechanics_engine'):
            self.engine.mechanics_engine.apply_mechanics(faction_name, hook_name, context)

    @profile_method
    def process_faction_turn(self, f_name: str, fast_resolve: bool = False) -> None:
        """Processes a single faction's turn sequentially (Total War Window)."""
        if self.engine.logger:
            self.engine.logger.system(f"|--- {f_name.upper()} ACTIVE WINDOW ---|")
            
        faction = self.engine.get_faction(f_name)
        context = {"faction": faction, "engine": self.engine, "turn": self.engine.turn_counter}
        
        # MECHANICS HOOK: Turn Start
        self._execute_mechanics_hook(f_name, "on_turn_start", context)
        
        # [TOTAL_WAR_STYLE] Army Turn Start Reset
        for p in self.engine.all_planets:
            for ag in p.armies:
                if ag.faction == f_name and not ag.is_destroyed:
                    ag.reset_turn_flags()

        # 0. Update Visibility (Fog of War)
        # Using intel_manager directly to avoid circular dependency or wrapper overhead
        self.engine.intel_manager.update_faction_visibility(f_name)
        
        # [TOTAL WAR STYLE] Turn Start Production
        # Queue processing happens at START of turn so player sees new units/buildings immediately.
        
        # 0.1 Planet Production
        faction_planets = [p for p in self.engine.all_planets if p.owner == f_name]
        for p in faction_planets:
            p.process_queue(self.engine)
            
        # 0.2 Starbase Production
        # Assuming starbases are tracked or we scan systems (inefficient but safe)
        # Optimally we should have a faction.starbases list. 
        # For now, scan systems:
        for s in self.engine.systems:
             for sb in s.starbases:
                 if sb.faction == f_name and sb.is_alive():
                     sb.process_queue(self.engine)
        
        # [TOTAL WAR STYLE] Fleet Consolidation
        # Organize fleets before the player/AI moves them.
        if hasattr(self.engine.fleet_manager, 'consolidate_fleets'):
             self.engine.fleet_manager.consolidate_fleets(max_size=self.engine.config.max_fleet_size, faction_filter=f_name)
        
        # [QUIRK] Phase-Based Unit Regeneration (Agnostic)
        regen_total = 0
        faction_fleets = [f for f in self.engine.fleets if f.faction == f_name and not f.is_destroyed]
        for f in faction_fleets:
            for u in f.units:
                active, amount = u.regenerate_infantry()
                if active: regen_total += amount
        
        # Phase 106: Regenerate ground armies on planets (Agnostic)
        for p in self.engine.all_planets:
            for ag in p.armies:
                if ag.faction == f_name and not ag.is_destroyed:
                    for u in ag.units:
                        active, amount = u.regenerate_infantry()
                        if active: regen_total += amount

        if regen_total > 0 and self.engine.logger:
            self.engine.logger.combat(f"[{f_name}] Regeneration protocols active. Restored {regen_total} HP across empire.")
        
        # 1. Strategy & Economy
        # 1. Strategy & Economy
        self.engine.strategic_ai.process_faction_strategy(f_name)

        # MECHANICS HOOK: Economy Phase
        self._execute_mechanics_hook(f_name, "on_economy_phase", context)

        self.engine.economy_manager.process_faction_economy(f_name)
        
        # 1.5 Orders for idle fleets
        # OPTIMIZATION: Update spatial indices ONCE before movement processing
        if hasattr(self.engine.battle_manager, '_update_presence_indices'):
            self.engine.battle_manager._update_presence_indices()

        faction_fleets = [f for f in self.engine.fleets if f.faction == f_name and not f.is_destroyed]
        for fleet in faction_fleets:
            landed_this_move = False
            # Movement
            move_status = fleet.update_movement(engine=self.engine)
            if move_status:
                # Fleet just ARRIVED (Target or Intercepted)
                arrival_type = "INTERCEPTED at" if move_status == "INTERCEPTED" else "arrived at"
                loc_name = fleet.location.name if hasattr(fleet.location, 'name') else 'system'
                if self.engine.logger:
                    self.engine.logger.campaign(f"{fleet.id} {arrival_type} {loc_name}")
                
                # Update visibility immediately upon arrival (before combat can kill the scout)
                self.engine.intel_manager.update_faction_visibility(f_name, force_refresh=True)
                
                # Update indices globally ONCE per faction turn (or sub-step if needed)
                # self.engine.battle_manager._update_presence_indices() # Assume done at start of turn or explicitly here if needed
                
                # Resolve battles regardless of whether it was the target or an intercept
                # Phase 16.5: Explicitly mark current faction as Aggressor (Total War Style)
                # OPTIMIZATION: update_indices=False to avoid O(N^2) rebuild inside loop
                self.engine.battle_manager.resolve_battles_at(fleet.location, update_indices=False, force_domain="space", aggressor_faction=f_name)
            
        # 3. Transport & Invasions (Check all fleets for this faction every turn)
        self.engine.battle_manager.process_invasions(faction_filter=f_name)

        # 4. Army Movement Processing
        for p in self.engine.all_planets:
            for ag in p.armies:
                if ag.faction == f_name and not ag.is_destroyed and ag.state == "MOVING":
                    ag.update_movement(engine=self.engine)
        
        # Phase 18: Starbase Construction Progress
        self.engine.construction_service.process_starbase_queues(f_name)

        # MECHANICS HOOK: Turn End
        self._execute_mechanics_hook(f_name, "on_turn_end", context)
        
        # [TOTAL WAR STYLE] End of Turn Combat Resolution
        # Force resolution of Space and Ground battles involving this faction
        # so they get immediate feedback on their actions.
        
        if hasattr(self.engine.battle_manager, 'process_active_battles'):
             self.engine.battle_manager.process_active_battles(faction_filter=f_name)
             
        # Resolve Ground Invasions initiated this turn
        self.engine.battle_manager.resolve_ground_war(faction_filter=f_name)

        # 4. Army Cleanup/Reinforcements (Delegated)
        strategy = self.engine.strategies.get(f_name, self.engine.default_strategy)
        strategy.process_reinforcements(f_name, self.engine)
        
        # 5. Resolve Ground Wars (Moved to Global Phase)
        # self.engine.battle_manager.resolve_ground_war()

    def flush_analytics(self, output_dir, run_id):
        """Flushes buffered stats to disk to free memory."""
        if not self.engine.stats_history: return
        
        keys = list(self.engine.stats_history[0].keys())
        filename = f"economy_{run_id}.csv"
        filepath = os.path.join(output_dir, filename)
        
        file_exists = os.path.exists(filepath)
        
        try:
            with open(filepath, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(self.engine.stats_history)
                
            self.engine.stats_history = [] # Clear memory
        except Exception as e:
            if self.engine.logger:
                self.engine.logger.error(f"Warning: Failed to flush analytics: {e}")

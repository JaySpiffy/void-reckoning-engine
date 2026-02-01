from typing import Dict, Any, Optional

class SalvageProcessor:
    """
    Handles post-battle salvage processing, including blueprint recovery and quality degradation.
    """

    @staticmethod
    def process_battle_salvage(state, factions_dict: Optional[Dict[str, Any]] = None):
        """
        Hook to capture destroyed units (wreckage), compute salvage quality,
        and register salvaged blueprints via BlueprintRegistry.
        """
        from src.utils.blueprint_registry import BlueprintRegistry
        from src.reporting.telemetry import EventCategory
        import copy
    
        for faction in state.battle_stats:
            wreckage_list = state.battle_stats[faction].get("wreckage", [])
            for wreckage in wreckage_list:
                blueprint_id = wreckage["blueprint_id"]
                quality = wreckage["quality"]
                
                # Load blueprint
                bp = BlueprintRegistry.get_instance().get_blueprint(blueprint_id)
                if bp:
                    salvaged_bp = copy.deepcopy(bp)
                    
                    # Apply quality degradation to universal_stats
                    if "universal_stats" in salvaged_bp:
                        for stat in salvaged_bp["universal_stats"]:
                            if isinstance(salvaged_bp["universal_stats"][stat], (int, float)):
                                salvaged_bp["universal_stats"][stat] *= quality
                            
                    # Add "Salvaged" trait
                    if "default_traits" not in salvaged_bp: salvaged_bp["default_traits"] = []
                    if "Salvaged" not in salvaged_bp["default_traits"]:
                        salvaged_bp["default_traits"].append("Salvaged")
                        
                    # --- DOCTRINE CHECK (Step 9) ---
                    f_obj = factions_dict.get(faction) if factions_dict else None
                    if f_obj and hasattr(f_obj, 'engine') and hasattr(f_obj.engine, 'ai_manager'):
                         ai_mgr = f_obj.engine.ai_manager
                         if not ai_mgr.filter_tech_by_doctrine(f_obj, blueprint_id, "salvage"):
                              # Doctrine rejects salvage
                              # print(f"  > [DOCTRINE] {faction} doctrine rejected salvaged {blueprint_id}")
                              ai_mgr.apply_doctrine_effects(f_obj, "reject_alien_tech", blueprint_id)
                              continue # Skip this salvage
    
                    # Helper method usage instead of singletons if possible, but this matches original logic
                    BlueprintRegistry.get_instance().register_blueprint(salvaged_bp, faction_owner=faction)
                    
                    # Award additional intel
                    salvage_intel = int(50 * quality)
                    if factions_dict and faction in factions_dict:
                        f_obj = factions_dict[faction]
                        if hasattr(f_obj, 'earn_intel') and salvage_intel > 0:
                            f_obj.earn_intel(salvage_intel, source="salvage", reason=f"Salvaged {blueprint_id}")
                            
                            # Also register in faction model if method exists
                            if hasattr(f_obj, 'register_salvaged_blueprint'):
                                salvaged_id = salvaged_bp.get("id", blueprint_id) # Ensure ID exists
                                f_obj.register_salvaged_blueprint(salvaged_id, quality, wreckage["killer_faction"], state.round_num)
                            
                            # Log Telemetry
                            if hasattr(f_obj, 'engine') and hasattr(f_obj.engine, 'telemetry'):
                                    f_obj.engine.telemetry.log_event(
                                        EventCategory.TECHNOLOGY, "blueprint_salvaged",
                                        {"faction": faction, "blueprint_id": blueprint_id, "quality": quality, "source_faction": wreckage["killer_faction"]},
                                        turn=getattr(f_obj.engine, 'turn_counter', 0),
                                        faction=faction
                                    )

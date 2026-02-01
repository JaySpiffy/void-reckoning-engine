import random
import copy
from typing import Optional, TYPE_CHECKING
from src.utils.blueprint_registry import BlueprintRegistry
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.managers.diplomacy_manager import DiplomacyManager

class DiplomaticActionHandler:
    """
    Executes specific diplomatic interactions like blueprint sharing.
    Handles verification of requirements (trust, treaties) for actions.
    """
    def __init__(self, diplomacy_manager: 'DiplomacyManager'):
        self.diplomacy_manager = diplomacy_manager
        self.engine: 'CampaignEngine' = diplomacy_manager.engine

    def share_blueprint(self, faction_a: str, faction_b: str, blueprint_id: str) -> bool:
        """High-trust factions exchange blueprints directly via treaties."""
        engine = self.engine
        rel_service = self.diplomacy_manager.relation_service
        treaty_coord = self.diplomacy_manager.treaty_coordinator
        
        # 1. Trust Check
        if rel_service.get_relation(faction_a, faction_b) < 50: return False
        
        # 2. Treaty Check
        if treaty_coord.get_treaty(faction_a, faction_b) != "Trade": return False
        
        # 3. Transfer
        bp = BlueprintRegistry.get_instance().get_blueprint(blueprint_id)
        if not bp: return False
        
        shared_bp = copy.deepcopy(bp)
        
        # --- DOCTRINE CHECK ---
        ai_mgr = engine.ai_manager
        f_b_obj = engine.factions.get(faction_b)
        if f_b_obj and hasattr(ai_mgr, 'filter_tech_by_doctrine'):
             if not ai_mgr.filter_tech_by_doctrine(f_b_obj, blueprint_id, "share"):
                  if engine.logger:
                       engine.logger.diplomacy(f"[DOCTRINE] {faction_b} rejected shared tech {blueprint_id} from {faction_a}")
                  
                  personality = getattr(f_b_obj, 'learned_personality', None)
                  if personality and getattr(personality, 'tech_doctrine', 'PRAGMATIC') == "XENOPHOBIC":
                       rel_service.modify_relation(faction_b, faction_a, -10)
                       
                  return False 
        
        # Add "Gifted" trait
        if "default_traits" not in shared_bp: shared_bp["default_traits"] = []
        if "Gifted" not in shared_bp["default_traits"]:
             shared_bp["default_traits"].append("Gifted")
             
        # Register with Faction B
        BlueprintRegistry.get_instance().register_blueprint(shared_bp, faction_owner=faction_b)
        
        # Meta storage in faction
        if f_b_obj:
             if hasattr(f_b_obj, 'register_shared_blueprint'):
                  f_b_obj.register_shared_blueprint(blueprint_id, faction_a, engine.turn_counter)
             
             if hasattr(f_b_obj, 'unlocked_techs') and blueprint_id not in f_b_obj.unlocked_techs:
                  f_b_obj.unlocked_techs.append(blueprint_id)
                       
             engine.faction_reporter.log_event(faction_b, "diplomacy", f"Received blueprint {blueprint_id} from {faction_a}")
             
             if hasattr(engine, 'telemetry'):
                  engine.telemetry.log_event(
                      EventCategory.TECHNOLOGY, "blueprint_shared",
                      {"faction_a": faction_a, "faction_b": faction_b, "blueprint_id": blueprint_id},
                      turn=engine.turn_counter
                  )
             
        # Relation Bonus
        rel_service.modify_relation(faction_a, faction_b, 5)
        
        # Phase 14: Alliance Effectiveness
        if treaty_coord.get_treaty(faction_a, faction_b) == "Alliance":
            treaty_coord.log_alliance_interaction(faction_a, faction_b, "shared_tech")
            
        if engine.logger:
             engine.logger.diplomacy(f"[DIPLOMACY] {faction_a} SHARED tech {blueprint_id} with {faction_b}")
             
        return True

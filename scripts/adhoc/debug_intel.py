import sys
import os
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.managers.intelligence_manager import IntelligenceManager
from src.models.faction import Faction

def debug_theft():
    engine = MagicMock()
    intel_mgr = IntelligenceManager(engine)
    
    f_name = "Imperium"
    target_f = "Orks"
    
    f_obj = Faction(f_name)
    target_f_obj = Faction(target_f)
    target_f_obj.unlocked_techs = ["OrkTech"]
    
    factions_dict = {f_name: f_obj, target_f: target_f_obj}
    
    # Mock engine.get_faction
    engine.get_faction.side_effect = lambda name: factions_dict.get(name)
    
    # Mock other needed things
    engine.ai_manager = MagicMock()
    engine.tech_manager = MagicMock()
    engine.tech_manager.analyze_tech_tree.return_value = {"OrkTech": 1.0}
    
    f_obj.visible_planets = {"GorkCity"}
    f_obj.intel_points = 500
    
    location = MagicMock()
    location.name = "GorkCity"
    location.is_sieged = False
    
    with patch("src.utils.blueprint_registry.BlueprintRegistry.get_instance") as mock_registry:
        mock_inst = mock_registry.return_value
        mock_inst.get_blueprint.return_value = {"id": "OrkTech", "universal_stats": {"damage": 10}, "default_traits": []}
        
        with patch("random.random", return_value=0.01), \
             patch("random.choices", return_value=["OrkTech"]):
            print(f"Calling attempt_blueprint_theft for {target_f}...")
            try:
                success = intel_mgr.attempt_blueprint_theft(f_name, target_f, location, engine)
                print(f"Success: {success}")
            except Exception as e:
                print(f"Caught exception: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    debug_theft()

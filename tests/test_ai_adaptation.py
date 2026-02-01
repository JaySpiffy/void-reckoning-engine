import pytest
from unittest.mock import MagicMock
from src.managers.ai_manager import StrategicAI
from src.managers.tech_manager import TechManager
from src.models.faction import Faction

@pytest.fixture
def ai_setup():
    engine = MagicMock()
    tech_manager = TechManager()
    engine.tech_manager = tech_manager
    ai = StrategicAI(engine)
    faction = Faction("Imperium")
    engine.factions = {"Imperium": faction}
    engine.turn_counter = 1
    return ai, engine, tech_manager, faction

def test_adaptation_logic(ai_setup):
    """Test the full AI adaptation lifecycle."""
    ai, engine, tech_manager, faction = ai_setup
    tech_id = "hybrid_st_wh40k_phaser_power_cell"
    
    # 1. Check availability (Should be false, prerequisites missing)
    assert not tech_manager.is_hybrid_tech_available(faction, tech_id)
    
    # 2. Add prerequisites
    faction.unlocked_techs = ["hand_phaser_tech", "lasgun_standardization"]
    assert tech_manager.is_hybrid_tech_available(faction, tech_id) is True
    
    # 3. Evaluate value
    score = ai.evaluate_hybrid_tech_value(faction, tech_id)
    assert score > 0
    
    # 4. Request adaptation (Lack of intel)
    faction.intel_points = 100
    success = ai.request_adaptation(faction, tech_id)
    assert success is False
    assert len(faction.pending_adaptations) == 0
    
    # 5. Earn intel and request again
    faction.earn_intel(3000)
    success = ai.request_adaptation(faction, tech_id)
    assert success is True
    assert len(faction.pending_adaptations) == 1
    assert faction.intel_points == 3100 # Not spent yet!
    
    # 6. Process turns
    ai.process_adaptation_requests(faction, 2)
    assert faction.pending_adaptations[0]["turns_left"] == 2
    assert faction.intel_points == 3100
    
    ai.process_adaptation_requests(faction, 3)
    ai.process_adaptation_requests(faction, 4)
    
    # Should be unlocked now and spent
    assert tech_id in faction.unlocked_techs
    assert faction.intel_points == 600 # Spent now!
    assert len(faction.pending_adaptations) == 0

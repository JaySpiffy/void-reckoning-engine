import pytest
from unittest.mock import MagicMock, patch
from src.managers.ai_manager import StrategicAI
from src.models.faction import Faction
from universes.base.personality_template import FactionPersonality

class MockEngine:
    def __init__(self):
        self.turn_counter = 1
        self.factions = {}
        self.diplomacy = MagicMock()
        self.diplomacy.treaties = {}
        self.all_planets = []
        self.planets_by_faction = {}
        self.fleets = []
        self.intelligence_manager = MagicMock()
        self.telemetry = MagicMock()
        self.faction_reporter = MagicMock()
        self.morale_manager = MagicMock()

    def get_faction(self, name):
        return self.factions.get(name)

@pytest.fixture
def ai_manager():
    engine = MockEngine()
    hybrid_mgr = MagicMock()
    # Setup default mock returns to avoid MagicMock > float errors
    hybrid_mgr.analyze_tech_tree.return_value = {"default": 1.0}
    hybrid_mgr.get_hybrid_tech_requirements.return_value = {"intel_cost": 100, "research_turns": 5}
    
    engine.tech_manager = hybrid_mgr
    ai = StrategicAI(engine)
    
    # Patch personality manager to avoid disk I/O and ensure test isolation
    ai.personality_manager = MagicMock()
    
    return ai, engine, hybrid_mgr

def test_doctrine_filtering_radical(ai_manager):
    ai, engine, hybrid_mgr = ai_manager
    faction = Faction("Chaos", 1000)
    personality = FactionPersonality("Chaos", tech_doctrine="RADICAL")
    
    ai.personality_manager.get_faction_personality.return_value = personality
    
    # RADICAL should accept anything
    assert ai.filter_tech_by_doctrine(faction, "alien_tech_1", "theft") is True
    assert ai.filter_tech_by_doctrine(faction, "alien_tech_2", "salvage") is True
    assert ai.filter_tech_by_doctrine(faction, "alien_tech_3", "research") is True

def test_doctrine_filtering_puritan(ai_manager):
    ai, engine, hybrid_mgr = ai_manager
    faction = Faction("Imperium", 1000)
    personality = FactionPersonality("Imperium", tech_doctrine="PURITAN")
    
    ai.personality_manager.get_faction_personality.return_value = personality
    
    # PURITAN should reject theft and salvage checks
    # Note: Logic says if acquisition_type in ["theft", "salvage"] return False
    assert ai.filter_tech_by_doctrine(faction, "alien_tech_1", "theft") is False
    assert ai.filter_tech_by_doctrine(faction, "alien_tech_2", "salvage") is False
    # Research might be allowed depending on logic (test says False for research too if Puritan means NO ALIEN TECH)
    # The actual logic: elif doctrine == "PURITAN": ... return False # Reject hybrid research
    assert ai.filter_tech_by_doctrine(faction, "alien_tech_3", "research") is False

def test_doctrine_filtering_pragmatic_high_value(ai_manager):
    ai, engine, hybrid_mgr = ai_manager
    faction = Faction("Orks", 1000)
    personality = FactionPersonality("Orks", tech_doctrine="PRAGMATIC")
    
    ai.personality_manager.get_faction_personality.return_value = personality
    
    # High value tech (> 3.0)
    # Mock evaluate_hybrid_tech_value directly on TechDoctrineManager delegate to be sure,
    # or rely on calculation. 5.0 base / (100 cost / 100) -> 5.0 * 1000 = 5000 >> 3.0
    # Let's mock the evaluate method for precision
    with patch.object(ai.tech_doctrine_manager, 'evaluate_hybrid_tech_value', return_value=5.0):
        assert ai.filter_tech_by_doctrine(faction, "good_tech", "theft") is True

def test_doctrine_filtering_pragmatic_low_value(ai_manager):
    ai, engine, hybrid_mgr = ai_manager
    faction = Faction("Orks", 1000)
    personality = FactionPersonality("Orks", tech_doctrine="PRAGMATIC")
    
    ai.personality_manager.get_faction_personality.return_value = personality
    
    # Low value tech (<= 3.0)
    with patch.object(ai.tech_doctrine_manager, 'evaluate_hybrid_tech_value', return_value=1.5):
        assert ai.filter_tech_by_doctrine(faction, "bad_tech", "theft") is False

def test_doctrine_effects_radical_bonus(ai_manager):
    ai, engine, hybrid_mgr = ai_manager
    faction = Faction("Chaos", 1000)
    personality = FactionPersonality("Chaos", tech_doctrine="RADICAL")
    
    ai.personality_manager.get_faction_personality.return_value = personality
    
    faction.research_multiplier = 1.0
    
    ai.apply_doctrine_effects(faction, "complete_adaptation", "tech_x")
    
    # RADICAL gets 1.1x multiplier
    assert faction.research_multiplier == pytest.approx(1.1)

def test_doctrine_effects_puritan_morale(ai_manager):
    ai, engine, hybrid_mgr = ai_manager
    faction = Faction("Imperium", 1000)
    personality = FactionPersonality("Imperium", tech_doctrine="PURITAN")
    
    ai.personality_manager.get_faction_personality.return_value = personality
    
    ai.apply_doctrine_effects(faction, "reject_alien_tech", "tech_y")
    
    engine.morale_manager.modify_faction_morale.assert_called_with("Imperium", 5, reason="Rejected alien tech tech_y")

def test_intel_driven_research_automation(ai_manager):
    ai, engine, hybrid_mgr = ai_manager
    faction = Faction("Tau", 1000)
    faction.intel_points = 1000
    personality = FactionPersonality("Tau", tech_doctrine="RADICAL")
    
    ai.personality_manager.get_faction_personality.return_value = personality
    
    hybrid_mgr.hybrid_tech_trees = {"tech_1": {}}
    hybrid_mgr.is_hybrid_tech_available.return_value = True
    hybrid_mgr.get_hybrid_tech_requirements.return_value = {"intel_cost": 200, "research_turns": 5}
    
    # Set turn counter to bypass cooldown
    engine.turn_counter = 15
    faction.last_hybrid_tech_request_turn = 0
    
    # Mock evaluation to return high score
    with patch.object(ai.tech_doctrine_manager, 'evaluate_hybrid_tech_value', return_value=10.0):
        ai.process_intel_driven_research(faction, 15)
        
    # Check if tech was queued
    assert "tech_1" in [a["tech_id"] for a in faction.pending_adaptations]
    assert faction.last_hybrid_tech_request_turn == 15

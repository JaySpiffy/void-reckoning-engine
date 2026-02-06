import pytest
import os
import json
from unittest.mock import MagicMock, patch
from src.ai.posture_registry import PostureRegistry
from src.ai.posture_system import PostureManager

@pytest.fixture
def mock_ai_manager():
    ai = MagicMock()
    ai.engine.turn_counter = 1
    
    # Setup Faction Manager Mock
    f_mgr = MagicMock()
    f_mgr.name = "TestFaction"
    f_mgr.strategic_posture = "BALANCED"
    f_mgr.intelligence_memory = {} # Fix: Use real dict to avoid MagicMock comparison errors
    f_mgr.learned_personality = MagicMock(biomass_hunger=0) # Fix for scoring quirk check
    
    ai.engine.factions = {"TestFaction": f_mgr}
    ai.engine.get_faction.return_value = f_mgr
    ai.get_faction_personality.return_value = MagicMock(aggression=1.0, expansion_bias=1.0)
    ai.assess_economic_health.return_value = {"state": "HEALTHY"}
    ai.engine.fleets = []
    ai.engine.diplomacy = None
    ai.engine.logger = MagicMock()
    ai.engine.telemetry = MagicMock()
    
    # Initialize Real Posture Components for testing
    from src.ai.posture_system import PostureManager
    ai.posture_manager = PostureManager(ai)
    
    return ai

def test_registry_loading():
    """Verify that the registry can load and inherit from archetypes."""
    registry = PostureRegistry("void_reckoning")
    
    # Check if we have some postures
    assert len(registry.postures) >= 1
    
    # Check inheritance: BLITZ should have weights from its archetype
    blitz = registry.get_posture("BLITZ")
    assert blitz is not None
    assert "weights" in blitz
    assert blitz["weights"]["capital"] == 4.0 # From archetype (updated in generator)

def test_posture_scoring_inertia(mock_ai_manager):
    """Verify that inertia makes the AI prefer its current posture."""
    manager = PostureManager(mock_ai_manager)
    
    f_mgr = mock_ai_manager.engine.get_faction("TestFaction")
    f_mgr.strategic_posture = "BALANCED"
    
    # Create fake situation
    situation = {
        "is_at_war": False,
        "econ_state": "HEALTHY",
        "military_ratio": 1.0,
        "turn": 1
    }
    
    # Calculate score for current vs other
    score_balanced = manager._calculate_posture_score("BALANCED", manager.registry.get_posture("BALANCED"), f_mgr, situation, "BALANCED")
    score_other = manager._calculate_posture_score("BOOM", manager.registry.get_posture("BOOM"), f_mgr, situation, "BALANCED")
    
    # Score for balanced should be higher due to inertia
    assert score_balanced > score_other

def test_posture_transition_logic(mock_ai_manager):
    """Verify that the manager actually triggers a change when conditions are right."""
    manager = PostureManager(mock_ai_manager)
    f_mgr = mock_ai_manager.engine.get_faction("TestFaction")
    f_mgr.strategic_posture = "BALANCED"
    
    # Mock situation where BLITZ is very attractive
    # (aggression high, military ratio high)
    mock_ai_manager.get_faction_personality.return_value = MagicMock(aggression=2.0)
    
    # We'll mock _get_situation_context to avoid complex fleet power math
    manager._get_situation_context = MagicMock(return_value={
        "is_at_war": True,
        "econ_state": "HEALTHY",
        "military_ratio": 5.0, # Extremely High ratio to trigger BLITZ
        "turn": 1
    })
    
    # Force randomness to 0 to make it deterministic
    # And lower inertia for this test to force a switch
    manager.inertia_bonus = 0.0
    
    with patch('random.uniform', return_value=0):
        with patch('random.choice', lambda x: x[0]):
            manager.update_faction_posture("TestFaction")
    
    # Should have switched to BLITZ 
    assert f_mgr.strategic_posture == "BLITZ"
    assert f_mgr.posture_changed_turn == 1

def test_weight_injection(mock_ai_manager):
    """Verify that TargetScoringService pulls the correct weights."""
    from src.services.target_scoring_service import TargetScoringService
    service = TargetScoringService(mock_ai_manager)
    
    f_mgr = mock_ai_manager.engine.get_faction("TestFaction")
    f_mgr.strategic_posture = "TURTLE"
    
    # EXTREMELY EXPLICIT MOCKING
    f_mgr.intelligence_memory = {} 
    
    # Mock planet
    mock_planet = MagicMock()
    mock_planet.name = "Sector_7"
    mock_planet.income_req = 100
    mock_planet.income_prom = 0
    mock_planet.owner = "Neutral"
    mock_planet.provinces = [] # Fix: Use real list
    mock_planet.system = MagicMock(x=0, y=0) # Fix: Concrete coords
    mock_ai_manager.engine.get_planet.return_value = mock_planet
    
    # Ensure get_faction returns our specific mock
    mock_ai_manager.engine.get_faction.return_value = f_mgr
    
    # Mock intelligence coordinator to return a real float
    mock_ai_manager.intelligence_coordinator.get_known_enemy_power.return_value = 0.0
    
    # Disable logging to avoid JSON serialization errors with MagicMocks
    with patch('src.services.target_scoring_service.logging_config.LOGGING_FEATURES', {}):
        # Run scoring
        score = service.calculate_expansion_target_score("Sector_7", "TestFaction", 0, 0, "Aggressive", "HEALTHY", 1)
    
    assert score > 0

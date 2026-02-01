import pytest
from unittest.mock import MagicMock
from src.managers.diplomacy_manager import DiplomacyManager

@pytest.fixture
def diplo_manager():
    factions = ["Imperium", "Orks", "Chaos"]
    engine = MagicMock()
    engine.turn_counter = 1 # Fix: Needs to be int for comparisons
    return DiplomacyManager(factions, engine)

def test_grudge_impact_on_relations(diplo_manager):
    """Test that grudges reduce the effective relation score."""
    f1 = "Imperium"
    f2 = "Orks"
    
    # Base relation
    base = diplo_manager.get_relation(f1, f2)
    
    # Add Grudge
    diplo_manager.add_grudge(f1, f2, 50, "Raided World")
    
    # Check new relation
    new_rel = diplo_manager.get_relation(f1, f2)
    assert new_rel == base - 50
    
    # Verify grudge data
    assert diplo_manager.grudges[f1][f2]['value'] == 50
    assert diplo_manager.grudges[f1][f2]['reason'] == "Raided World"

def test_grudge_decay(diplo_manager):
    """Test that grudges decay over time."""
    f1 = "Imperium"
    f2 = "Chaos"
    
    diplo_manager.add_grudge(f1, f2, 10, "Heresy")
    
    # Decay is 0.5 per turn
    diplo_manager.process_turn()
    
    assert diplo_manager.grudges[f1][f2]['value'] == 9.5
    
    # Check relation impact integration
    base = diplo_manager.relations[f1][f2]
    expected = base - 9.5
    # get_relation casts to int (truncates)
    assert diplo_manager.get_relation(f1, f2) == int(expected)

def test_grudge_removal(diplo_manager):
    """Test that grudges are removed when they decay to zero."""
    f1 = "Imperium"
    f2 = "Orks"
    
    # Small grudge
    diplo_manager.add_grudge(f1, f2, 0.4, "Minor Insult")
    # Decay is 0.5
    
    diplo_manager.process_turn()
    
    # Should be gone
    assert f2 not in diplo_manager.grudges[f1]
    
    # Relation should return to base
    assert diplo_manager.get_relation(f1, f2) == diplo_manager.relations[f1][f2]

def test_add_grudge_accumulates(diplo_manager):
    """Test that adding multiple grudges sums up."""
    f1 = "Chaos"
    f2 = "Imperium"
    
    diplo_manager.add_grudge(f1, f2, 10, "First Strike")
    diplo_manager.add_grudge(f1, f2, 20, "Second Strike")
    
    assert diplo_manager.grudges[f1][f2]['value'] == 30
    assert diplo_manager.grudges[f1][f2]['reason'] == "Second Strike" # Should update reason for major acts

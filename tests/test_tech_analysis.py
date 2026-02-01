import pytest
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.managers.tech_manager import TechManager

def test_tech_scorng_logic():
    """Test that analyze_tech_tree correctly calculates unlock values."""
    tm = TechManager()
    
    # Manual setup of a fake faction tree
    # Graph:
    # Tech A --> Unit 1
    # Tech A --> Tech B
    # Tech B --> Unit 2
    # Tech B --> Unit 3
    
    # Expected Scores:
    # Tech B: Unlocks Unit 2 (1) + Unit 3 (1) = 2.0
    # Tech A: Unlocks Unit 1 (1) + Tech B (0.5 + 2.0) = 3.5
    
    fake_tree = {
        "techs": {
            "Tech A": 100,
            "Tech B": 200
        },
        "units": {
            "Unit 1": "Tech A",
            "Tech B": "Tech A", # Tech B requires Tech A
            "Unit 2": "Tech B",
            "Unit 3": "Tech B"
        }
    }
    
    tm.faction_tech_trees["test_faction"] = fake_tree
    
    scores = tm.analyze_tech_tree("test_faction")
    
    print(f"Scores: {scores}")
    
    assert scores["Tech B"] == 2.0
    assert scores["Tech A"] == 3.5

def test_tech_scoring_diamonds():
    """Test efficient traversal for shared dependencies (Diamond pattern)."""
    # Graph:
    # Root --> Branch 1
    # Root --> Branch 2
    # Branch 1 --> Final Unit
    # Branch 2 --> Final Unit (Shared Unlock? Or different paths?)
    # In tree structure, a unit usually has ONE parent.
    # If a unit requires [Tech A, Tech B], unit_parser supports list.
    # But TechManager mermaid parsing maps 1 parent.
    # "Child -> Parent". One parent key.
    # So tech trees are strictly Hierarchical (Trees/Forests), not DAGs (usually) in this storage model.
    # Child key is unique.
    
    # Let's test deep chain.
    # A -> B -> C -> Unit
    
    fake_tree_chain = {
        "techs": {"A": 1, "B": 1, "C": 1},
        "units": {
            "B": "A",
            "C": "B",
            "Unit": "C"
        }
    }
    tm = TechManager()
    tm.faction_tech_trees["chain"] = fake_tree_chain
    scores = tm.analyze_tech_tree("chain")
    
    # C: 1 (Unit)
    # B: 0.5 + 1 = 1.5
    # A: 0.5 + 1.5 = 2.0
    
    assert scores["C"] == 1.0
    assert scores["B"] == 1.5
    assert scores["A"] == 2.0

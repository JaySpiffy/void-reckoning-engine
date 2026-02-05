import pytest
from unittest.mock import MagicMock, patch
from src.managers.diplomacy_manager import DiplomacyManager

@pytest.fixture
def mock_engine():
    e = MagicMock()
    e.logger = MagicMock()
    e.faction_reporter = MagicMock()
    e.telemetry = MagicMock()
    e.turn_counter = 1
    e.factions = {"FactionA": MagicMock(), "FactionB": MagicMock(), "FactionC": MagicMock()}
    
    for f in e.factions.values():
        f.stats = {"turn_diplomacy_actions": 0}
        f.requisition = 1000
    
    # Mocking necessary managers
    e.economy_manager = MagicMock()
    e.economy_manager.get_faction_economic_report.return_value = {"margin": 1.5, "balance": 5000}
    e.tech_manager = MagicMock()
    e.tech_manager.analyze_tech_tree.return_value = {}
    e.strategic_ai = MagicMock()
    e.strategic_ai.predict_enemy_threats.return_value = []
    e.report_organizer = MagicMock()
    e.planets_by_faction = {}
    
    # Disable FOW by populating known_factions
    for f_name, f_obj in e.factions.items():
        f_obj.known_factions = ["FactionA", "FactionB", "FactionC", "FactionD"]
        f_obj.name = f_name
    
    # Mock engine.get_faction
    def get_f(n): return e.factions.get(n)
    e.get_faction.side_effect = get_f

    return e

@pytest.fixture
def diplomacy_mgr(mock_engine):
    factions = ["FactionA", "FactionB", "FactionC"]
    
    with patch("src.services.relation_service.UniverseDataManager") as mock_udm:
        mock_instance = mock_udm.get_instance.return_value
        mock_instance.get_historical_bias.return_value = {}
        
        dm = DiplomacyManager(factions, mock_engine)
        return dm

def test_mutual_enemy_drift(diplomacy_mgr):
    """
    Test that Faction A and B's relation improves when they share an enemy C.
    """
    # Baseline relations: Neutral (0)
    diplomacy_mgr.relation_service.relations["FactionA"]["FactionB"] = 0
    diplomacy_mgr.relation_service.relations["FactionB"]["FactionA"] = 0
    
    # Setup Wars: Both A and B are at war with C
    # We must set both directions for the war matrix to pick it up correctly
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionA", "FactionC", "War")
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionB", "FactionC", "War")
    
    # Synchronize the war matrix (usually handles itself on _set_treaty through invalidate_war_cache)
    # DiplomacyManager._set_treaty calls treaty_coordinator.set_treaty and invalidate_war_cache.
    # We used treaty_coordinator.set_treaty directly, so we need to invalidate cache.
    diplomacy_mgr.invalidate_war_cache()
    
    # Verify setup
    assert "FactionC" in diplomacy_mgr.get_enemies("FactionA")
    assert "FactionC" in diplomacy_mgr.get_enemies("FactionB")
    
    # 2. Execute process_turn
    diplomacy_mgr.process_turn()
    
    # 3. Verify Drift
    # Expected: 0 + 1 = 1
    new_rel = diplomacy_mgr.get_relation("FactionA", "FactionB")
    assert new_rel == 1, f"Expected relation 1 (0 + 1), but got {new_rel}"

def test_mutual_enemy_drift_stacked(diplomacy_mgr):
    """
    Test that Faction A and B's relation improves more when they share multiple enemies.
    """
    diplomacy_mgr.factions.append("FactionD")
    diplomacy_mgr.relation_service.factions.append("FactionD")
    diplomacy_mgr.relation_service.relations["FactionA"]["FactionB"] = 0
    diplomacy_mgr.relation_service.relations["FactionB"]["FactionA"] = 0
    
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionA", "FactionC", "War")
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionB", "FactionC", "War")
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionA", "FactionD", "War")
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionB", "FactionD", "War")
    
    diplomacy_mgr.invalidate_war_cache()
    
    # 2 mutual enemies: FactionC and FactionD -> +2
    diplomacy_mgr.process_turn()
    
    new_rel = diplomacy_mgr.get_relation("FactionA", "FactionB")
    assert new_rel == 2, f"Expected relation 2 (0 + 2), but got {new_rel}"

def test_mutual_enemy_drift_cap(diplomacy_mgr):
    """
    Test that Faction A and B's relation stops drifting at +40.
    """
    # Start at +39
    diplomacy_mgr.relation_service.relations["FactionA"]["FactionB"] = 39
    diplomacy_mgr.relation_service.relations["FactionB"]["FactionA"] = 39
    
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionA", "FactionC", "War")
    diplomacy_mgr.treaty_coordinator.set_treaty("FactionB", "FactionC", "War")
    diplomacy_mgr.invalidate_war_cache()
    
    # Mock random.random to prevent accidental trade treaties during cap test
    with patch("random.random", return_value=1.0):
        # First Turn: 39 -> 40
        diplomacy_mgr.process_turn()
        assert diplomacy_mgr.get_relation("FactionA", "FactionB") == 40
        
        # Second Turn: Should stay at 40
        diplomacy_mgr.process_turn()
        assert diplomacy_mgr.get_relation("FactionA", "FactionB") == 40

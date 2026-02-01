import pytest
from unittest.mock import MagicMock
from src.managers.battle_manager import BattleManager
from src.models.unit import Regiment
from src.models.faction import Faction

def test_unit_loss_tracking():
    """Verify turn_units_lost is incremented after battle finalization."""
    
    # Setup Context
    context = MagicMock()
    context.factions = {
        "Imperium": Faction("Imperium"),
        "Orks": Faction("Orks")
    }
    context.logger = MagicMock()
    context.telemetry = MagicMock()
    
    bm = BattleManager(context)
    
    # Mock Battle State
    battle = MagicMock()
    # 2 Imperium Units (1 Dead), 2 Ork Units (2 Dead)
    imp1 = Regiment("Guard 1", 30, 30, 10, 5, 5, {}, faction="Imperium")
    imp2 = Regiment("Guard 2", 30, 30, 10, 5, 5, {}, faction="Imperium")
    ork1 = Regiment("Boy 1", 30, 30, 10, 5, 5, {}, faction="Orks")
    ork2 = Regiment("Boy 2", 30, 30, 10, 5, 5, {}, faction="Orks")
    
    imp1.current_hp = 0 # Dead
    ork1.current_hp = 0 # Dead
    ork2.current_hp = 0 # Dead
    
    battle.state.armies_dict = {
        "Imperium": [imp1, imp2],
        "Orks": [ork1, ork2]
    }
    battle.state.round_num = 5
    
    # Mock Planet
    planet = MagicMock()
    planet.name = "Test World"
    
    # Execute Finalize
    # We need to mock _sync methods too as they might fail with Mocks
    bm._sync_fleet_status = MagicMock()
    bm._sync_army_status = MagicMock()
    
    bm._finalize_battle(battle, planet, "Imperium", 1)
    
    # Verify Stats
    stats_imp = context.factions["Imperium"].stats
    stats_ork = context.factions["Orks"].stats
    
    assert stats_imp["turn_units_lost"] == 1
    assert stats_imp["units_lost"] == 1
    
    assert stats_ork["turn_units_lost"] == 2
    assert stats_ork["units_lost"] == 2
    
    print("\nUnit Loss Tracking Verified!")

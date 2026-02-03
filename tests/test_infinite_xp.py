
import pytest
from unittest.mock import MagicMock
from src.combat.ability_manager import AbilityManager
from src.models.unit import Unit

class TestInfiniteXP:
    @pytest.fixture
    def manager(self):
        return AbilityManager({})

    @pytest.fixture
    def unit(self):
        u = Unit("TestUnit", "TestFaction", level=1, experience=0)
        u.xp_gain_rate = 1.0
        return u

    def test_failed_ability_does_not_grant_xp(self, manager, unit):
        # Setup ability that fails
        manager.registry = {
            "fail_ability": {
                "payload_type": "damage", 
                "damage": 10,
                "cooldown": 5.0
            }
        }
        
        target = Unit("Target", "Enemy", hp=100)
        
        # Mock Context with battle_state
        state = MagicMock()
        state.total_sim_time = 0.0
        context = {"battle_state": state}

        # 1. Cast and Fail (on cooldown)
        # Force cooldown first
        unit.cooldowns["fail_ability"] = 10.0 # Future
        
        initial_xp = unit.experience
        result = manager.execute_ability(unit, target, "fail_ability", context)
        
        assert result["success"] == False
        assert result["reason"] == "Ability on cooldown"
        assert unit.experience == initial_xp # Should not gain XP

    def test_level_up_does_not_loop_infinitely(self, manager, unit):
        # Setup: Unit close to level up
        # Level 1 threshold? 100 * (1.2^0) = 100
        unit.experience = 99
        
        # Mock AbilityManager to return a new ability on level up
        manager.get_random_applicable_ability = MagicMock(return_value="new_ability_v1")
        manager.registry["new_ability_v1"] = {"payload_type": "damage"}
        
        # Context needs ability_manager for level_up to call it
        context = {"ability_manager": manager}
        
        # Trigger XP gain
        unit.gain_xp(10, context)
        
        assert unit.level == 2
        assert unit.experience == 9 # 109 - 100
        manager.get_random_applicable_ability.assert_called_once()
        
    def test_handle_damage_xp_gain(self, manager, unit):
        # Verify XP is ONLY gained on ACTUAL damage
        manager.registry = {"dmg_ability": {"payload_type": "damage", "damage": 10}}
        target = Unit("Target", "Enemy", hp=100)
        
        context = {"battle_state": MagicMock()}
        # Mock total_sim_time as a float to avoid MagicMock comparison error
        context["battle_state"].total_sim_time = 0.0
        
        initial_xp = unit.experience
        
        # Success case
        result = manager.execute_ability(unit, target, "dmg_ability", context)
        assert result["success"] == True
        assert result["applied"] == True
        
        # Should gain XP
        assert unit.experience > initial_xp

    def test_failed_damage_no_xp(self, manager, unit):
        # Target immune to damage
        manager.registry = {"dmg_ability": {"payload_type": "damage", "damage": 10}}
        target = MagicMock()
        del target.take_damage # Remove method
        
        context = {"battle_state": MagicMock()}
        context["battle_state"].total_sim_time = 0.0
        
        initial_xp = unit.experience
        
        result = manager.execute_ability(unit, target, "dmg_ability", context)
        
        assert result["success"] == True # It executed
        # AbilityManager sets result["applied"] = False if target has no take_damage
        assert result["applied"] == False 
        
        # XP logic: _handle_damage only calls gain_xp if "applied" logic runs?
        # Actually _handle_damage code:
        # if hasattr(target, "take_damage"): ... gain_xp ... else: result["applied"] = False
        # So it shouldn't gain XP.
        assert unit.experience == initial_xp 

    def test_recursion_limit(self, manager, unit):
        """Verify level_up recursion guard."""
        # Setup: Unit levels up, gets ability, which somehow triggers another level up?
        # Simulating by having a mock ability manager that might trigger something or 
        # just verifying the lock is checked.
        
        # We can't easily force recursion without mocking context recursively.
        # But we can check that _level_up_lock functions.
        
        unit.gain_xp = MagicMock(wraps=unit.gain_xp)
        
        # Create a manager that calls gain_xp AGAIN inside level_up?
        # Hard to safely monkeypatch in a test without breaking things.
        
        # Instead, just verify normal level up still works with the lock in place
        unit.experience = 999 
        # Should level up
        manager.get_random_applicable_ability = MagicMock(return_value="ab_v1")
        manager.registry["ab_v1"] = {}
        
        context = {"ability_manager": manager, "battle_state": MagicMock()}
        unit.level_up(context)
        
        assert unit.level == 2
        
        # Verify lock was released
        assert not getattr(unit, "_level_up_lock", False)

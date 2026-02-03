
import pytest
from unittest.mock import MagicMock
from src.combat.ability_manager import AbilityManager
from src.models.unit import Unit
from src.combat.combat_state import CombatState

class TestAbilityCooldown:
    @pytest.fixture
    def mock_registry(self):
        return {
            "test_ability": {
                "id": "test_ability",
                "payload_type": "damage",
                "cooldown": 5.0,
                "cost": {} 
            }
        }

    @pytest.fixture
    def manager(self, mock_registry):
        return AbilityManager(mock_registry)

    @pytest.fixture
    def unit(self):
        return Unit(name="TestUnit", faction="TestFaction")

    @pytest.fixture
    def target(self):
        return Unit(name="TargetUnit", faction="EnemyFaction")
        
    @pytest.fixture
    def combat_state(self):
        state = MagicMock(spec=CombatState)
        state.total_sim_time = 0.0
        # Mock armies_dict for context
        state.armies_dict = {"TestFaction": [], "EnemyFaction": []}
        return state

    def test_cooldown_application(self, manager, unit, target, combat_state):
        # Setup context
        context = {"battle_state": combat_state}
        
        # 1. First Cast (T=0) - Should Succeed
        result = manager.execute_ability(unit, target, "test_ability", context)
        assert result["success"] is True
        assert "test_ability" in unit.cooldowns
        assert unit.cooldowns["test_ability"] == 5.0
        
        # 2. Immediate Second Cast (T=0) - Should Fail
        result_fail = manager.execute_ability(unit, target, "test_ability", context)
        assert result_fail["success"] is False
        assert result_fail["reason"] == "Ability on cooldown"
        
        # 3. Advance Time partially (T=2.0) - Should Fail
        combat_state.total_sim_time = 2.0
        result_fail_2 = manager.execute_ability(unit, target, "test_ability", context)
        assert result_fail_2["success"] is False
        
        # 4. Advance Time to ready (T=6.0) - Should Succeed
        combat_state.total_sim_time = 6.0
        result_success = manager.execute_ability(unit, target, "test_ability", context)
        assert result_success["success"] is True
        assert unit.cooldowns["test_ability"] == 11.0 # 6 + 5

    def test_cooldown_no_context(self, manager, unit, target):
        # Without context (no time), it should allow if cooldown dict is empty, but fail if manually set
        # This behavior depends on how we handle missing context, but let's test the specific logic
        
        # 1. Cast without context
        # The manager defaults time to 0.0 if not found
        result = manager.execute_ability(unit, target, "test_ability", None)
        assert result["success"] is True
        # It should set timestamp to 0 + 5.0 = 5.0
        assert unit.cooldowns["test_ability"] == 5.0
        
        # 2. Cast again without context
        # Time defaults to 0.0. Ready at 5.0. 0.0 < 5.0 -> Fail
        result_fail = manager.execute_ability(unit, target, "test_ability", None)
        assert result_fail["success"] is False

if __name__ == "__main__":
    pytest.main([__file__])

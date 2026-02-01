
import pytest
import unittest
from unittest.mock import MagicMock
from src.managers.battle_manager import BattleManager
from src.managers.combat.invasion_manager import InvasionManager
from src.models.unit import Unit

class MockPlanet:
    def __init__(self, name, owner):
        self.name = name
        self.owner = owner
        self.is_sieged = False
        self.buildings = []
        self.provinces = []

class MockUnit(Unit):
    def __init__(self, name, faction, is_ship_val=False):
        self.name = name
        self.faction = faction
        self.is_alive = lambda: True
        self.current_hp = 100
        self.base_hp = 100
        self.is_ship = lambda: is_ship_val
        self.is_deployed = True
        self.xp_gain_rate = 100
        self.rank = 0
        self.next_level_xp = 100
        self.xp = 0
        self.service_record = []
        
    def gain_xp(self, amount, turn=0):
        pass
        
    def log_service_event(self, event, details, turn):
        pass

def test_space_victory_siege():
    """Verifies Space victory results in Siege, not Conquest."""
    
    # Setup Context
    context = MagicMock()
    context.game_config = {"combat": {"real_time_headless": False}}
    context.logger = MagicMock()
    context.update_planet_ownership = MagicMock() # Should NOT be called
    
    # Setup Managers
    bm = BattleManager(context)
    im = InvasionManager(context)
    bm.invasion_manager = im
    
    # Setup Planet and Battle
    planet = MockPlanet("Arrakis", "Defender")
    attacker = "Attacker"
    
    # Mock Battle Object
    battle = MagicMock()
    battle.state = MagicMock()
    battle.state.round_num = 10
    battle.start_time = 1000.0 # Float for time
    
    # Attacker has ONLY ships left (Space Victory)
    ship = MockUnit("Ship1", attacker, is_ship_val=True)
    battle.state.armies_dict = {
        attacker: [ship],
        "Defender": [] # Wiped out
    }
    
    # Mock time.time() is hard, but _finalize calculates duration = time.time() - start_time. 
    # Ideally we mock time.time but BattleManager imports it. 
    # Simpler fix: BattleManager logging line 728 does format string on float.
    # The error "unsupported format string passed to MagicMock.__format__" means `duration` became a Mock because `time.time()` wasn't mocked.
    # We must patch time.time OR just accept the crash is in logging and mock logic is sound.
    # Let's patch time.
    with unittest.mock.patch('src.managers.battle_manager.time.time', return_value=1200.0):
        # Execute Finalize
        bm._finalize_battle(battle, planet, attacker, 0)
    
    # Assertions
    assert planet.is_sieged == True, "Space victory should set is_sieged to True"
    assert planet.owner == "Defender", "Space victory should NOT change ownership"
    context.update_planet_ownership.assert_not_called()

def test_ground_victory_conquest():
    """Verifies Ground victory results in Conquest."""
    
    # Setup Context
    context = MagicMock()
    context.game_config = {"combat": {"real_time_headless": False}}
    context.update_planet_ownership = MagicMock() # SHOULD be called
    
    # Setup Managers
    bm = BattleManager(context)
    im = InvasionManager(context)
    bm.invasion_manager = im
    
    # Setup Planet
    planet = MockPlanet("Cadia", "Defender")
    attacker = "Attacker"
    
    # Mock Battle
    battle = MagicMock()
    battle.state = MagicMock()
    battle.start_time = 1000.0
    
    # Attacker has Troops (Ground Victory)
    troop = MockUnit("Troop1", attacker, is_ship_val=False)
    battle.state.armies_dict = {
        attacker: [troop],
        "Defender": []
    }
    
    # Execute Finalize with Time Patch
    with unittest.mock.patch('src.managers.battle_manager.time.time', return_value=1200.0):
        bm._finalize_battle(battle, planet, attacker, 0)
    
    # Assertions
    # Note: Mock context.update_planet_ownership handles the literal update in real code,
    # but InvasionManager.handle_conquest calls it.
    
    context.update_planet_ownership.assert_called_with(planet, attacker)
    # The MockPlanet owner won't change unless the mock function side-effect does it, 
    # but asking if the function was called is sufficient proof of intent.
    
if __name__ == "__main__":
    test_space_victory_siege()
    test_ground_victory_conquest()
    print("Invasion Logic Verified!")

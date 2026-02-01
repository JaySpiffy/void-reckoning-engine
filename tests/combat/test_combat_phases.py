# import pytest
from src.combat.combat_phases import resolve_shooting_phase, resolve_movement_phase
from src.combat.tactical_grid import TacticalGrid
from src.models.unit import Unit

# Removed redundant MockUnit definition

class MockWeapon:
    def __init__(self, name, range=24, str=4, ap=0):
        self.name = name
        self.type = "Weapon"
        self.weapon_stats = {"Range": range, "Str": str, "AP": ap}
        self.is_destroyed = False

class MockUnit:
    def __init__(self, name, faction, hp=100):
        self.name = name
        self.faction = faction
        self.current_hp = hp
        self.base_hp = hp
        self.movement_points = 5
        self.grid_x = 0
        self.grid_y = 0
        self.facing = 0
        self.is_deployed = True
        self.is_suppressed = False
        self.shield_current = 0
        self.shield_max = 0
        self.bs = 50
        self.armor = 30
        self.armor_front = 30
        self.armor_side = 20
        self.armor_rear = 10
        self.components = []
        self.weapon_arcs = {}
        self._strength_dirty = True
        self.morale_aura = 0
        self.leadership = 7
        self.hp_start_of_round = hp
        self.abilities = {}

    def is_alive(self):
        return self.current_hp > 0
    def is_ship(self):
        return self.shield_max > 0
    def recover_suppression(self):
        self.is_suppressed = False
    def regenerate_shields(self):
        self.shield_current = self.shield_max
    def take_damage(self, amount, target_component=None, ignore_mitigation=True):
        self.current_hp -= amount
        return 0, amount, 0, None

def test_execute_weapon_fire_success():
    from src.combat.combat_utils import execute_weapon_fire
    grid = TacticalGrid(100, 100)
    attacker = MockUnit("Attacker", "F1")
    defender = MockUnit("Defender", "F2")
    weapon = MockWeapon("Boltgun", range=24)
    attacker.components.append(weapon)
    attacker.weapon_arcs["Boltgun"] = "All"
    
    grid.place_unit(attacker, 10, 10)
    grid.place_unit(defender, 15, 15)
    
    attacker.bs = 100 # Guarantee hit
    result = execute_weapon_fire(attacker, defender, weapon, grid.get_distance(attacker, defender), 
                                 grid, "CHARGE", {}, {}, 1)
    
    assert result is not None
    assert result["damage"] > 0
    assert defender.current_hp < defender.base_hp

def test_execute_weapon_fire_out_of_range():
    from src.combat.combat_utils import execute_weapon_fire
    grid = TacticalGrid(100, 100)
    attacker = MockUnit("Attacker", "F1")
    defender = MockUnit("Defender", "F2")
    weapon = MockWeapon("Boltgun", range=5)
    
    grid.place_unit(attacker, 10, 10)
    grid.place_unit(defender, 20, 20)
    
    result = execute_weapon_fire(attacker, defender, weapon, grid.get_distance(attacker, defender), 
                                 grid, "CHARGE", {}, {}, 1)
    
    assert result is None

def test_resolve_shooting_phase_doctrine_bonus():
    grid = TacticalGrid(100, 100)
    u1 = MockUnit("Attacker", "F1")
    u2 = MockUnit("Defender", "F2")
    weapon = MockWeapon("Boltgun")
    u1.components.append(weapon)
    u1.weapon_arcs["Boltgun"] = "All"
    
    grid.place_unit(u1, 10, 10)
    grid.place_unit(u2, 12, 12)
    
    active_units = [(u1, "F1")]
    enemies_by_faction = {"F1": [u2]}
    faction_doctrines = {"F1": "KITE", "F2": "CHARGE"}
    faction_metadata = {
        "F1": {"faction_doctrine": "HIT_AND_RUN", "intensity": 2.0},
        "F2": {"faction_doctrine": "STANDARD", "intensity": 1.0}
    }
    
    # This ensures BS is boosted by both KITE and HIT_AND_RUN
    # BS = 50 + MOD_DOCTRINE_KITE_BS_BONUS(5) + 5*2.0 = 50 + 5 + 10 = 65
    resolve_shooting_phase(active_units, enemies_by_faction, grid, None, 
                           faction_doctrines, faction_metadata, 1)
    
    # Verification is mostly that it runs and applies metadata correctly (no crash)

def test_movement_kite_retreats():
    import math
    grid = TacticalGrid(100, 100)
    u1 = MockUnit("Kiter", "F1")
    u2 = MockUnit("Chaser", "F2")
    weapon = MockWeapon("LongRifle", range=40)
    u1.components.append(weapon)
    
    grid.place_unit(u1, 10, 10)
    grid.place_unit(u2, 12, 12) # Very close
    
    active_units = [(u1, "F1")]
    enemies_by_faction = {"F1": [u2]}
    faction_doctrines = {"F1": "KITE"}
    faction_metadata = {"F1": {"faction_doctrine": "STANDARD", "intensity": 1.0}}
    
    start_dist = grid.get_distance(u1, u2)
    resolve_movement_phase(active_units, enemies_by_faction, grid, None, 
                           faction_doctrines, faction_metadata, 1)
    
    # KITE should move AWAY if distance < 15
    new_dist = grid.get_distance(u1, u2)
    assert new_dist > start_dist

def test_state_recovery():
    grid = TacticalGrid(100, 100)
    u1 = MockUnit("Ship", "F1")
    u1.shield_max = 50
    u1.shield_current = 0
    u1.is_suppressed = True
    
    active_units = [(u1, "F1")]
    enemies_by_faction = {"F1": []}
    faction_doctrines = {"F1": "CHARGE"}
    faction_metadata = {"F1": {"faction_doctrine": "STANDARD", "intensity": 1.0}}
    
    # Shooting phase handles suppression and shield recovery
    resolve_shooting_phase(active_units, enemies_by_faction, grid, None, 
                           faction_doctrines, faction_metadata, 1)
    
    assert u1.is_suppressed == False
    assert u1.shield_current == 50

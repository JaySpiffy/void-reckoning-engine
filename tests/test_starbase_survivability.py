import pytest
import numpy as np
from src.combat.batch_shooting import resolve_shooting_batch
from src.models.unit import Unit, Component
from src.combat.tactical.gpu_tracker import GPUTracker
from src.core import gpu_utils

class MockUnit:
    def __init__(self, name, faction, grid_x, grid_y, abilities=None, md=0):
        self.name = name
        self.faction = faction
        self.grid_x = grid_x
        self.grid_y = grid_y
        self.abilities = abilities or {}
        self.md = md
        self.bs = 100 # High BS to ensure hits
        self.current_hp = 1000000
        self.is_destroyed = False
        self.components = []
        self.tags = (abilities.get("Tags", []) if abilities else []) or []

    def is_alive(self):
        return not self.is_destroyed

def test_fortress_reduction_in_batch():
    """Verify that the 50% Fortress reduction is applied correctly in vectorized combat."""
    
    # Attacker 1 -> Normal Target
    att1 = MockUnit("Attacker 1", "F1", 0, 0)
    wpn = Component("Laser", 100, "Weapon", weapon_stats={"Str": 10, "AP": 0, "D": 1, "Attacks": 1000, "Range": 100, "BS": 100})
    att1.components.append(wpn)
    tgt1 = MockUnit("Normal", "F2", 10, 10, md=0)
    
    # Attacker 2 -> Fortress Target
    att2 = MockUnit("Attacker 2", "F1", 0, 0)
    att2.components.append(wpn)
    tgt2 = MockUnit("Fortress", "F2", 10, 10, abilities={"Tags": ["Fortress"]}, md=0)
    
    attackers = [att1, att2]
    target_map = {id(att1): id(tgt1), id(att2): id(tgt2)}
    distance_map = {id(att1): 10.0, id(att2): 10.0}
    active_units_dict = {id(att1): att1, id(att2): att2, id(tgt1): tgt1, id(tgt2): tgt2}
    
    results = resolve_shooting_batch(attackers, target_map, distance_map, active_units_dict)
    
    res1 = next(r for r in results if r["target"] == tgt1)
    res2 = next(r for r in results if r["target"] == tgt2)
    
    dmg1 = res1["damage"]
    dmg2 = res2["damage"]
    
    # Fortress should be approximately 50% of Normal damage
    # (Damage is roughly hits * 100 * 0.5)
    ratio = dmg2 / dmg1 if dmg1 > 0 else 0
    assert 0.4 <= ratio <= 0.6 , f"Expected ~0.5 ratio, got {ratio} (dmg1={dmg1}, dmg2={dmg2})"

def test_evasion_in_batch():
    """Verify that Target MD reduces hits in vectorized combat."""
    att1 = MockUnit("Attacker 1", "F1", 0, 0)
    wpn = Component("Laser", 100, "Weapon", weapon_stats={"Str": 10, "AP": 0, "D": 1, "Attacks": 1000, "Range": 100, "BS": 100})
    att1.components.append(wpn)
    
    att2 = MockUnit("Attacker 2", "F1", 0, 0)
    att2.components.append(wpn)
    
    # Target 1: 0 MD
    tgt1 = MockUnit("Clumsy", "F2", 10, 10, md=0)
    # Target 2: 50 MD
    tgt2 = MockUnit("Evasive", "F2", 10, 10, md=50)
    
    attackers = [att1, att2]
    target_map = {id(att1): id(tgt1), id(att2): id(tgt2)}
    distance_map = {id(att1): 10.0, id(att2): 10.0}
    active_units_dict = {id(att1): att1, id(att2): att2, id(tgt1): tgt1, id(tgt2): tgt2}
    
    results = resolve_shooting_batch(attackers, target_map, distance_map, active_units_dict)
    
    res1 = next(r for r in results if r["target"] == tgt1)
    res2 = next(r for r in results if r["target"] == tgt2)
    
    hits1 = res1["hit_count"]
    hits2 = res2["hit_count"]
    
    # Evasive (MD 50) should have approximately 50% of Normal hits
    ratio = hits2 / hits1 if hits1 > 0 else 0
    assert 0.4 <= ratio <= 0.6, f"Expected ~0.5 ratio, got {ratio} (hits1={hits1}, hits2={hits2})"

def test_gpu_tracker_priority_weighting():
    """Verify that static units are de-prioritized in targeting."""
    tracker = GPUTracker()
    
    att = MockUnit("Attacker", "F1", 0, 0)
    # Mobile unit at dist 15
    mobile = MockUnit("Mobile", "F2", 15, 0)
    # Static unit (Starbase) at dist 10 (Closer but weighted)
    starbase = MockUnit("Starbase", "F2", 10, 0, abilities={"Tags": ["Starbase"]})
    
    units = [att, mobile, starbase]
    tracker.initialize(units)
    
    # Nearest enemy for Attacker
    results = tracker.compute_nearest_enemies()
    target_uid, dist = results[id(att)]
    
    assert target_uid == id(mobile)

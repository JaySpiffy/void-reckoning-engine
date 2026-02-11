
import unittest
from unittest.mock import MagicMock
import math

from src.ai.tactical_ai import TacticalAI

class MockUnit:
    def __init__(self, x, y, faction):
        self.grid_x = x
        self.grid_y = y
        self.faction = faction
        self.id = "u1"
        self.components = []
        self.name = "TestUnit"

class MockGrid:
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def get_unit_at(self, x, y):
        return None

class MockManager:
    def __init__(self):
        self.rounds_since_last_damage = 0

class TestStalemateBreaker(unittest.TestCase):
    def setUp(self):
        self.ai = TacticalAI()
        self.grid = MockGrid(20, 20)
        self.unit = MockUnit(10, 10, "FactionA")
        # Enemy at (18, 10) -> Dist 8.
        self.enemy = MockUnit(18, 10, "FactionB")
        self.enemies = [self.enemy]
        
        # Setup Weapon with Range 10
        weapon_comp = MagicMock()
        weapon_comp.type = "Weapon"
        weapon_comp.weapon_stats = {"Range": 10}
        self.unit.components = [weapon_comp]

    def test_kiting_behavior(self):
        """Verify normal Kiting behavior favors distance ~9-10"""
        manager = MockManager()
        manager.rounds_since_last_damage = 0
        context = {"doctrine": "KITE", "war_goal": "GUERRILLA", "manager": manager}
        
        # Test distinct moves
        # 1. Move Away (to 9, 10) -> Dist 9 (Perfect Kite)
        # 2. Move Closer (to 11, 10) -> Dist 7 (Too close)
        
        # We can't easily mock the internal score logic without exposing it, 
        # but we can observe the result of decide_movement.
        # But decide_movement iterates neighbors.
        # Let's fake neighbors
        
        move = self.ai.decide_movement(self.unit, self.grid, self.enemies, context)
        # Expect move AWAY from enemy (enemy at 18). Unit at 10.
        # Max Range 10. Optimal 9-11.
        # Current Dist 8. Too close (0.8 ratio).
        # Should move to 9 (Dist 9).
        
        # self.assertEqual(move, (-1, 0)) # Moved left, away from enemy
        # NOTE: score_position checks (nx, ny).
        # (9, 10) -> Dist 9. Ratio 0.9. Good? (0.95-1.1 is sweet spot).
        # (10, 10) -> Dist 8. Ratio 0.8.
        # (11, 10) -> Dist 7. Ratio 0.7.
        
        # Actually Dist 9 is Ratio 0.9. Logic:
        # if 0.95 <= ratio <= 1.1: +50
        # elif ratio < 0.95: -20.
        
        # Dist 9 is ratio 0.9. (-20)
        # Dist 8 is ratio 0.8. (-20)
        # Wait, Kiting logic penalizes getting closer than 95%.
        # So moving away (Dist 9) is better than moving closer (Dist 7).
        # But staying at Dist 8 is synonymous with current pos.
        
        # Let's verify it moves AWAY (-1, 0) to get to Dist 9, which is closer to 9.5 than 8.
        print(f"Normal Kiting Move: {move}")
        # It's hard to predict exact scores without running the full math, but (-1,0) increases distance.
        self.assertEqual(move, (-1, 0))

    def test_stalemate_breaker(self):
        """Verify Stalemate Breaker forces CHARGE"""
        manager = MockManager()
        manager.rounds_since_last_damage = 151 # TRIGGER (Updated from 101)
        context = {"doctrine": "KITE", "war_goal": "GUERRILLA", "manager": manager}
        
        move = self.ai.decide_movement(self.unit, self.grid, self.enemies, context)
        
        # Logic: 
        # val = 30.0 - dist_to_enemy.
        # We want to MINIMIZE distance to maximize score.
        # Move towards enemy (1, 0) -> Dist 7. Score 23.
        # Move away (-1, 0) -> Dist 9. Score 21.
        
        print(f"Stalemate Breaker Move: {move}")
        self.assertEqual(move, (1, 0)) # Moved RIGHT, TOWARDS enemy

if __name__ == '__main__':
    unittest.main()

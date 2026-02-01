import unittest
from src.combat.combat_state import CombatState
from src.models.unit import Unit
from src.models.fleet import Fleet

class MockUnit:
    def __init__(self, faction, hp=100):
        self.faction = faction
        self.max_hp = hp
        self.current_hp = hp
        self.is_routing = False
        self.is_destroyed = False
        self.name = f"Unit_{faction}"

    def is_alive(self):
        return not self.is_destroyed and self.current_hp > 0

class TestAttackerLoseArrival(unittest.TestCase):
    def setUp(self):
        self.armies_dict = {}
        self.faction_doctrines = {}
        self.faction_metadata = {}

    def test_defender_wins_stalemate_via_arrival_logic(self):
        # Setup: Faction A is Defender (Stationary), Faction B is Attacker (Arrived)
        # Faction B is STRONGER (more HP) to prove HP check is bypassed
        
        # Defenders (Faction A) - Weak
        units_a = [MockUnit("Faction_A", hp=100) for _ in range(5)] # Total 500
        self.armies_dict["Faction_A"] = units_a
        
        # Attackers (Faction B) - Strong
        units_b = [MockUnit("Faction_B", hp=100) for _ in range(50)] # Total 5000
        self.armies_dict["Faction_B"] = units_b
        
        # Calculate Defender Factions (Simulating BattleManager logic)
        # Fleet A arrived_this_turn = False
        # Fleet B arrived_this_turn = True
        defender_factions = {"Faction_A"}
        
        # Initialize State
        state = CombatState(
            self.armies_dict, 
            self.faction_doctrines, 
            self.faction_metadata, 
            defender_factions=defender_factions
        )
        
        # Simulate Stalemate (1001 rounds with no kills/damage)
        state.rounds_since_last_damage = 1001
        
        # Check Victory
        winner, survivors, is_finished = state.check_victory_conditions(force_result=True)
        
        # Assertions
        print(f"\n[TEST] Winner: {winner}")
        
        self.assertTrue(is_finished, "Battle should be finished on stalemate.")
        self.assertEqual(winner, "Faction_A", "Defender (Faction_A) should win despite being weaker.")
        
        # Check Retreats
        for u in units_b:
            self.assertTrue(u.is_routing, "Attacker units should be forced to retreat.")
            
        for u in units_a:
            self.assertFalse(u.is_routing, "Defender units should hold ground.")

    def test_sequential_arrival_order(self):
        # Setup: Faction A and Faction B arrive.
        # Logic V3: "The one moving (Aggressor) is the Attacker."
        
        # Scenario 1: Faction A moves into Faction B's hex
        # Faction B is Defender. Faction A is Attacker.
        # Stalemate -> Faction B (Defender) wins.
        
        units_a = [MockUnit("Faction_A", hp=100) for _ in range(50)] # Strong Attacker
        units_b = [MockUnit("Faction_B", hp=100) for _ in range(5)]  # Weak Defender
        
        self.armies_dict["Faction_A"] = units_a
        self.armies_dict["Faction_B"] = units_b
        
        # Faction A is moving, so they are Aggressor
        defender_factions = {"Faction_B"} # B is not A
        
        state = CombatState(
            self.armies_dict, 
            self.faction_doctrines, 
            self.faction_metadata, 
            defender_factions=defender_factions
        )
        
        state.rounds_since_last_damage = 1001
        winner, survivors, is_finished = state.check_victory_conditions(force_result=True)
        
        print(f"[TEST] Sequential (A attacks B) Winner: {winner}")
        self.assertEqual(winner, "Faction_B", "Defender (B) should win on time, despite being weaker.")

    def test_counter_attack_scenario(self):
        # Scenario 2: Faction B (Weak) counter-attacks Faction A (Strong)
        # Faction A is holding ground (Defender).
        # Faction B is moving (Attacker).
        # Stalemate -> Faction A (Defender) wins.
        
        units_a = [MockUnit("Faction_A", hp=100) for _ in range(50)] # Strong Defender
        units_b = [MockUnit("Faction_B", hp=100) for _ in range(5)]  # Weak Attacker
        
        self.armies_dict = {"Faction_A": units_a, "Faction_B": units_b}
        
        # Faction B is moving (Aggressor)
        defender_factions = {"Faction_A"} # A is not B
        
        state = CombatState(
            self.armies_dict, 
            self.faction_doctrines, 
            self.faction_metadata, 
            defender_factions=defender_factions
        )
        
        state.rounds_since_last_damage = 1001
        winner, survivors, is_finished = state.check_victory_conditions(force_result=True)
        
        print(f"[TEST] Counter-Attack (B attacks A) Winner: {winner}")
        self.assertEqual(winner, "Faction_A", "Defender (A) should win on time.")

if __name__ == '__main__':
    unittest.main()

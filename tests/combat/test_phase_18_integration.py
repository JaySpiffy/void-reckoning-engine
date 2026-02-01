import os
import json
import pytest
from src.managers.battle_manager import BattleManager, ActiveBattle
from src.models.fleet import Fleet
from src.models.unit import Ship, Regiment
from src.combat.tactical_engine import resolve_real_time_combat

class MockContext:
    def __init__(self):
        self.game_config = {"combat": {"real_time_headless": True}}
        self.logger = type('MockLogger', (), {'combat': lambda self, msg: print(msg)})()
        self.telemetry = type('MockTelemetry', (), {
            'log_event': lambda *args, **kwargs: None,
            'metrics': type('MockMetrics', (), {'record_battle_performance': lambda *args, **kwargs: None})()
        })()
        self.turn_counter = 1
        self.fleet_manager = MagicMock()
        
        self.log_battle_result = lambda *args, **kwargs: None
        
        # Mock Strategic AI
        class MockStrategicAI:
            def get_task_force_for_fleet(self, fleet):
                return type('MockTF', (), {'id': 'TF1', 'combat_doctrine': 'STANDARD', 'determine_combat_doctrine': lambda self: 'STANDARD'})()
        self.strategic_ai = MockStrategicAI()
        
        def get_faction(name):
             return type('MockFaction', (), {'evasion_rating': 0, 'intel_level': 0})()
        self.get_faction = get_faction
        
        self.fleets = []
        def get_all_fleets():
            return self.fleets
        self.get_all_fleets = get_all_fleets
        
        def get_all_planets():
            return []
        self.get_all_planets = get_all_planets

class MockLocation:
    def __init__(self, name, planet_class="Desert"):
        self.name = name
        self.planet_class = planet_class
        self.is_sieged = False

def test_full_real_time_integration():
    # 1. Setup
    ctx = MockContext()
    bm = BattleManager(ctx)
    loc = MockLocation("Arrakis", "Desert")
    
    # 2. Create Factions & Units
    f1_units = [Ship("Iron Vanguard Frigate", 50, 50, 100, 10, 20, {"Tags": ["Frigate"]}, faction="Iron Vanguard", domain="space", shield=50)]
    f1_units[0].authentic_weapons = ["Laser Battery"]
    
    f2_units = [Regiment("Solar Hegemony Cadre", 40, 40, 50, 5, 10, {}, faction="Solar Hegemony", domain="ground")]
    
    fleet1 = Fleet("F1", "Iron Vanguard", "Arrakis")
    fleet1.units = f1_units
    ctx.fleets.append(fleet1)
    
    # ArmyGroup is used in BattleManager
    class MockArmyGroup:
        def __init__(self, id, faction, units):
            self.id = id
            self.faction = faction
            self.units = units
            self.is_engaged = False
            self._fleet_id = None
            
    army1 = MockArmyGroup("A1", "Solar Hegemony", f2_units)
    
    # [FIX] Ensure RetreatHandler sees units as present
    fleet1.location = loc
    loc.armies = [army1]
    
    # 3. Initialize Battle
    bm._initialize_new_battle(loc, [fleet1], [army1], {"Iron Vanguard", "Solar Hegemony"})
    
    assert len(bm.active_battles) == 1
    battle = list(bm.active_battles.values())[0]
    battle.json_file = "test_battle_par.json"
    
    # [PHASE 18] Trigger Resolve
    print("Processing active battles (Triggering Real-Time Resolve)...")
    bm.process_active_battles()
    
    # 4. Verification
    assert battle.is_finished == True
    par_path = "test_battle_par.json"
    assert os.path.exists(par_path)
    
    with open(par_path, "r") as f:
        data = json.load(f)
        assert "par" in data
        assert "snapshots" in data
        assert len(data["snapshots"]) > 0
        print(f"Verified PAR generation: Winner = {data['par']['meta']['winner']}")
        print(f"Duration: {data['par']['meta']['duration']}s")
        print(f"Snapshots captured: {len(data['snapshots'])}")

if __name__ == "__main__":
    try:
        test_full_real_time_integration()
        print("\nSUCCESS: Phase 18 Implementation Verified.")
    except Exception as e:
        print(f"\nFAILED: Phase 18 Verification failed: {e}")
        import traceback
        traceback.print_exc()

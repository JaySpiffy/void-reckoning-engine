
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.fleet import Fleet
from src.models.planet import Planet
from src.core.universe_data import UniverseDataManager

# Mock Unit with Upkeep
class MockUnit:
    def __init__(self, uid, upkeep):
        self.id = uid
        self.upkeep = upkeep
        self.fleet = None
        self.name = f"Mock_{uid}"
        self.ma = 0
    
    def set_fleet(self, f): self.fleet = f
    def is_ship(self): return True # Mock as Ship
    def is_alive(self): return True

def verify_caching():
    print("Verifying Economy Caching...")
    
    # 1. Fleet Upkeep Caching
    print("  1. Checking Fleet Upkeep Cache...")
    f = Fleet("TestFleet", "Imps", None)
    
    u1 = MockUnit("u1", 10)
    u2 = MockUnit("u2", 20)
    
    # Bypassing complex add_unit to test cache mechanism directly
    f.units.append(u1)
    u1.set_fleet(f)
    f.update_upkeep_cache()
    
    # Check if cache updated
    assert f.upkeep == 10, f"Expected 10, got {f.upkeep}"
    
    f.units.append(u2)
    u2.set_fleet(f)
    f.update_upkeep_cache()
    
    assert f.upkeep == 30, f"Expected 30, got {f.upkeep}"
    
    print("    - Fleet Upkeep Cache: PASS")
    
    # 2. Planet Output Caching
    print("  2. Checking Planet Output Cache...")
    
    # Mock UniverseData building db
    MOCK_DB = {
        "Mine": {"income_req": 100, "maintenance": 10},
        "Lab": {"income_req": 0, "maintenance": 20, "research_output": 50}
    }
    
    # Patch UniverseDataManager
    orig_get_db = UniverseDataManager.get_building_database
    orig_get_classes = UniverseDataManager.get_planet_classes
    
    UniverseDataManager.get_building_database = lambda self: MOCK_DB
    UniverseDataManager.get_planet_classes = lambda self: {
        "Terran": {"req_mod": 1.0, "def_mod": 1.0, "slots": 10}
    }
    
    try:
        p = Planet("TestPlanet", None, 1, base_req=500)
        p.income_req = 500 # Ensure recalc didn't overwrite with modifier
        
        # Initial State
        res = p.generate_resources()
        assert res["req"] == 500, f"Expected Base 500, got {res['req']}"
        
        # Add Building (Simulate Construction)
        print("    - Adding Mine (100 req)...")
        p.buildings.append("Mine")
        p.update_economy_cache() # Manually trigger (usually called by construction service)
        
        res = p.generate_resources()
        assert res["req"] == 600, f"Expected 600 (500+100), got {res['req']}"
        assert res["infrastructure_upkeep"] == 10, f"Expected 10 upkeep, got {res['infrastructure_upkeep']}"
        
        # Add Research Lab
        print("    - Adding Lab (50 research)...")
        p.buildings.append("Lab")
        p.update_economy_cache()
        
        res = p.generate_resources()
        assert res["research"] == 50, f"Expected 50 research, got {res['research']}"
        assert res["infrastructure_upkeep"] == 30, f"Expected 30 upkeep, got {res['infrastructure_upkeep']}"
        
        print("    - Planet Output Cache: PASS")
        
    finally:
        # Restore
        UniverseDataManager.get_building_database = orig_get_db
        UniverseDataManager.get_planet_classes = orig_get_classes

    print("Economy Caching Verification: PASS")

if __name__ == "__main__":
    verify_caching()

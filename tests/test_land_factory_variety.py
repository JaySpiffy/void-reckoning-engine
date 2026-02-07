
import pytest
import os
import json
from src.factories.land_factory import LandDesignFactory

@pytest.fixture
def factory_data():
    base_dir = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\base"
    
    chassis_path = os.path.join(base_dir, "units", "base_land_chassis.json")
    modules_path = os.path.join(base_dir, "modules", "base_land_modules.json")
    equipment_path = os.path.join(base_dir, "weapons", "base_land_equipment.json")
    
    with open(chassis_path, 'r') as f:
        chassis = json.load(f)
    with open(modules_path, 'r') as f:
        modules = json.load(f)
    with open(equipment_path, 'r') as f:
        equipment = json.load(f)
        
    return chassis, modules, equipment

def test_land_factory_variety(factory_data):
    chassis, modules, equipment = factory_data
    factory = LandDesignFactory(chassis, modules, equipment)
    
    # Mock arsenal (ship weapons to be scaled)
    mock_arsenal = {
        "plasma_cannon": {
            "name": "Plasma Cannon",
            "stats": {"power": 100, "range": 1000}
        },
        "laser_battery": {
            "name": "Laser Battery",
            "stats": {"power": 50, "range": 2000}
        }
    }
    
    faction_traits = ["Aggressive", "Militarist"]
    roster = factory.design_roster("Terran Hegemony", faction_traits, mock_arsenal)
    
    # 1. Verify we have 20 unique chassis keys being processed
    assert len(chassis) == 20
    
    # 2. Verify roster contains multiple variants (Standard, Elite, etc.)
    # Roster size should be at least len(chassis)
    assert len(roster) >= 20
    
    # 3. Verify specific new classes are present in the design output
    found_recon = any("recon_scout_drone" in d["blueprint_id"] for d in roster)
    found_hover_tank = any("hover_tank_chassis" in d["blueprint_id"] for d in roster)
    found_psi = any("psi_weaver_acolyte" in d["blueprint_id"] for d in roster)
    
    assert found_recon, "Recon Scout Drone design missing from roster"
    assert found_hover_tank, "Hover Tank Chassis design missing from roster"
    assert found_psi, "Psi-Weaver Acolyte design missing from roster"
    
    # 5. Verify Style logic: Transcendent Order should have "Energy" style
    energy_roster = factory.design_roster("Transcendent Order", [], mock_arsenal)
    for unit in energy_roster:
        assert unit["style"] == "Energy"
        # Check that energy weapons are prioritized if available
        # (Bolters are kinetic/explosive, Lasguns are energy)
        comps = [c["component"] for c in unit["components"]]
        if "standard_infantry" in unit["type"]:
            assert "lasgun" in comps or "pulse_rifle" in comps or "blaster_rifle" in comps
            assert "bolter" not in comps
    
    # 4. Check Scaling Logic (ensure micro-scaled weapons are applied)
    # Check Recon Drone (it should have a micro scale weapon or utility)
    recon_design = next(d for d in roster if "recon_scout_drone" in d["blueprint_id"])
    assert len(recon_design["components"]) > 0
    
    print(f"Successfully generated {len(roster)} land unit designs across 20 chassis types.")

if __name__ == "__main__":
    # For manual execution
    chassis_p = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\base\units\base_land_chassis.json"
    modules_p = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\base\modules\base_land_modules.json"
    equipment_p = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\universes\base\weapons\base_land_equipment.json"
    
    with open(chassis_p, 'r') as f: c = json.load(f)
    with open(modules_p, 'r') as f: m = json.load(f)
    with open(equipment_p, 'r') as f: e = json.load(f)
    
    test_land_factory_variety((c, m, e))

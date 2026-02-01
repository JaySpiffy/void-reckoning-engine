import sys
import os

# Include src in path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.unit import Unit, Ship, Regiment
from src.builders.unit_builder import UnitBuilder
from src.factories.unit_factory import UnitFactory
from src.combat.components.health_component import HealthComponent

def test_unit_creation_manual_legacy():
    print("Testing Manual Legacy Unit Creation...")
    u = Unit("TestMarine", "Imperium", hp=100, ma=40, md=40, armor=30)
    assert u.name == "TestMarine"
    assert u.faction == "Imperium"
    assert u.health_comp is not None
    assert u.health_comp.max_hp == 100
    assert u.armor_comp is not None
    assert u.armor_comp.base_armor == 30
    assert u.stats_comp is not None
    assert u.base_ma == 40
    print("Legacy Creation: OK")

def test_unit_builder():
    print("Testing UnitBuilder...")
    u = (UnitBuilder("Space Marine", "Imperium")
         .with_health(120)
         .with_armor(50)
         .with_stats_comp(ma=60)
         .build())
    assert u.name == "Space Marine"
    assert u.current_hp == 120
    assert u.base_armor == 50
    assert u.base_ma == 60
    print("UnitBuilder: OK")

def test_unit_factory():
    print("Testing UnitFactory.create_pdf...")
    pdf = UnitFactory.create_pdf("Regular", "Imperium")
    assert pdf.name == "PDF Regular"
    assert pdf.health_comp.max_hp == 40
    assert pdf.armor_comp.base_armor == 15
    print("UnitFactory (PDF): OK")

def test_ship_subclass():
    print("Testing Ship Subclass...")
    s = Ship("Naval Vessel", "Imperium", hp=1000)
    assert s.is_ship() == True
    assert s.domain == "space"
    assert s.unit_class == "ship"
    print("Ship Subclass: OK")

def test_proxies_and_setters():
    print("Testing Proxies...")
    u = Unit("ProxyTest", "Chaos", hp=100)
    u.current_hp = 50
    assert u.health_comp.current_hp == 50
    
    u.base_hp = 200
    assert u.health_comp.max_hp == 200
    assert u.stats_comp.base_hp == 200
    print("Proxies: OK")

if __name__ == "__main__":
    try:
        test_unit_creation_manual_legacy()
        test_unit_builder()
        test_unit_factory()
        test_ship_subclass()
        test_proxies_and_setters()
        print("\nAll Refactored Unit Tests PASSED.")
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

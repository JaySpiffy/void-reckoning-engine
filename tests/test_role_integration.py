import pytest
from src.models.unit import Unit, Component, Regiment
from src.combat.tactical_engine import select_target_by_doctrine, TacticalGrid

def test_unit_auto_role_assignment():
    """Verify that a newly created Unit automatically gets tactical_roles."""
    
    # Create Unit with Anti-Tank Weapon
    # Lascannon: S9, AP-3
    stats = {"S": 9, "AP": -3, "D": 3.5, "Range": 48, "Type": "Heavy 1"}
    
    u = Regiment("Devastator", 40, 40, 20, 10, 5, {}, faction="Imperium")
    # Manually add component (normally parser does this, or subclass)
    c = Component("Lascannon", 10, "Weapon", weapon_stats=stats)
    u.components.append(c)
    
    # Trigger Update (recalc_stats calls update_tactical_roles)
    u.recalc_stats()
    
    print(f"Roles: {u.tactical_roles}")
    assert "Anti-Tank" in u.tactical_roles
    assert u.power_rating > 0

def test_targeting_priority_integration():
    """Verify TacticalEngine prioritizes based on assigned roles."""
    grid = TacticalGrid(100, 100)
    
    # Attacker: Anti-Tank
    attacker = Regiment("Hunter", 40, 40, 20, 10, 5, {}, faction="Imperium")
    c = Component("Lascannon", 10, "Weapon", weapon_stats={"S": 9, "AP": -3})
    attacker.components.append(c)
    attacker.recalc_stats() # Assign roles
    
    # Target 1: Infantry (Closer, Distance 10)
    infantry = Regiment("Guard", 30, 30, 10, 5, 3, {"Tags": ["Infantry"]}, faction="Traitor")
    infantry.grid_x, infantry.grid_y = 10, 10
    grid.place_unit(infantry, 10, 10)
    
    # Target 2: Tank (Further, Distance 20)
    tank = Regiment("Leman Russ", 30, 30, 100, 20, 5, {"Tags": ["Vehicle"]}, faction="Traitor")
    # Make sure toughness matches vehicle logic if tags fail (T7)
    tank.toughness = 8 
    tank.grid_x, tank.grid_y = 20, 20
    grid.place_unit(tank, 20, 20)
    
    attacker.grid_x, attacker.grid_y = 0, 0
    grid.place_unit(attacker, 0, 0)
    
    # Standard Logic: Closest (Infantry)
    # Role Logic: Anti-Tank prefers Tank (-15 score modifier vs +10 distance diff?)
    # Dist Infantry: 14.1
    # Dist Tank: 28.2
    # Score Infantry: 14.1
    # Score Tank: 28.2 - 15 = 13.2
    # Tank (13.2) < Infantry (14.1) -> Tank should be picked!
    
    target = select_target_by_doctrine(attacker, [infantry, tank], "ranged", grid)
    
    assert target.name == "Leman Russ"
    print(f"Selected Target: {target.name}")

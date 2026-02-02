import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.ship_design_service import ShipDesignService
from src.services.recruitment_service import RecruitmentService
from src.models.unit import Ship
from src.models.starbase import Starbase
from src.models.faction import Faction
from src.combat.tactical_grid import TacticalGrid
from src.combat.combat_phases import ShootingPhase
from unittest.mock import MagicMock

def test_ship_variety():
    print("\n--- Testing Ship Variety ---")
    ai_mock = MagicMock()
    ai_mock.engine.factions = {"TestFaction": Faction("TestFaction")}
    ai_mock.turn_cache = {}
    
    designer = ShipDesignService(ai_mock)
    
    classes = [
        "Corvette", "Frigate", "Destroyer", "Cruiser", "Carrier", "Battleship", "Titan",
        "World Devastator", "Reality Breaker", "Thought Weaver", "Solar-Anchor", "Mothership"
    ]
    for cls in classes:
        design = designer.generate_design("TestFaction", cls, "General")
        hp = design['stats'].get('hp', 0)
        armor = design['stats'].get('armor', 0)
        weapons = [c for c in design['components'] if c['type'] == 'Weapon']
        defenses = [c for c in design['components'] if c['type'] == 'Defense']
        hangars = [c for c in design['components'] if c['type'] == 'Hangar']
        
        print(f"Class: {cls:16} | Slots: {len(design['components']):2} | W:{len(weapons):2} D:{len(defenses):2} H:{len(hangars):2} | HP: {hp:6} | Armor: {armor:3}")

def test_multi_targeting():
    print("\n--- Testing Multi-Targeting ---")
    
    # 1. Setup Massive Attacker (Titan)
    attacker = Ship(
        name="Judgement of Terra",
        ma=10, md=5, hp=5000, armor=25,
        damage=0, abilities={"Tags": ["Ship", "Titan", "Massive"]},
        faction="Empire",
        cost=10000, shield=2000,
        unit_class="Titan"
    )
    attacker.tactical_roles = ["Titan-Killer"] 
    attacker.bs = 100
    attacker.weapon_arcs = {"Heavy Lance": "Omni", "Plasma Battery": "Omni", "P-Defense Left": "Omni", "P-Defense Right": "Omni"}
    
    from src.models.unit import Component
    attacker.components = [
        Component("Heavy Lance", 100, "Weapon", weapon_stats={"Range": 100, "S": 10, "AP": 4, "D": 10}),
        Component("Plasma Battery", 50, "Weapon", weapon_stats={"Range": 30, "S": 8, "AP": 3, "D": 5}),
        Component("P-Defense Left", 30, "Weapon", weapon_stats={"Range": 15, "S": 6, "AP": 1, "D": 3}),
        Component("P-Defense Right", 30, "Weapon", weapon_stats={"Range": 15, "S": 6, "AP": 1, "D": 3})
    ]
    from src.combat.components.trait_component import TraitComponent
    attacker.add_component(TraitComponent([], abilities={"Tags": ["Ship", "Titan", "Massive"]}))
    attacker.grid_x, attacker.grid_y = 50, 50
    attacker.is_alive = lambda: True
    attacker.recover_suppression = lambda: None
    attacker.regenerate_shields = lambda: None

    from src.combat.components.trait_component import TraitComponent
    
    # 2. Setup Targets
    # A Titan far away (Dist 40). Score = 40 - 50 = -10.
    target1 = Ship(name="Enemy Titan", faction="Rebels", hp=100, armor=10, ma=30, md=30, cost=100, shield=0)
    target1.add_component(TraitComponent([], abilities={"Tags": ["Ship", "Titan"]}))
    target1.grid_x, target1.grid_y = 50, 90 
    
    # An Escort close (Dist 15). Score = 15.
    target2 = Ship(name="Near Escort A", faction="Rebels", hp=100, armor=10, ma=30, md=30, cost=100, shield=0)
    target2.add_component(TraitComponent([], abilities={"Tags": ["Ship", "Escort"]}))
    target2.grid_x, target2.grid_y = 50, 65 

    enemies = [target1, target2]
    for e in enemies: e.is_alive = lambda: True
    # Ensure they have positions for TargetSelector
    target1.grid_x, target1.grid_y = 50, 90
    target2.grid_x, target2.grid_y = 50, 65
    
    # 3. Setup Combat Context
    grid = TacticalGrid(100, 100)
    if not grid.place_unit(attacker, 50, 50): print("Error placing attacker")
    if not grid.place_unit(target1, 50, 90): print("Error placing target1")
    if not grid.place_unit(target2, 50, 65): print("Error placing target2")
    
    context = {
        "active_units": [(attacker, "Empire")],
        "enemies_by_faction": {"Empire": enemies},
        "grid": grid,
        "faction_doctrines": {"Empire": "STANDARD"},
        "faction_metadata": {},
        "round_num": 1,
        "manager": MagicMock()
    }
    context["manager"].battle_stats = {}
    
    phase = ShootingPhase()
    log_file = "multi_target_test.log"
    if os.path.exists(log_file): os.remove(log_file)
    context["detailed_log_file"] = log_file
    
    print("Executing Shooting Phase...")
    phase.execute(context)
    
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            print("Combat Logs:")
            targets_hit = set()
            for line in lines:
                print(f"  {line.strip()}")
                if " fires " in line and " at " in line:
                    # Find the last ' at ' to avoid splitting on names like 'Battery'
                    parts = line.split(" at ")
                    if len(parts) >= 2:
                        target_info = parts[-1] # The part after the last ' at '
                        target_name = target_info.split("(")[0].strip()
                        targets_hit.add(target_name)
            
            print(f"Unique targets hit: {targets_hit}")
            if len(targets_hit) >= 2:
                print("  [SUCCESS] Titan engaged multiple targets!")
            else:
                print("  [FAILURE] Titan only engaged one target.")
    else:
        print("  [ERROR] No log file generated.")

if __name__ == "__main__":
    test_ship_variety()
    test_multi_targeting()

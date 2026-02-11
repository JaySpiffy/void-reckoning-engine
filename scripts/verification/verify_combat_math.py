import sys
import os
sys.path.append(os.getcwd())

from src.combat.rust_tactical_engine import RustTacticalEngine

class MockUnit:
    def __init__(self, name, faction, hp=100.0, damage=10.0):
        self.name = name
        self.faction = faction
        self.max_hp = hp
        self.current_hp = hp
        self.damage = damage
        self.weapon_comps = []
        self.health_comp = self
        self.is_destroyed = False
        
    def add_weapon(self, name, damage, cooldown):
        w = type('obj', (object,), {
            "name": name, 
            "weapon_stats": {"damage": damage, "cooldown": cooldown, "type": "Kinetic"}
        })
        self.weapon_comps.append(w)

print("Starting Combat Verification...")

engine = RustTacticalEngine()
if not engine.rust_engine:
    print("FAILED: Rust engine not loaded.")
    sys.exit(1)

# Create Units
u1 = MockUnit("Attacker", "Empire", hp=100.0)
u1.add_weapon("Laser", 20.0, 1.0)

u2 = MockUnit("Defender", "Rebels", hp=100.0)
u2.add_weapon("Blaster", 15.0, 1.0)

armies = {
    "Empire": [u1],
    "Rebels": [u2]
}

print("Initializing Battle...")
engine.initialize_battle(armies)

print("Running Simulation...")
for i in range(5):
    cont = engine.resolve_round()
    state = engine.get_state()
    # Sync back to check python objects
    engine.sync_back_to_python(armies)
    
    print(f"Round {i+1}: Attacker HP={u1.current_hp}, Defender HP={u2.current_hp}")
    
    if not cont:
        print("Battle ended early.")
        break

if u1.current_hp < 100.0 and u2.current_hp < 100.0:
    print("SUCCESS: Damage exchanged.")
else:
    print("FAILURE: No damage exchanged.")

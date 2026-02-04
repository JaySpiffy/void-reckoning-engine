import json
import random
import os

class ComponentGenerator:
    def __init__(self, target_count=1200):
        self.target_count = target_count
        self.output_path = os.path.join("data", "ships", "procedural_components.json")
        
        self.themes = {
            "Federation": {
                "prefixes": ["Phased", "Precise", "Harmonic", "Diplomatic", "Standard"],
                "weapons": ["Phaser", "Photon Torpedo", "Quantum Array"],
                "defenses": ["Multiphase Shield", "Regenerative Plating"],
                "bias": {"accuracy": 1.2, "shield": 1.3, "damage": 0.8},
                "flavor": "Star Trek"
            },
            "Imperium": {
                "prefixes": ["Holy", "Venerable", "Gothic", "Relic", "Exterminatus"],
                "weapons": ["Macro Cannon", "Lance Battery", "Melta-Beam"],
                "defenses": ["Adamantine Plate", "Void Shield"],
                "bias": {"damage": 1.4, "armor": 1.5, "accuracy": 0.7, "cost": 1.2},
                "flavor": "Warhammer 40k"
            },
            "Covenant": {
                "prefixes": ["Sacred", "Sublime", "Prophetic", "Glassing", "Blessed"],
                "weapons": ["Plasma Mortar", "Needler Bank", "Energy Projector"],
                "defenses": ["Energy Shielding", "Covenant Lattice"],
                "bias": {"shield_strip": 1.5, "speed": 1.1, "hp": 0.9},
                "flavor": "Halo"
            },
            "UNSC": {
                "prefixes": ["Hardened", "Tactical", "Orbital", "Ballistic", "Prototype"],
                "weapons": ["MAC Cannon", "Railgun", "Archer Missile"],
                "defenses": ["Titanium-A Plate", "Reactive Armor"],
                "bias": {"range": 1.4, "damage": 1.1, "shield": 0.5},
                "flavor": "Halo"
            },
            "Borg": {
                "prefixes": ["Adaptive", "Assimilated", "Collective", "Transwarp", "Hive"],
                "weapons": ["Cutting Beam", "Magnetometric Torpedo"],
                "defenses": ["Adaptive Shielding", "Self-Repairing Hull"],
                "bias": {"hp": 1.6, "power_efficiency": 1.4, "speed": 0.5},
                "flavor": "Star Trek"
            }
        }
        
        self.slot_types = ["S", "M", "L", "X", "P", "G", "T", "I"]
        self.tiers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
    def generate(self):
        components = []
        count_per_theme = self.target_count // len(self.themes)
        
        for theme_name, data in self.themes.items():
            for _ in range(count_per_theme):
                comp_type = random.choice(["weapon", "defense", "utility", "engine"])
                tier = random.choice(self.tiers)
                slot = random.choice(self.slot_types)
                
                if comp_type == "weapon":
                    comp = self._generate_weapon(theme_name, data, tier, slot)
                elif comp_type == "defense":
                    comp = self._generate_defense(theme_name, data, tier, slot)
                elif comp_type == "utility":
                    comp = self._generate_utility(theme_name, data, tier, slot)
                else:
                    comp = self._generate_engine(theme_name, data, tier, slot)
                
                components.append(comp)
        
        # Save to file
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        with open(self.output_path, 'w') as f:
            json.dump({"components": components}, f, indent=4)
            
        print(f"Successfully generated {len(components)} components at {self.output_path}")

    def _generate_weapon(self, theme, data, tier, slot):
        prefix = random.choice(data["prefixes"])
        base_name = random.choice(data["weapons"])
        name = f"{prefix} {base_name} Type-{tier} ({slot})"
        
        # Base stats scaled by tier
        base_damage = 5 * tier
        base_range = 30 + (10 * tier)
        base_accuracy = 0.8
        
        # Apply theme biases
        bias = data.get("bias", {})
        damage = base_damage * bias.get("damage", 1.0)
        rng = base_range * bias.get("range", 1.0)
        acc = min(0.95, base_accuracy * bias.get("accuracy", 1.0))
        
        # Slot scaling
        slot_mult = {"S": 1, "M": 2.5, "L": 6, "X": 15, "P": 0.5, "G": 4, "T": 0, "I": 0}
        mult = slot_mult.get(slot, 1)
        
        return {
            "id": f"proc_{theme.lower()}_{name.replace(' ', '_').lower()}",
            "name": name,
            "theme": theme,
            "flavor": data["flavor"],
            "slot_type": slot,
            "tech_level": tier,
            "cost": int((20 * tier * mult) * bias.get("cost", 1.0)),
            "power": -int(10 * tier * mult),
            "stats": {
                "damage": round(damage * mult, 1),
                "range": round(rng * (mult**0.5), 1),
                "accuracy": round(acc, 2)
            }
        }

    def _generate_defense(self, theme, data, tier, slot):
        prefix = random.choice(data["prefixes"])
        base_name = random.choice(data["defenses"])
        name = f"{prefix} {base_name} Mark-{tier}"
        
        bias = data.get("bias", {})
        hp = (50 * tier) * bias.get("hp", 1.0)
        armor = (5 * tier) * bias.get("armor", 1.0)
        shield = (40 * tier) * bias.get("shield", 1.0)
        
        return {
            "id": f"proc_{theme.lower()}_{name.replace(' ', '_').lower()}",
            "name": name,
            "theme": theme,
            "flavor": data["flavor"],
            "slot_type": "A", # Defense usually goes in Aux/Armor slots
            "tech_level": tier,
            "cost": int(30 * tier),
            "power": -int(5 * tier) if shield > 0 else 0,
            "stats": {
                "hp": round(hp, 1),
                "armor": round(armor, 1),
                "shield": round(shield, 1)
            }
        }

    def _generate_utility(self, theme, data, tier, slot):
        name = f"{theme} {random.choice(['Sensor Array', 'Processor Core', 'Capacitor'])} T-{tier}"
        return {
            "id": f"proc_{theme.lower()}_{name.replace(' ', '_').lower()}",
            "name": name,
            "theme": theme,
            "slot_type": "T",
            "tech_level": tier,
            "cost": 100 * tier,
            "power": 50 * tier, # Generators provide power
            "stats": {"utility": "power_gen"}
        }

    def _generate_engine(self, theme, data, tier, slot):
        name = f"{theme} {random.choice(['Warp Drive', 'Ion Engine', 'Reaction Drive'])} V-{tier}"
        bias = data.get("bias", {})
        speed = (10 * tier) * bias.get("speed", 1.0)
        
        return {
            "id": f"proc_{theme.lower()}_{name.replace(' ', '_').lower()}",
            "name": name,
            "theme": theme,
            "slot_type": "THRUSTER",
            "tech_level": tier,
            "cost": 50 * tier,
            "power": -20 * tier,
            "stats": {
                "speed": round(speed, 1),
                "evasion": round(0.01 * tier, 3)
            }
        }

if __name__ == "__main__":
    gen = ComponentGenerator()
    gen.generate()

import sys
import os
import random
sys.path.append(os.getcwd())

from src.managers.campaign_manager import CampaignEngine
from src.models.faction import Faction
from src.models.unit import Unit
from src.mechanics.faction_mechanics_engine import FactionMechanicsEngine

def test_mechanics():
    print(">>> INITIALIZING MECHANICS ENGINE TEST <<<")
    
    # 1. Setup Mock Engine
    engine = CampaignEngine(universe_name="warhammer40k")
    # Force load checks
    engine.mechanics_engine = FactionMechanicsEngine(engine, "warhammer40k")
    
    # 2. Setup Mock Faction (Zealot Legions -> Conviction)
    f_name = "Imperium"
    faction = Faction(f_name)
    faction.conviction_stacks = 10
    engine.factions[f_name] = faction
    
    # Manually register mechanic for test if not loaded from file
    # But we want to test the loader too.
    # Assuming "Mech_Crusade" is in registry.
    
    print(f"Initial Conviction: {faction.conviction_stacks}")
    
    # 3. Test on_turn_start (Should decay conviction)
    print("\n--- Testing on_turn_start (Decay) ---")
    context = {"faction": faction, "engine": engine, "turn": 1}
    engine.mechanics_engine.apply_mechanics(f_name, "on_turn_start", context)
    print(f"Post-Turn Start Conviction: {faction.conviction_stacks}")
    
    if faction.conviction_stacks < 10:
        print("[PASS] Conviction decayed.")
    else:
        print("[FAIL] Conviction did not decay (Ensure 'Mech_Crusade' is active for Imperium).")

    # 4. Test on_unit_death (Should gain conviction)
    print("\n--- Testing on_unit_death (Gain) ---")
    killer = Faction("Imperium") # Killer is same faction? No, normally killer is self for glory? 
    # Wait, Conviction says "killer and killer.faction == faction.name".
    # So if I kill someone, I get stacks.
    
    # Fix Unit calls: name, ma, md, hp, armor, damage, abilities
    context_death = {
        "killer": "Imperium", # Test STRING killer (Comment 3 fix)
        "faction": faction, # The one who owns the mechanic
        "unit": Unit("TestEnemy", 40, 40, 100, 10, 10, {}), 
        "battle_state": None
    }
    
    engine.mechanics_engine.apply_mechanics(f_name, "on_unit_death", context_death)
    print(f"Post-Kill Conviction (String Killer): {faction.conviction_stacks}")
    
    if faction.conviction_stacks > 5: 
        print("[PASS] Conviction gained via String Killer.")
    else:
        print("[FAIL] Conviction not gained via String Killer.")

    # 5. Test Biomass (Tyranids)
    print("\n--- Testing Biomass (Hive Swarm) ---")
    t_name = "Tyranids"
    tyranids = Faction(t_name)
    tyranids.biomass_pool = 0
    engine.factions[t_name] = tyranids
    
    class MockPlanet:
        def __init__(self):
            self.owner = "Tyranids"
            self.name = "Prey World"

    u_dead = Unit("SpaceMarine", 40, 40, 100, 10, 10, {})
    u_dead.cost = 1000
    
    context_bio = {
        "unit": u_dead,
        "faction": tyranids,
        "location": MockPlanet()
    }
    engine.mechanics_engine.apply_mechanics(t_name, "on_unit_death", context_bio)
    print(f"Biomass Pool: {tyranids.biomass_pool}")
    
    if tyranids.biomass_pool > 0:
        print(f"[PASS] Biomass gained: {tyranids.biomass_pool}")
    else:
        print("[FAIL] No biomass gained.")

    # 6. Test Ability Use (Aether Overload)
    print("\n--- Testing Ability Use Hook ---")
    # Manually register Aether mechanic to a dummy faction
    from src.mechanics.combat_mechanics import AetherOverloadMechanic
    
    a_name = "Ascended_Order"
    ascended = Faction(a_name)
    ascended.name = a_name
    engine.factions[a_name] = ascended
    
    # Mock registry injection
    mech_aether = AetherOverloadMechanic("Mech_Aether", {})
    engine.mechanics_engine.active_mechanics[a_name] = [mech_aether]
    
    caster = Unit("Sorcerer", 50, 50, 100, 0, 10, {})
    caster.elemental_dna = {"atom_volatility": 0, "atom_stability": 0} # 0 Stability = 100% fail chance if Aether >= 20
    caster.current_hp = 100
    
    ability = {
        "elemental_dna": {"atom_aether": 50}, # High aether
        "payload": {"damage": 20}
    }
    
    context_ability = {
        "caster": caster,
        "ability": ability,
        "target": u_dead,
        "faction": ascended
    }
    
    engine.mechanics_engine.apply_mechanics(a_name, "on_ability_use", context_ability)
    
    print(f"Caster HP after overload check: {caster.current_hp}")
    if caster.current_hp < 100:
        print("[PASS] Ability hook triggered (Overload damage applied).")
    else:
        print("[FAIL] Ability hook not triggered (No overload damage).")

if __name__ == "__main__":
    test_mechanics()

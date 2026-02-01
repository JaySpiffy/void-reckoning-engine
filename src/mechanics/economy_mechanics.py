from src.mechanics.base_mechanic import BaseMechanic
import random

class RaidMechanic(BaseMechanic):
    """
    Nebula Drifters: Raid
    Bonus income from fighting on enemy planets.
    """
    def on_battle_end(self, context):
        faction = context.get("faction")
        planet = context.get("planet")
        winner = context.get("winner")
        
        if planet and planet.owner != faction.name:
            # We fought on enemy soil. Did we win? Or just raid?
            # Even losing might grant raid income if we destroyed stuff.
            # Let's give income based on planet value.
            # Let's give income based on planet value * loot bonus
            loot_mult = 1.0 + self.get_modifier("loot_bonus", 0.0)
            income = planet.base_income_req * 0.5 * loot_mult
            faction.add_income(income)
            
            stats = getattr(faction, "stats", {})
            stats["raid_income_this_turn"] = stats.get("raid_income_this_turn", 0) + income
            faction.stats = stats

    def on_economy_phase(self, context):
        faction = context.get("faction")
        if not hasattr(faction, "temp_modifiers"): faction.temp_modifiers = {}
        
        # speed_strategic: 0.4
        faction.temp_modifiers["strategic_speed_mult"] = 1.0 + self.get_modifier("speed_strategic", 0.0)

class SalvageMechanic(BaseMechanic):
    """
    Scrap-Lord Marauders: Salvage
    Steal blueprints/tech after battle.
    """
    def on_battle_end(self, context):
        # Already hooked in TacticalEngine logic?
        # Here we just boost the chance or logic.
        faction = context.get("faction")
        destroyed_units = context.get("destroyed_enemy_units", [])
        
        for unit in destroyed_units:
            if random.random() < 0.30:
                # Salvage blueprint
                # Need mechanism to unlock blueprints.
                # faction.unlock_blueprint(unit.blueprint_id)
                pass 

class PlasmaOverchargeMechanic(BaseMechanic):
    """
    Aurelian Hegemony: Plasma Overcharge
    Weapon boost with risk.
    """
    def on_ability_use(self, context):
        # Similar to Aether Overload but for Energy weapons
        caster = context.get("caster")
        ability = context.get("ability")
        
        dna = ability.get("elemental_dna", {})
        if dna.get("atom_energy", 0) >= 20:
             # Logic to choose overcharge? 
             # For now, passive check or context flag "use_overcharge"
             if context.get("use_overcharge", False):
                 context["damage_multiplier"] = 1.5
                 if random.random() < 0.20:
                     caster.current_hp -= caster.hp * 0.10
                     context["self_damage"] = True

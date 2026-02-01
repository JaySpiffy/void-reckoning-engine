from src.mechanics.base_mechanic import BaseMechanic

class ConvictionMechanic(BaseMechanic):
    """
    Templars of the Flux: Conviction
    Gain stacks on kills. Stacks provide damage bonus. Decay per turn.
    """
    def on_unit_death(self, context):
        # context: {unit, killer, faction}
        killer = context.get("killer")
        faction = context.get("faction")
        
        # killer might be a Faction object or a string name
        killer_name = getattr(killer, 'name', killer) if not isinstance(killer, str) else killer
        
        # We want to know if WE (faction) are the killer.
        if killer_name == faction.name:
            # Gain stack
            faction.conviction_stacks = min(faction.conviction_stacks + 1, 100)
            
            # [UPDATE] Immediately refresh modifiers so benefit is instant
            self._update_modifiers(faction)
            
    def on_economy_phase(self, context):
        # Apply damage bonus based on stacks
        faction = context.get("faction")
        self._update_modifiers(faction)

    def on_turn_start(self, context):
        # Decay
        faction = context.get("faction")
        if faction:
             # Basic decay: -5 per turn
             faction.conviction_stacks = max(0, faction.conviction_stacks - 5)
        
        # Refresh modifiers after decay
        self._update_modifiers(faction)

    def on_ability_use(self, context):
        """
        Hook for abilities that might generate/spend conviction or have side effects.
        """
        faction_name = getattr(context.get("caster"), "faction", None)
        # We need the faction object to modify resources.
        # Ensure context provides it or we can lookup via mechanics engine logic.
        # But here 'context' is from `on_ability_use` hook which passes dictionary.
        # We might need to rely on `self.engine` if available or `context` hacks.
        # Based on my check of `ability_manager`, we pass `faction` if possible but let's see.
        pass

    def on_morale_check(self, context):
        """
        Zealots are immune to morale checks if they have 'Morale Immune' trait 
        OR if they have high Conviction (e.g. > 50).
        """
        # Return True to indicate immunity
        unit = context.get("unit")
        # faction = context.get("faction") # Might be passed
        
        # 1. Trait Check
        if "Morale Immune" in getattr(unit, "traits", []):
            context["is_immune"] = True
            return True
            
        # 2. Conviction Check
        faction = context.get("faction")
        if faction:
             if faction.conviction_stacks >= 50:
                 context["is_immune"] = True
                 return True
                 
        return False

    def _update_modifiers(self, faction):
        """Helper to push conviction bonuses to faction temp_modifiers."""
        if not faction: return
        stacks = faction.conviction_stacks
        
        # 0.5% damage per stack -> max 50%
        damage_bonus = (stacks * 0.005)
        
        if not hasattr(faction, "temp_modifiers"):
            faction.temp_modifiers = {}
            
        faction.temp_modifiers["global_damage_mult"] = 1.0 + damage_bonus
        # Ability power scales too
        faction.temp_modifiers["ability_power_mult"] = 1.0 + damage_bonus


class BiomassMechanic(BaseMechanic):
    """
    Bio-Tide Collective: Biomass
    Gain biomass from deaths. Spend to reduce recruitment cost.
    """
    def on_unit_death(self, context):
        unit = context.get("unit")
        faction = context.get("faction")
        # Ensure we are gaining biomass from deaths on OUR planets or BY US? 
        # Plan says "unit dies on faction-owned planet".
        # Context needs location.
        location = context.get("location") # Planet object
        
        if location and location.owner == faction.name:
            cost = unit.cost
            gain = cost * 0.3
            faction.biomass_pool += gain

    def on_unit_recruited(self, context):
        unit = context.get("unit")
        faction = context.get("faction")
        
        cost = 0
        if unit:
            cost = unit.cost
        elif "cost" in context:
            cost = context["cost"]
        elif "blueprint" in context:
            bp = context["blueprint"]
            cost = getattr(bp, 'cost', 0)
            
        if cost <= 0: return
        
        current_pool = faction.biomass_pool
        if current_pool > 0:
            discount = min(current_pool, cost * 0.2) # Max 20% discount
            # We need to signal the discount back to the caller.
            # Assuming context is a mutable dict for return values or we modify unit?
            # Recruitment service has likely already paid. 
            # We strictly need this hook BEFORE payment or REFUND.
            # Let's assume Refund for now -> Add back to budget.
            if hasattr(faction, "requisition"):
                faction.requisition += discount
            
            faction.biomass_pool -= discount

    def on_economy_phase(self, context):
        faction = context.get("faction")
        if faction:
             faction.biomass_pool *= 0.9 # 10% decay


class IndustrialMightMechanic(BaseMechanic):
    """
    Steel-Bound Syndicate: Industrial Might
    Reduced building costs, faster production.
    """
    def on_economy_phase(self, context):
        # Applied via static modifiers usually, but we can set dynamic ones here
        faction = context.get("faction")
        # building_cost: -0.1
        if not hasattr(faction, "temp_modifiers"): faction.temp_modifiers = {}
        faction.temp_modifiers["building_cost_mult"] = 1.0 + self.get_modifier("building_cost", -0.1)

    def on_building_constructed(self, context):
        # "Increase production speed" - maybe finish another item?
        # Or simply passive speed boost. 
        # Plan: "Increase production speed by 25% (reduce turns_left)"
        # This hook runs AFTER construction. Maybe it affects REMAINING items in queue?
        planet = context.get("planet")
        if planet and planet.construction_queue:
            for task in planet.construction_queue:
                # Reduce turns left by 1 (simulating 25% speedup over time or instant boost)
                # Simple implementation: 25% chance to reduce turn count by 1
                import random
                if random.random() < 0.25 and task.get('turns_left', 0) > 1:
                    task['turns_left'] -= 1

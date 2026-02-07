from src.mechanics.base_mechanic import BaseMechanic
import random

class ReanimationProtocolsMechanic(BaseMechanic):
    """
    Algorithmic Hierarchy: Reanimation Protocols
    Chance to revive units on death.
    """
    def on_unit_death(self, context):
        unit = context.get("unit")
        faction = context.get("faction")
        # Logic is handled inside TacticalEngine hook generally, but we keep state here
        
        # Check chance
        chance = self.get_modifier("revive_chance", 0.5)
        if random.random() < chance:
            # We need to tell the engine to CANCEL the death or REVIVE.
            # Context["revived"] = True
            context["revived"] = True
            
            # Heal unit
            unit.current_hp = unit.max_hp * 0.25
            
            # Track stats
            stats = getattr(faction, "stats", {})
            stats["reanimations_this_turn"] = stats.get("reanimations_this_turn", 0) + 1
            faction.stats = stats

    def on_economy_phase(self, context):
        # Apply Logic Core modifiers (research speed, maintenance)
        faction = context.get("faction")
        
        if not hasattr(faction, "temp_modifiers"): faction.temp_modifiers = {}
        
        # Pull from registry config
        # research_speed: 0.3
        # maintenance_cost: -0.1
        
        # We need to map these to whatever the economy engine expects.
        # Assuming economy engine checks 'temp_modifiers' or we need to apply them directly?
        # Faction.py doesn't have a centralized modifier system for these yet, unlike combat.
        # But we can set them for later lookups.
        
        faction.temp_modifiers["research_speed_mult"] = 1.0 + self.get_modifier("research_speed", 0.0)
        faction.temp_modifiers["maintenance_mult"] = 1.0 + self.get_modifier("maintenance_cost", 0.0)

class AetherOverloadMechanic(BaseMechanic):
    """
    Transcendent Order: Aether Overload
    High Aether abilities risk self-damage.
    """
    def on_ability_use(self, context):
        # context: {caster, ability, target}
        caster = context.get("caster")
        ability = context.get("ability")
        
        # [LEGACY] Atomic attributes removed. Check new Ability Tags/Properties?
        # For now, default to stable/no-overload unless specified in ability effects?
        # Use atom_aether from ability dna if present (Phase 9 legacy)
        aether = ability.get("elemental_dna", {}).get("atom_aether", 0)
        if not aether:
             aether = ability.get("aether_cost", 0) # Fallback
             
        dna = getattr(caster, "elemental_dna", {})
        stability = dna.get("atom_stability", 50.0) if dna else 50.0
        
        # Fail chance
        fail_chance = (aether / 100.0) * (1.0 - (stability / 100.0))
        
        if random.random() < fail_chance:
            # Backfire
            damage = ability.get("payload", {}).get("damage", 0) * 0.5
            caster.current_hp -= damage
            context["overload_triggered"] = True
            
            # Apply debuff (abstractly represented in context or log)
            # In a real engine we'd add a StatusEffect object
            context["status_effects"] = context.get("status_effects", []) + ["Overloaded"]

class InstabilityMechanic(BaseMechanic):
    """
    Void-Spawn Entities: Instability
    Randomly phase out of reality.
    """
    def on_turn_start(self, context):
        faction = context.get("faction")
        engine = context.get("engine") # CampaignEngine
        
        # We need to access all units of this faction to apply phase shift.
        # This is expensive, but per mechanics design.
        # We iterate engine.fleets -> units, and engine.all_planets -> armies -> units?
        # Or hopefully the faction object has a list of units? No, Faction object doesn't list units directly (O(N) global scan).
        
        # Optimization: Use Engine's fleet/army lists and filter by faction.
        if engine:
            # 1. Fleets
            for fleet in engine.fleets:
                if fleet.faction == faction.name:
                    for u in fleet.units:
                         self.process_unit_instability(u)
                         
            # 2. Armies (Planets) - A bit harder to find all quickly without loop
            # But we can iterate all_planets if we must.
            # Assuming 'engine' has 'all_planets'
            if hasattr(engine, 'all_planets'):
                for p in engine.all_planets:
                     if hasattr(p, 'armies'):
                         for ag in p.armies:
                             if ag.faction == faction.name:
                                 for u in ag.units:
                                      self.process_unit_instability(u)

    # Helper for per-unit update if engine supports it, or manual iteration
    def process_unit_instability(self, unit):
        # Check elemental dna for volatility
        vol = 0
        dna = getattr(unit, "elemental_dna", {})
        if dna:
             vol = dna.get("atom_volatility", 0)
             
        # If we want instability, check tags
        if hasattr(unit, "tags") and "PhaseShift" in unit.tags:
             vol = max(vol, 50)

        
        if vol > 0 and random.random() < (vol / 100.0):
            unit.is_phased = True
            # Abstract effect: Maybe immune to damage but cannot attack?
            # Implemented elsewhere in combat engine checks "if unit.is_phased"
        else:
            unit.is_phased = False

class EternalMechanic(BaseMechanic):
    """
    Primeval Sentinels: Eternal
    Units go dormant instead of dying.
    """
    def on_unit_death(self, context):
        unit = context.get("unit")
        # Prevent death
        context["cancel_death"] = True
        unit.is_dormant = True
        unit.current_hp = 1 # Keep at 1 HP so is_alive() remains true? 
        # Or is_dormant overrides is_alive logic in combat engine?
        # Combat engine checks is_alive() -> current_hp > 0.
        # So we keep it at 1 HP but 'dormant' flag prevents actions.
        
        # We also need to remove them from combat? 
        # Or they stay on field as distinct hulks?
        # For simplicity: Stay on field, but ignored by targeting (needs engine support).
        
    def on_turn_start(self, context):
        # Regen dormant units
        faction = context.get("faction")
        engine = context.get("engine")
        
        if engine:
            # Similar iteration to Instability
            for fleet in engine.fleets:
                if fleet.faction == faction.name:
                    for u in fleet.units:
                        self.process_dormancy(u)
                        
            if hasattr(engine, 'all_planets'):
                for p in engine.all_planets:
                     if hasattr(p, 'armies'):
                         for ag in p.armies:
                             if ag.faction == faction.name:
                                 for u in ag.units:
                                     self.process_dormancy(u)
                                     
    def process_dormancy(self, unit):
        if getattr(unit, 'is_dormant', False):
            # Regen check
            # e.g. 50% chance or based on dna
            if random.random() < 0.3:
                unit.is_dormant = False
                unit.current_hp = unit.max_hp * 0.5 # Revive at 50%

class FurorMechanic(BaseMechanic):
    """
    Scrap-Lord Marauders: Furor!
    Momentum based combat bonus.
    """
    def on_battle_start(self, context):
        faction = context.get("faction")
        engine = context.get("engine")
        
        # Simple implementation: Boost melee damage based on army size
        # If we have more units than enemy, gain bonus.
        
        # We need to know our units in this battle.
        # Context usually has 'units' list if it's a battle context?
        # If not, we rely on static or global Furor counter?
        # Let's assume global Furor counter in faction.stats or similar.
        pass

    def on_economy_phase(self, context):
        # Apply static Furor modifiers from registry if any
        faction = context.get("faction")
        if not hasattr(faction, "temp_modifiers"): faction.temp_modifiers = {}
        
        # Modifiers: recruitment_cost: -0.1, melee_damage_mult: 0.1
        faction.temp_modifiers["recruitment_cost_mult"] = 1.0 + self.get_modifier("recruitment_cost", 0.0)
        faction.temp_modifiers["melee_damage_mult"] = 1.0 + self.get_modifier("melee_damage_mult", 0.0)

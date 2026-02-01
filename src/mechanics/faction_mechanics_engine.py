from src.mechanics.mechanics_loader import MechanicsLoader

class FactionMechanicsEngine:
    def __init__(self, campaign_manager, universe_name="void_reckoning"):
        self.campaign_manager = campaign_manager
        self.engine = campaign_manager # Alias for tactical engine compatibility
        self.loader = MechanicsLoader(universe_name)
        self.registry = self.loader.load_registry()
        self.active_mechanics = self.loader.instantiate_mechanics(self.registry) # {faction_name: [mechanics]}

    def apply_mechanics(self, faction_name, hook_name, context):
        """
        Execute all mechanics for a given faction at a specific hook.
        """
        # print(f"DEBUG: apply_mechanics called for {faction_name} - {hook_name}")
        # Handle snake_case vs Title Case vs whatever
        # Registry usually uses Title Case (Templars_of_the_Flux)
        # But simulation might use snake_case
        
        # Try exact match first
        mechanics = self.active_mechanics.get(faction_name)
        if not mechanics:
            # Try normalizing
            normalized = faction_name.replace(" ", "_").title() # Templars_of_the_Flux
            mechanics = self.active_mechanics.get(normalized, [])
            
        for mech in mechanics:
            handler = getattr(mech, hook_name, None)
            if handler and callable(handler):
                handler(context)
                
    def apply_mechanic_modifiers(self, faction_name, units):
        """
        Apply current faction-level modifiers (from mechanics) to a list of units.
        This allows global bonuses (e.g. Conviction, Furor!) to persist in combat.
        """
        # Resolve Faction Object
        faction = self.engine.factions.get(faction_name)
        if not faction: return
            
        # Get Standardized Modifiers (Phase 11 Refinement)
        # We consolidate key combat multipliers here
        unit_mods = {
            "melee_damage_mult": faction.get_modifier("melee_damage_mult", 1.0),
            "global_damage_mult": faction.get_modifier("global_damage_mult", 1.0),
            "bs_mod": int(faction.get_modifier("bs_mod", 0)),
            "defense_mod": int(faction.get_modifier("defense_mod", 0))
        }
        
        # Apply to units
        for u in units:
            if hasattr(u, "apply_temporary_modifiers"):
                u.apply_temporary_modifiers(unit_mods)
                
    def get_mechanic(self, faction_name, mechanic_type_cls):
        """Helper to get a specific mechanic instance for a faction"""
        mechanics = self.active_mechanics.get(faction_name, [])
        for m in mechanics:
            if isinstance(m, mechanic_type_cls):
                return m
        return None

    def get_ability_registry(self):
        """
        Returns the mapped ability registry for the universe, merging local overrides.
        """
        from src.core.universe_data import UniverseDataManager
        return UniverseDataManager.get_instance().get_ability_database().copy()

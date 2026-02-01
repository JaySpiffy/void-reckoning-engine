from typing import Optional, Dict, List, Any
from src.models.unit import Unit
from src.core import balance as bal

class UnitFactory:
    """
    Factory for creating Unit instances to ensure standardized initialization.
    """
    
    @staticmethod
    def create_from_blueprint(blueprint: Any, faction_name: str) -> Unit:
        """
        Creates a Unit instance from a UnitBlueprint using UnitBuilder.
        """
        from src.builders.unit_builder import UnitBuilder
        
        name = getattr(blueprint, 'name', "Unknown Unit")
        ma = getattr(blueprint, 'base_ma', 50)
        md = getattr(blueprint, 'base_md', 50)
        hp = getattr(blueprint, 'base_hp', 100)
        armor = getattr(blueprint, 'armor', 0)
        damage = getattr(blueprint, 'base_damage', 10)
        abilities = getattr(blueprint, 'abilities', {})
        auth_weapons = getattr(blueprint, 'authentic_weapons', [])
        traits = getattr(blueprint, 'traits', [])
        cost = getattr(blueprint, 'cost', 100)
        shield = getattr(blueprint, 'shield_max', 0)
        movement = getattr(blueprint, 'movement_points', 6)
        
        blueprint_id = getattr(blueprint, 'blueprint_id', None)
        unit_type = getattr(blueprint, 'type', "infantry").lower()
        
        builder = UnitBuilder(name, faction_name)
        builder.with_health(hp, max_shield=shield)
        builder.with_armor(armor)
        builder.with_morale(bal.UNIT_DEFAULT_LEADERSHIP)
        builder.with_traits(traits, abilities)
        builder.with_movement(movement)
        builder.with_stats_comp(ma=ma, md=md, damage=damage, armor=armor, hp=hp)
        
        # Add Weapons
        from src.data.weapon_data import get_weapon_stats
        for w_id in auth_weapons:
            w_stats = get_weapon_stats(w_id)
            builder.with_weapon(w_id, w_stats)
            
        builder.with_extra_data("unit_type", "Ship" if "ship" in unit_type or "cruiser" in unit_type else "Regiment")
        builder.with_extra_data("blueprint_id", blueprint_id)
        builder.with_extra_data("cost", cost)
        
        unit = builder.build()
        UnitFactory._finalize_unit(unit)
        return unit

    @staticmethod
    def create_from_blueprint_id(blueprint_id: str, faction_name: str, traits: List[str] = None) -> Any:
        from src.builders.unit_builder import UnitBuilder
        from src.utils.blueprint_registry import BlueprintRegistry
        import copy
        
        blueprint = BlueprintRegistry.get_instance().get_blueprint(blueprint_id)
        if not blueprint: return None
            
        b_data = copy.deepcopy(blueprint)
        builder = UnitBuilder(b_data.get("name", "Unknown"), faction_name)
        
        stats = b_data.get("base_stats", {})
        builder.with_health(stats.get("hp", 100), max_shield=stats.get("shield", 0))
        builder.with_armor(stats.get("armor", 0))
        builder.with_morale(bal.UNIT_DEFAULT_LEADERSHIP)
        builder.with_movement(stats.get("movement", 6))
        builder.with_stats_comp(
            ma=stats.get("ma", 50), md=stats.get("md", 50), 
            damage=stats.get("damage", 10), armor=stats.get("armor", 0), hp=stats.get("hp", 100)
        )
        
        # Process Traits
        final_traits = b_data.get("default_traits", [])
        if traits: final_traits = list(set(final_traits + traits))
        builder.with_traits(final_traits, {})
        
        # Process Components/Weapons
        from src.data.weapon_data import get_weapon_stats
        for c_entry in b_data.get("components", []):
            if isinstance(c_entry, dict):
                comp_id = c_entry.get("component")
                if comp_id:
                    w_stats = get_weapon_stats(comp_id)
                    builder.with_weapon(comp_id, w_stats)

        builder.with_extra_data("unit_type", "Ship" if "ship" in b_data.get("type", "").lower() else "Regiment")
        builder.with_extra_data("blueprint_id", blueprint_id)
        builder.with_extra_data("cost", b_data.get("cost", 100))
        
        unit = builder.build()
        UnitFactory._finalize_unit(unit)
        return unit

    @staticmethod
    def create_from_file(filepath: str, faction: str) -> Optional[Unit]:
        """Creates a Unit from either XML or markdown file."""
        from src.utils.unit_parser import detect_file_format, parse_unit_file
        # Note: Third-party parsing (e.g., parse_stellaris_units) has been removed.
        # To add custom universe-specific parsing, add logic here.
        try:
            fmt = detect_file_format(filepath)
            if fmt == "xml":
                print(f"WARNING: XML parsing is deprecated. Skipping {filepath}")
                return None
            elif fmt == "markdown":
                return parse_unit_file(filepath, faction)
        except Exception as e:
            print(f"Error in UnitFactory.create_from_file: {e}")
            return None
        return None

    @staticmethod
    def _finalize_unit(unit: Unit):
        """Applies trait modifications and finalizes unit state."""
        if not unit: return
        
        # [PHASE 3] Component Initialization for Legacy Units
        if not unit.health_comp:
            from src.builders.unit_builder import UnitBuilder
            # Use data from the unit to build components
            # This handles units created via legacy constructors
            builder = UnitBuilder(unit.name, unit.faction)
            builder.with_health(unit.base_hp, max_shield=getattr(unit, 'shield_max', 0))
            builder.with_armor(unit.base_armor)
            builder.with_morale(unit.base_leadership)
            builder.with_traits(unit.traits, unit.abilities)
            
            # Sync back
            unit.health_comp = builder.health
            unit.armor_comp = builder.armor
            unit.morale_comp = builder.morale
            unit.trait_comp = builder.trait
            
            # Populate weapon components from authentic_weapons
            from src.data.weapon_data import get_weapon_stats
            for w_id in unit.authentic_weapons:
                w_stats = get_weapon_stats(w_id)
                unit.weapon_comps.append(builder.with_weapon(w_id, w_stats).weapons[-1])

        # Apply Traits from Registry
        from src.core.universe_data import UniverseDataManager
        registry = UniverseDataManager.get_instance().get_trait_registry()
        
        if registry:
            trait_mods = {}
            for trait_name, trait_data in registry.items():
                if "modifiers" in trait_data:
                    trait_mods[trait_name] = trait_data["modifiers"]
            
            unit.apply_traits(trait_mods)
        
        unit.recalc_stats()

    @staticmethod
    def create_transport(faction_name: str) -> Unit:
        """Creates a standard transport ship."""
        from src.builders.unit_builder import UnitBuilder
        builder = UnitBuilder("Generic Transport", faction_name)
        return (builder.with_health(200, max_shield=0)
                .with_armor(10)
                .with_traits([], {"Tags": ["Transport"]})
                .with_extra_data("transport_capacity", 4)
                .build())


    @staticmethod
    def create_pdf(tier: str, faction_name: str) -> Unit:
        """
        Creates Planetary Defense Force units using UnitBuilder.
        """
        from src.builders.unit_builder import UnitBuilder
        
        tier_stats = {
            "Conscript": {"ma": 30, "md": 30, "hp": 30, "armor": 10},
            "Regular": {"ma": 35, "md": 35, "hp": 40, "armor": 15},
            "Elite": {"ma": 40, "md": 40, "hp": 50, "armor": 20}
        }
        stats = tier_stats.get(tier, {"ma": 25, "md": 25, "hp": 25, "armor": 0})
        
        builder = UnitBuilder(f"PDF {tier}", faction_name)
        return (builder.with_health(stats["hp"])
                .with_armor(stats["armor"])
                .with_stats_comp(ma=stats["ma"], md=stats["md"], damage=2, armor=stats["armor"], hp=stats["hp"])
                .with_movement(6)
                .with_traits([], {"Tags": ["Infantry"]})
                .build())

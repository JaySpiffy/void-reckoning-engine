import os
import copy
from typing import Dict, List, Any, Set, Optional

from src.models.unit import Unit
from src.core.config import get_universe_config
from src.combat.tactical_engine import resolve_fleet_engagement

class CrossUniverseCombatHandler:
    """
    Handles logic for cross-universe combat, including detecting mixed armies,
    translating units to a common stat scale, and orchestrating battles.
    """

    @staticmethod
    def detect_universe_mix(armies_dict: Dict[str, List[Unit]]) -> Dict[str, Any]:
        """
        Analyzes armies to detect if units are from multiple universes.
        Returns: {
            "is_mixed": bool,
            "universes": Set[str],
            "faction_universes": Dict[faction, universe],
            "recommended_battle_universe": str
        }
        """
        universes = set()
        faction_universes = {}
        
        for faction, units in armies_dict.items():
            for unit in units:
                source_uni = getattr(unit, 'source_universe', None) or \
                            getattr(unit, 'universe', None) or \
                            'unknown'
                universes.add(source_uni)
                faction_universes[faction] = source_uni
                
        return {
            "is_mixed": len(universes) > 1,
            "universes": universes,
            "faction_universes": faction_universes,
            "recommended_battle_universe": list(universes)[0] if universes else "void_reckoning"
        }

    @staticmethod
    def translate_army_to_universe(army: List[Unit], target_universe: str) -> List[Unit]:
        """
        Translates all units in an army to the target universe's stat scale.
        """
        # DNA system removed. Using static stats.
        # In the future, this can use a stat translation table.
        translated_army = []
        for unit in army:
            translated_unit = copy.copy(unit)
            translated_unit.is_translated = True
            translated_unit.active_universe = target_universe
            translated_army.append(translated_unit)
            
        return translated_army

    @staticmethod
    def load_universe_combat_rules(universe_name: str = "void_reckoning"):
        """Dynamically loads combat rules for a universe."""
        try:
            config = get_universe_config(universe_name)
            # Using module reference from config.json
            rules_module = config.load_module("combat_rules")
            
            # Look for a class that implements CombatRulesBase (proxy: ends in CombatRules)
            for attr in dir(rules_module):
                if attr.endswith("CombatRules"):
                    cls = getattr(rules_module, attr)
                    if isinstance(cls, type):
                        return cls()
            
            # Fallback to direct import if no class found in module
            if universe_name == "void_reckoning":
                 from universes.void_reckoning.combat_phases import EternalCrusadeCombatRules
                 return EternalCrusadeCombatRules()
        except Exception as e:
            print(f"  > [WARNING] Failed to load combat rules for {universe_name}: {e}")
            # Final fallback
            try:
                 from universes.void_reckoning.combat_phases import EternalCrusadeCombatRules
                 return EternalCrusadeCombatRules()
            except ImportError:
                 return None

    @classmethod
    def resolve_fleet_engagement_with_universe(cls, armies_dict, universe_name=None, 
                                              cross_universe=False, profile_memory=False, **kwargs):
        """
        Convenience wrapper for universe-aware combat with cross-universe support.
        """
        from src.utils.memory_profiler import MemoryProfiler
        
        profiler = None
        if profile_memory:
            profiler = MemoryProfiler()
            profiler.start()
            profiler.snapshot("Start")
        
        # Detect universe mix
        mix_info = cls.detect_universe_mix(armies_dict)
        
        if mix_info["is_mixed"] or cross_universe:
            if profiler:
                profiler.snapshot("Before Translation")
                
            # Determine battle universe
            battle_uni = universe_name or mix_info["recommended_battle_universe"]
            print(f"\n=== CROSS-UNIVERSE COMBAT DETECTED ===")
            print(f"Universes involved: {', '.join(mix_info['universes'])}")
            print(f"Battle Universe: {battle_uni}")
            print("Translating all units to common stat scale...")
            
            # Translate all armies
            translated_armies = {}
            for faction, army in armies_dict.items():
                translated_armies[faction] = cls.translate_army_to_universe(army, battle_uni)
                
            armies_dict = translated_armies
            universe_name = battle_uni
            
            if profiler:
                profiler.snapshot("After Translation")
        
        # Load rules for battle universe
        rules = cls.load_universe_combat_rules(universe_name or "void_reckoning")
        
        # [VERIFICATION FIX] Instantiate Mechanics Engine if not present
        if "mechanics_engine" not in kwargs:
             # We need a backing engine mock or instance
             # For standalone combat, we create a lightweight wrapper
             from src.mechanics.faction_mechanics_engine import FactionMechanicsEngine
             
             class MockReporter:
                 def log_event(self, *args, **kwargs): pass
                 def report_status(self, *args, **kwargs): pass

             class AdHocCampaignEngine:
                 def __init__(self, armies):
                     self.factions = {}
                     self.faction_reporter = MockReporter()
                     for f in armies.keys():
                         self.factions[f] = AdHocFaction(f)
             
             class AdHocFaction:
                 def __init__(self, name):
                     self.name = name
                     self.custom_resources = {}
                     self.temp_modifiers = {}

                 def get_modifier(self, key, default=0):
                     return self.temp_modifiers.get(key, default)
                     
                     try:
                         import json
                         reg_path = os.path.join("universes", universe_name or "void_reckoning", "factions", "faction_registry.json")
                         if os.path.exists(reg_path):
                             with open(reg_path, 'r') as f:
                                 data = json.load(f)
                                 if name in data:
                                     start_res = data[name].get("starting_resources", {})
                                     if "conviction" in start_res: self.custom_resources["conviction"] = start_res["conviction"]
                                     if "biomass" in start_res: self.custom_resources["biomass"] = start_res["biomass"]
                                     if "souls" in start_res: self.custom_resources["souls"] = start_res["souls"]
                     except Exception as e:
                         print(f"Warning: Failed to load AdHoc resources for {name}: {e}")
    
             if armies_dict:
                 camp_engine = AdHocCampaignEngine(armies_dict)
                 mech_engine = FactionMechanicsEngine(camp_engine, universe_name=universe_name or "void_reckoning")
                 kwargs["mechanics_engine"] = mech_engine
                 
        result = resolve_fleet_engagement(armies_dict, universe_rules=rules, **kwargs)
        
        if profiler:
            profiler.snapshot("After Combat")
            report = profiler.stop()
            print(profiler.get_report())
        else:
            report = None
            
        # Standardize result to dictionary
        if isinstance(result, tuple):
            result = {
                "winner": result[0],
                "survivors": result[1],
                "rounds": result[2],
                "stats": result[3] if len(result) > 3 else {}
            }
        
        if report:
            result["memory_profile"] = report
            
        return result

    @classmethod
    def run_cross_universe_duel(cls, unit1_path: str, unit2_path: str, battle_universe: str = None):
        """
        Executes a duel between two units from potentially different universes.
        """
        from src.combat.combat_utils import find_unit_by_name
        from src.core.universe_data import UniverseDataManager
        from src.utils.unit_parser import load_all_units
        
        udm = UniverseDataManager.get_instance()
        
        def parse_unit_path(path):
            parts = path.split(':')
            if len(parts) != 3:
                raise ValueError(f"Invalid unit path format: {path}. Expected universe:faction:unit_name")
            return parts[0], parts[1], parts[2]
        
        u1_uni, u1_fac, u1_name = parse_unit_path(unit1_path)
        u2_uni, u2_fac, u2_name = parse_unit_path(unit2_path)
        
        # Load data for both universes
        udm.load_universe_data(u1_uni)
        udm.load_universe_data(u2_uni)
        
        # Find units
        registry = load_all_units()
        
        u1_base = find_unit_by_name(registry, u1_name, universe_name=u1_uni)
        u2_base = find_unit_by_name(registry, u2_name, universe_name=u2_uni)
        
        if not u1_base or not u2_base:
            print(f"Error: Could not find units {u1_name} or {u2_name}")
            return
        
        # Create armies
        armies = {
            f"{u1_uni}_{u1_fac}": [u1_base],
            f"{u2_uni}_{u2_fac}": [u2_base]
        }
        
        # Resolve
        return cls.resolve_fleet_engagement_with_universe(
            armies, 
            universe_name=battle_universe or u1_uni,
            cross_universe=True
        )

    @classmethod
    def run_cross_universe_battle(cls, config_path: str, profile_memory: bool = False):
        """Executes a cross-universe battle based on a JSON config."""
        import json
        from src.combat.combat_utils import find_unit_by_name
        from src.utils.unit_parser import load_all_units
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        battle_uni = config.get("battle_universe", "void_reckoning")
        armies_dict = {}
        
        # Load unit registry
        registry = load_all_units()
        
        for faction_cfg in config.get("factions", []):
            f_name = faction_cfg["name"]
            f_uni = faction_cfg["universe"]
            units = []
            for u_name in faction_cfg.get("units", []):
                count = faction_cfg.get("count", 1)
                base = find_unit_by_name(registry, u_name, universe_name=f_uni)
                if base:
                    for _ in range(count):
                        # Shallow copy/clone logic
                        new_u = copy.copy(base)
                        units.append(new_u)
            armies_dict[f_name] = units
            
        return cls.resolve_fleet_engagement_with_universe(
            armies_dict,
            universe_name=battle_uni,
            cross_universe=True,
            profile_memory=profile_memory,
            **config.get("combat", {})
        )

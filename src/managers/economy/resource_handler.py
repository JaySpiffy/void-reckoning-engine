from typing import TYPE_CHECKING, Dict, List, Any
import time
from src.core.constants import categorize_building, TRADE_BONUS_PER_PARTNER
from src.core import balance as bal
from src.utils.profiler import profile_method

if TYPE_CHECKING:
    from src.core.interfaces import IEngine
    from src.models.faction import Faction

ORBIT_DISCOUNT_MULTIPLIER = 0.5

def apply_resource_tier_bonuses(f, t): 
    # Placeholder for third-party mods
    return {}

class ResourceHandler:
    """
    Handles income generation, upkeep calculation, and resource aggregation.
    """
    def __init__(self, engine: 'IEngine'):
        self.engine = engine

    def calculate_ground_raid_income(self, f_name: str) -> int:
        """
        Calculate raiding income from ground armies on enemy planets.
        Provides alternative income source for factions without fleets.
        """
        raid_income = 0
        
        # This is a bit expensive (O(Planets)), but happens once per turn per faction
        for p in self.engine.all_planets:
            if p.owner == f_name:
                continue  # Skip own planets
            
            # Check for ground armies on this planet
            if hasattr(p, 'armies'):
                for ag in p.armies:
                    if ag.faction == f_name and not ag.is_destroyed:
                        # Calculate raid income based on planet value
                        planet_value = p.base_income_req if hasattr(p, 'base_income_req') else 100
                        raid_amount = int(planet_value * bal.GROUND_RAID_INCOME_RATIO) 
                        
                        # Scale by army size
                        army_size = len(ag.units)
                        raid_amount = min(raid_amount * army_size, bal.GROUND_RAID_MAX_PER_ARMY)
                        
                        raid_income += raid_amount
        
        return raid_income

    @profile_method
    def precalculate_economics(self) -> Dict[str, Any]:
        """
        Computes all faction economic data in a single pass.
        """
        start_time = time.time()
        
        cache = {}
        # Pre-filter and initialize cache
        factions_to_process = [f.name for f in self.engine.get_all_factions() if f.name != "Neutral"]
        cache = {f_name: {"income": 0, "fleet_upkeep": 0, "army_upkeep": 0, "infrastructure_upkeep": 0, "total_upkeep": 0, "planets_count": 0} for f_name in factions_to_process}

        # 1. Combined Income & Planet Stats pass
        for f_name, planets in self.engine.planets_by_faction.items():
            if f_name == "Neutral": continue
            f_cache = cache.get(f_name)
            if not f_cache: continue
            
            f_mgr = self.engine.get_faction(f_name)
            tier = 3
            if hasattr(self.engine, 'strategic_ai') and self.engine.strategic_ai:
                p_personality = self.engine.strategic_ai.get_faction_personality(f_name)
                if p_personality and hasattr(p_personality, 'quirks'):
                    tier = p_personality.quirks.get('tier', 3)
            
            multipliers = apply_resource_tier_bonuses(f_mgr, tier)
            income_mult = multipliers.get('energy', 1.0)
            
            base_income = 0
            army_upkeep = 0
            infra_upkeep = 0 # Initialized here
            rp_income = 0
            income_by_category = {"Tax": 0, "Mining": 0, "Trade": 0, "Conquest": 0}
            
            # 1b. Use Cached Planet Output
            for p in planets:
                # This call now uses _cached_econ_output internally if available
                generation = p.generate_resources() 
                
                # ... Categorization logic remains similar but faster ...
                res_breakdown = generation.get("breakdown", {})
                
                income_by_category["Tax"] += res_breakdown.get("base", 0)
                income_by_category["Mining"] += res_breakdown.get("buildings", 0) + res_breakdown.get("provinces", 0)
                
                base_income += generation.get("req", 0)
                
                # Base Income from Planet Ownership (prevent death spiral)
                base_planet_income = bal.MIN_PLANET_INCOME
                
                income_by_category["Tax"] += base_planet_income
                base_income += base_planet_income
                
                # Add pre-calc Maintenance
                infra_upkeep += generation.get("infrastructure_upkeep", 0)
                
                # Research Output (Passed through generation result now)
                rp_income += generation.get("research", 0)

                # Inline Army Upkeep calculation (Ground Armies)
                if hasattr(p, 'armies'):
                    p_armies = [ag for ag in p.armies if ag.faction == f_name and not ag.is_destroyed]
                    if p_armies:
                        capacity = getattr(p, 'garrison_capacity', 1)
                        # [FIX] Apply GARRISON_UPKEEP_MULTIPLIER to armies within capacity
                        # This rewards factions for maintaining defensive garrisons
                        
                        # Note: Could cache ArmyGroup upkeep too, but they are fewer than fleets.
                        costs = [sum(getattr(u, 'upkeep', 0) for u in ag.units) for ag in p_armies]
                        costs.sort(reverse=True) # Garrison the most expensive units first
                        
                        garrisoned_cost = sum(costs[:capacity]) * bal.GARRISON_UPKEEP_MULTIPLIER
                        excess_cost = sum(costs[capacity:])
                        army_upkeep += (garrisoned_cost + excess_cost)
            
            # Apply Trade Bonuses
            trade_bonus = 1.0
            if hasattr(self.engine, 'diplomacy') and self.engine.diplomacy:
                trade_partners = 0
                f_treaties = self.engine.diplomacy.treaties.get(f_name, {})
                for partner, treaty in f_treaties.items():
                    # [FIX] Allies also trade! "Level 2" includes "Level 1" benefits.
                    if treaty in ["Trade", "Alliance"]:
                        trade_partners += 1
                
                if trade_partners > 0:
                    trade_bonus = 1.0 + (trade_partners * TRADE_BONUS_PER_PARTNER)
            
            trade_income = int(base_income * income_mult * (trade_bonus - 1.0)) if trade_bonus > 1.0 else 0
            income_by_category["Trade"] = trade_income
            
            # Research Speed
            rp_mult = f_mgr.get_modifier("research_speed_mult", 1.0)
            f_cache["research_income"] = int(rp_income * rp_mult)
            
            f_cache["income"] = int(base_income * income_mult * trade_bonus)
            
            # Ground Raid Income
            raid_income = self.calculate_ground_raid_income(f_name)
            f_cache["income"] += raid_income
            if raid_income > 0 and self.engine.logger:
                 self.engine.logger.economy(f"[RAID] {f_name} plundered {raid_income} Req from ground operations.")

            f_cache["income_by_category"] = income_by_category
            f_cache["army_upkeep"] = army_upkeep
            f_cache["infrastructure_upkeep"] = infra_upkeep
            f_cache["planets_count"] = len(planets)


        # 2. Optimized Fleet Upkeep pass
        for f_name, fleets in self.engine.fleets_by_faction.items():
            f_cache = cache.get(f_name)
            if not f_cache: continue
            
            total_fleet_upkeep = 0
            for f in fleets:
                if f.is_destroyed: continue
                
                # optimization 4.2: Use Cached Upkeep
                fleet_total = f.upkeep # Property uses _cached_upkeep
                
                if f.is_in_orbit:
                    fleet_total *= ORBIT_DISCOUNT_MULTIPLIER
                
                # Apply UserRequested Reduced Maintenance
                if hasattr(bal, 'FLEET_MAINTENANCE_SCALAR'):
                    fleet_total *= bal.FLEET_MAINTENANCE_SCALAR
                
                total_fleet_upkeep += int(fleet_total)

                # [NEW] orbital infrastructure Income
                for u in f.units:
                    if getattr(u, 'unit_class', '') == 'MiningStation':
                         mining_yield = 500
                         f_cache["income"] += mining_yield
                         if "income_by_category" in f_cache:
                             f_cache["income_by_category"]["Mining"] += mining_yield
                             
                    elif getattr(u, 'unit_class', '') == 'ResearchOutpost':
                         research_yield = 10
                         # Apply research speed multiplier
                         f_mgr = self.engine.get_faction(f_name)
                         rp_mult = f_mgr.get_modifier("research_speed_mult", 1.0) if f_mgr else 1.0
                         
                         f_cache["research_income"] = f_cache.get("research_income", 0) + int(research_yield * rp_mult)
            
            f_cache["fleet_upkeep"] = total_fleet_upkeep
            f_cache["military_upkeep"] = total_fleet_upkeep + f_cache.get("army_upkeep", 0)
            
        # 3. Final Aggregation and Penalty
        for f_name, f_cache in cache.items():
            # Step 2: Fix - Include Infrastructure in Base Upkeep
            base_upkeep = f_cache["fleet_upkeep"] + f_cache["army_upkeep"] + f_cache["infrastructure_upkeep"]
            
            # Oversized Navy Penalty logic
            num_fleets = len([fl for fl in self.engine.fleets_by_faction.get(f_name, []) if not fl.is_destroyed])
            limit = max(1, f_cache["planets_count"] * 4)
            over = num_fleets - limit
            
            penalty = 0
            if over > 0:
                penalty_pct = min(1.0, over * bal.ECON_NAVY_PENALTY_RATE)
                penalty = int(base_upkeep * penalty_pct)

            f_mgr = self.engine.get_faction(f_name)
            m_mult = f_mgr.get_modifier("maintenance_mult", 1.0) if f_mgr else 1.0
            
            f_cache["total_upkeep"] = max(1, int((base_upkeep + penalty) * m_mult))

        return cache

    def analyze_flow_bottlenecks(self, f_name: str, econ_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes economic data to identify flow bottlenecks (e.g. lack of trade, high upkeep).
        Returns a dict suitable for 'resource_flow_bottleneck' telemetry.
        """
        bottlenecks = []
        income_cats = econ_data.get("income_by_category", {})
        total_income = econ_data.get("income", 1)
        if total_income == 0: total_income = 1
        
        # 1. Check Income Balance
        tax_ratio = income_cats.get("Tax", 0) / total_income
        trade_ratio = income_cats.get("Trade", 0) / total_income
        mining_ratio = income_cats.get("Mining", 0) / total_income
        
        if trade_ratio < 0.05 and self.engine.turn_counter > 20:
            bottlenecks.append({"category": "Trade", "issue": "underdeveloped", "impact": 0.0})
            
        if mining_ratio < 0.20:
             bottlenecks.append({"category": "Mining", "issue": "insufficient_capacity", "impact": 0.20 - mining_ratio})
             
        # 2. Check Expense Pressure
        total_upkeep = econ_data.get("total_upkeep", 0)
        upkeep_ratio = total_upkeep / total_income
        
        if upkeep_ratio > 0.8:
            bottlenecks.append({"category": "Upkeep", "issue": "critical_pressure", "impact": upkeep_ratio})
        elif upkeep_ratio > 0.5:
             bottlenecks.append({"category": "Upkeep", "issue": "high_pressure", "impact": upkeep_ratio})

        return {
            "flow_analysis": {
                "income_sources": income_cats,
                "expense_ratio": upkeep_ratio
            },
            "bottlenecks": bottlenecks,
            "efficiency_score": max(0.0, 1.0 - upkeep_ratio) * 100
        }

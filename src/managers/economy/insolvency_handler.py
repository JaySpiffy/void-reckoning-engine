import time
import heapq
import itertools
from operator import itemgetter
from typing import TYPE_CHECKING, List, Any
from src.core.constants import ORBIT_DISCOUNT_MULTIPLIER, categorize_building
from src.models.fleet import Fleet
from src.models.army import ArmyGroup
from src.utils.profiler import profile_method

if TYPE_CHECKING:
    from src.core.interfaces import IEngine
    from src.models.faction import Faction

class InsolvencyHandler:
    """
    Handles bankruptcy protocols and unit disbanding.
    """
    def __init__(self, engine: 'IEngine'):
        self.engine = engine
        self.perf_metrics = {"insolvency_time": 0.0, "disbanded_count": 0}

    @profile_method
    def handle_insolvency(self, f_name: str, faction_mgr: 'Faction', my_fleets: List['Fleet'], income: int, upkeep: int, cached_upkeep: int = None) -> None:
        """
        Emergency protocols for bankruptcy.
        Disbands units prioritizing high upkeep.
        """
        start_time = time.time()
        
        current_upkeep = cached_upkeep if cached_upkeep is not None else upkeep
        sustainability_threshold = income * 0.9
        
        # Early exit if solvent
        if faction_mgr.requisition >= 0 and current_upkeep < sustainability_threshold:
            return

        # 2a. Determine Category Overshoot (New Step 4)
        import src.core.balance as bal
        
        # Calculate totals from candidates (since we don't have separate sums here readily available without iterating)
        # But we do verify against `income` and `caps`.
        # To be efficient, we'll just check if we are *forced* to cut from a specific category.
        
        inc_base = max(1, income)
        
        # We need current upkeep per category to do this right. 
        # Since we don't want to re-sum everything, we rely on the `candidates` list and "cut until under cap".
        # But `candidates` is mixed.
        # We need to tag candidates with their category (Navy or Army).
        
        # Refine Candidate Generation to include type
        # Format: (upkeep_value, unit, container, location, type_tag)
        
        navy_candidates = ((getattr(u, 'upkeep', 0), u, f, None, "NAVY") for f in my_fleets for u in f.units)
        cargo_candidates = ((getattr(u, 'upkeep', 0), u, ag, f, "ARMY") for f in my_fleets for ag in f.cargo_armies for u in ag.units)
        planet_candidates = (
            (getattr(u, 'upkeep', 0), u, ag, p, "ARMY") for p in self.engine.planets_by_faction.get(f_name, [])
            if hasattr(p, 'armies')
            for ag in p.armies if ag.faction == f_name and not ag.is_destroyed
            for u in ag.units
        )
        
        candidates_gen = itertools.chain(navy_candidates, cargo_candidates, planet_candidates)
        
        # Materialize list to process stats
        candidates = list(candidates_gen)
        
        # Calculate current category upkeeps
        current_navy_upkeep = sum(c[0] for c in candidates if c[4] == "NAVY")
        current_army_upkeep = sum(c[0] for c in candidates if c[4] == "ARMY")
        
        navy_cap = income * bal.MAINT_CAP_NAVY
        army_cap = income * bal.MAINT_CAP_ARMY
        
        navy_over = current_navy_upkeep > navy_cap
        army_over = current_army_upkeep > army_cap
        
        # Sorting Strategy:
        # If insolvent (Req < 0), cut highest upkeep regardless of type (Emergency)
        # If Solvent but Over Cap, prioritize cutting the Over type.
        
        if faction_mgr.requisition < 0:
             # Deep cut needed - Debt Protocol
             candidates.sort(key=itemgetter(0), reverse=True)
        else:
            # Cap Compliance Protocol
            # Prioritize candidates that are from an oversized category
            # Sort Refined: (IsFromOverCategory, Upkeep)
            # Tuple boolean sorts False then True, so we want reverse=True for (True, HighUpkeep)
            def sort_key(c):
                is_over = (c[4] == "NAVY" and navy_over) or (c[4] == "ARMY" and army_over)
                return (is_over, c[0])
                
            candidates.sort(key=sort_key, reverse=True)
            
            # If nothing is over cap and we are solvent, we might clear list?
            # Original check 'current_upkeep < sustainability' handles overall health.
            # But the user wants STRICT enforcement of 12.5%.
            
            if not navy_over and not army_over and faction_mgr.requisition >= 0 and current_upkeep < sustainability_threshold:
                 candidates = [] # Nothing to do

        disbanded_count = 0
        savings = 0
        scrap_generated = 0
        
        # Pre-calculate garrison safety for free upkeep slots
        free_army_groups = set()
        for f_p in self.engine.planets_by_faction.get(f_name, []):
            if hasattr(f_p, 'armies'):
                 p_armies = [ag for ag in f_p.armies if ag.faction == f_name and not ag.is_destroyed]
                 if p_armies:
                     p_armies.sort(key=lambda ag: sum(getattr(unit, 'upkeep', 0) for unit in ag.units), reverse=True)
                     capacity = getattr(f_p, 'garrison_capacity', 1)
                     for i in range(min(len(p_armies), capacity)):
                         free_army_groups.add(p_armies[i])

        # 2. Disbanding loop
        if self.engine.logger:
             self.engine.logger.economy(f"[INSOLVENCY_DEBUG] {f_name} Unit Candidates: {len(candidates)}. Req: {faction_mgr.requisition}. NavyOver: {navy_over}, ArmyOver: {army_over}")
             
        for u_upkeep, u, container, loc, u_type in candidates:
            
            # STOP CONDITIONS RETHINK per Step 4
            # "Category-Based: If fleet exceeds 12.5%, disband until under limit."
            # "Aggressive: Stop only when Requisition >= 0"
            
            # Check dynamic caps
            now_navy_ok = current_navy_upkeep <= navy_cap
            now_army_ok = current_army_upkeep <= army_cap
            is_solvent = faction_mgr.requisition >= 0
            
            # If we are broke, we must cut.
            # If we are solvent, we only cut if the specific category is STILL over.
            
            should_cut = False
            
            if not is_solvent:
                should_cut = True # Emergency
            else:
                if u_type == "NAVY" and not now_navy_ok:
                    should_cut = True
                elif u_type == "ARMY" and not now_army_ok:
                    should_cut = True
                    
            if not should_cut:
                # If we are solvent and this unit's category is fine, skippit?
                # Or stop? If sorted by "Over", then once we hit non-over units, we might be done?
                # But we might have mixed list.
                continue 
            
            try:
                if isinstance(container, Fleet):
                    container.units.remove(u)
                    container.invalidate_caches()
                    if not container.units:
                        container.is_destroyed = True
                elif isinstance(container, ArmyGroup):
                    container.units.remove(u)
                    if not container.units:
                        container.is_destroyed = True
                        if loc:
                            if hasattr(loc, 'cargo_armies') and container in loc.cargo_armies:
                                loc.cargo_armies.remove(container)
                                if isinstance(loc, Fleet):
                                    loc.invalidate_used_capacity()
                            elif hasattr(loc, 'armies') and container in loc.armies:
                                loc.armies.remove(container)
            except ValueError:
                continue 
            
            # Update savings and upkeep
            adjusted_u_upkeep = u_upkeep
            if isinstance(container, Fleet) and container.is_in_orbit:
                adjusted_u_upkeep *= ORBIT_DISCOUNT_MULTIPLIER
            elif container in free_army_groups:
                adjusted_u_upkeep = 0

            savings += adjusted_u_upkeep
            current_upkeep -= adjusted_u_upkeep
            
            if u_type == "NAVY": current_navy_upkeep -= adjusted_u_upkeep
            if u_type == "ARMY": current_army_upkeep -= adjusted_u_upkeep
            
            scrap = int(u.cost * 0.25)
            faction_mgr.requisition += scrap 
            scrap_generated += scrap
            disbanded_count += 1
        
        self.perf_metrics["insolvency_time"] = time.time() - start_time
        self.perf_metrics["disbanded_count"] += disbanded_count
        
        if disbanded_count > 0:
            if self.engine.logger:
                self.engine.logger.economy(f"[INSOLVENCY] {f_name} restructured {disbanded_count} units. Saved {savings}R/turn. Gained {scrap_generated}R.")
            self.engine.faction_reporter.log_event(f_name, "economy", f"Financial Restructuring: {disbanded_count} units decommissioned.")

        if self.engine.logger:
             self.engine.logger.economy(f"[INSOLVENCY_DEBUG] {f_name} Liquidation Check. Req: {faction_mgr.requisition}, Fleets: {len(my_fleets)}")

        # 3. Infrastructure Liquidation (If still bankrupt or unsustainable)
        # Trigger if:
        # A) Unsustainable (Bleeding money)
        # B) Deep Debt (Need cash NOW to resume operations)
        # C) Defenseless (No Fleets and Debt = Deadlock. Must clear debt to recruit)
        
        is_deep_debt = faction_mgr.requisition < -20000
        is_bleeding = faction_mgr.requisition < 0 and current_upkeep > sustainability_threshold
        is_defenseless = len(my_fleets) == 0 and faction_mgr.requisition < 0
        
        if is_bleeding or is_deep_debt or is_defenseless:
             self._liquidate_infrastructure(f_name, faction_mgr, current_upkeep, sustainability_threshold)

    def _liquidate_infrastructure(self, f_name: str, faction_mgr: 'Faction', current_upkeep: int, sustainability_threshold: int):
        """
        Sells buildings to recover requisition and reduce upkeep.
        """
        from src.core.constants import get_building_category, categorize_building
        from operator import itemgetter
        
        building_db = self.engine.universe_data.get_building_database()
        candidates = []
        
        # Gather all buildings with upkeep
        for p in self.engine.planets_by_faction.get(f_name, []):
            # Check planet buildings
            for b_id in list(p.buildings):
                b_data = building_db.get(b_id, {})
                upkeep = b_data.get("maintenance", 0)
                category = categorize_building(b_id, b_data)

                # PROTECTION: Never sell economic buildings
                if category == "Economy":
                    continue

                if upkeep > 0:
                    candidates.append((upkeep, b_id, p, None)) # None = Planet Core
            
            # Check province buildings
            if hasattr(p, 'provinces'):
                 for node in p.provinces:
                     for b_id in list(node.buildings):
                         b_data = building_db.get(b_id, {})
                         upkeep = b_data.get("maintenance", 0)
                         category = categorize_building(b_id, b_data)
                         
                         # PROTECTION: Never sell economic buildings
                         if category == "Economy":
                             continue

                         if upkeep > 0:
                             candidates.append((upkeep, b_id, p, node))

        # Sort by Upkeep (High to Low)
        candidates.sort(key=itemgetter(0), reverse=True)
        
        liquidated_count = 0
        savings = 0
        scrap_total = 0
        
        # Aggressive Liquidation Thresholds
        start_req = faction_mgr.requisition
        target_req = 2000 # Restart Threshold (Seed money for a Mine/Farm)
        
        if self.engine.logger:
             self.engine.logger.economy(f"[INSOLVENCY_DEBUG] {f_name} Liquidation Start. Req: {start_req}, Candidates: {len(candidates)}")

        current_req = start_req
        
        for upkeep, b_id, p, node in candidates:
            # Stop if we are safe (Positive Cash Buffer)
            if current_req > target_req: 
                break

            # Execute Sale
            if node:
                if b_id in node.buildings:
                    node.buildings.remove(b_id)
            else:
                if b_id in p.buildings:
                    p.buildings.remove(b_id)
                    
            # Refund
            b_data = building_db.get(b_id, {})
            cost = b_data.get("cost", 1000)
            scrap = int(cost * 0.25)
            faction_mgr.requisition += scrap
            
            savings += upkeep
            current_upkeep -= upkeep
            scrap_total += scrap
            liquidated_count += 1
            
        if liquidated_count > 0:
            if self.engine.logger:
                self.engine.logger.economy(f"[INSOLVENCY] {f_name} liquidated {liquidated_count} buildings. Saved {savings}R/turn. Gained {scrap_total}R.")
            self.engine.faction_reporter.log_event(f_name, "economy", f"Infrastructure Liquidation: {liquidated_count} buildings sold.")

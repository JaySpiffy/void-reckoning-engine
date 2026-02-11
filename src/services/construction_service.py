import random
import time
from src.utils.rng_manager import get_stream
from typing import List, Optional, Tuple, TYPE_CHECKING, Dict, Any
from src.reporting.telemetry import EventCategory
from src.reporting.telemetry import EventCategory
from src.core.constants import get_building_database, get_building_category
from src.core import balance as bal

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.models.faction import Faction
    from src.models.planet import Planet

from src.reporting.decision_logger import DecisionLogger

class ConstructionService:
    """
    Handles operational logic for building construction and planet queues.
    """
    def __init__(self, engine: 'CampaignEngine', rng: random.Random = None):
        self.engine = engine
        # self.rng replaced by get_stream("economy")
        
        # Track construction queue history for analysis
        self._queue_history: Dict[str, List[Dict[str, Any]]] = {}
        
        self.decision_logger = DecisionLogger(engine=engine)

        # Track construction queue history for analysis
        self._queue_history: Dict[str, List[Dict[str, Any]]] = {}

    def _log_starbase_deployment(self, faction: str, location_name: str, tier: int, cost: int, strategic_value: str, status: str):
        """Logs starbase deployment telemetry (Metric #4)."""
        if not self.engine.telemetry: return
        
        self.engine.telemetry.log_event(
            EventCategory.CONSTRUCTION,
            "starbase_deployment",
            {
                "faction": faction,
                "location": location_name,
                "tier": tier,
                "cost": cost,
                "strategic_value": strategic_value,
                "status": status,
                "turn": self.engine.turn_counter
            },
            turn=self.engine.turn_counter,
            faction=faction
        )

    def _log_building_upgrade_event(self, faction: str, planet: 'Planet', building_id: str, upgrade_to: str, cost: int, turns: int):
        """
        Logs building upgrade telemetry events.
        
        Args:
            faction: Faction name
            planet: Planet object
            building_id: Original building ID
            upgrade_to: Target building ID
            cost: Upgrade cost
            turns: Construction turns
        """
        if not self.engine.telemetry:
            return
        
        turn = getattr(self.engine, 'turn_counter', 0)
        
        # Get building data
        b_data = get_building_database().get(building_id, {})
        up_data = get_building_database().get(upgrade_to, {})
        
        event_data = {
            'faction': faction,
            'turn': turn,
            'planet': planet.name,
            'system': getattr(planet.system, 'name', 'unknown') if hasattr(planet, 'system') and planet.system else 'unknown',
            'building_from': building_id,
            'building_to': upgrade_to,
            'tier_from': b_data.get('tier', 1),
            'tier_to': up_data.get('tier', 1),
            'category': get_building_category(upgrade_to),
            'cost': cost,
            'turns': turns,
            'building_type': 'orbital' if 'naval_slots' in up_data or 'Unlocks Space Ship Construction' in up_data.get('effects', {}).get('description', '') else 'ground',
            'node_id': None  # Will be set if applicable
        }
        
        # Check if this is a node-based upgrade
        if hasattr(planet, 'provinces') and planet.provinces:
            for node in planet.provinces:
                if building_id in node.buildings:
                    event_data['node_id'] = node.id
                    break
        
        self.engine.telemetry.log_event(EventCategory.CONSTRUCTION, 'building_upgrade', event_data)
    
    def _log_construction_queue_analysis(self, faction: str, owned_planets: List['Planet']):
        """
        Logs construction queue efficiency and analysis metrics.
        
        Args:
            faction: Faction name
            owned_planets: List of owned planets
        """
        if not self.engine.telemetry:
            return
        
        turn = getattr(self.engine, 'turn_counter', 0)
        
        # Aggregate queue statistics
        total_slots = 0
        used_slots = 0
        total_queue_items = 0
        queue_by_category = {"Economy": 0, "Military": 0, "Research": 0, "Infrastructure": 0, "Orbital": 0}
        queue_by_planet = []
        stalled_queues = 0
        blocked_queues = 0
        
        for p in owned_planets:
            planet_data = {
                'planet': p.name,
                'system': getattr(p.system, 'name', 'unknown') if hasattr(p, 'system') and p.system else 'unknown',
                'queue_length': len(p.construction_queue),
                'building_count': 0,
                'available_slots': 0,
                'categories': {}
            }
            
            # Calculate slots
            if hasattr(p, 'provinces') and p.provinces:
                for node in p.provinces:
                    total_slots += node.building_slots
                    used_slots += len(node.buildings)
                    planet_data['building_count'] += len(node.buildings)
                    planet_data['available_slots'] += node.building_slots - len(node.buildings)
                    
                    # Count queue items for this node
                    node_queue_items = sum(1 for q in p.construction_queue if q.get("node_id") == node.id)
                    total_queue_items += node_queue_items
            else:
                total_slots += p.building_slots
                used_slots += len(p.buildings)
                planet_data['building_count'] = len(p.buildings)
                planet_data['available_slots'] = p.building_slots - len(p.buildings)
                total_queue_items += len(p.construction_queue)
            
            # Categorize queue items
            planet_categories = {"Economy": 0, "Military": 0, "Research": 0, "Infrastructure": 0, "Orbital": 0}
            for item in p.construction_queue:
                b_id = item.get("building_id")
                if b_id:
                    category = get_building_category(b_id)
                    queue_by_category[category] += 1
                    planet_categories[category] += 1
                    
                    # Check for orbital buildings
                    b_data = get_building_database().get(b_id, {})
                    if 'naval_slots' in b_data or 'Unlocks Space Ship Construction' in b_data.get('effects', {}).get('description', ''):
                        queue_by_category['Orbital'] += 1
                        planet_categories['Orbital'] += 1
            
            planet_data['categories'] = planet_categories
            queue_by_planet.append(planet_data)
            
            # Check for stalled/blocked queues
            if len(p.construction_queue) > 0:
                # Check if faction can afford next item
                if self.engine.faction_manager.get_faction(faction):
                    faction_obj = self.engine.faction_manager.get_faction(faction)
                    next_item = p.construction_queue[0]
                    next_cost = get_building_database().get(next_item.get("building_id"), {}).get("cost", 0)
                    if next_cost > 0 and faction_obj.requisition < next_cost:
                        blocked_queues += 1
        
        idle_slots = max(0, total_slots - used_slots - total_queue_items)
        queue_efficiency = 1.0 - (idle_slots / total_slots) if total_slots > 0 else 1.0
        
        # Track queue history
        if faction not in self._queue_history:
            self._queue_history[faction] = []
        
        self._queue_history[faction].append({
            'turn': turn,
            'total_slots': total_slots,
            'used_slots': used_slots,
            'queue_items': total_queue_items,
            'idle_slots': idle_slots,
            'efficiency': queue_efficiency
        })
        
        # Keep only last 50 turns of history
        if len(self._queue_history[faction]) > 50:
            self._queue_history[faction] = self._queue_history[faction][-50:]
        
        # Calculate trends
        avg_efficiency = sum(h['efficiency'] for h in self._queue_history[faction]) / len(self._queue_history[faction])
        efficiency_trend = queue_efficiency - avg_efficiency if len(self._queue_history[faction]) > 1 else 0
        
        event_data = {
            'faction': faction,
            'turn': turn,
            'total_slots': total_slots,
            'used_slots': used_slots,
            'queue_items': total_queue_items,
            'idle_slots': idle_slots,
            'queue_efficiency': queue_efficiency,
            'avg_efficiency': avg_efficiency,
            'efficiency_trend': efficiency_trend,
            'queue_by_category': queue_by_category,
            'queue_by_planet': queue_by_planet,
            'blocked_queues': blocked_queues,
            'stalled_queues': stalled_queues,
            'total_planets': len(owned_planets)
        }
        
        self.engine.telemetry.log_event(EventCategory.CONSTRUCTION, 'queue_analysis', event_data)

    def _log_skip_reason(self, faction: str, reason: str, context: Dict[str, Any] = None):
        """Logs why construction was skipped for a faction."""
        if self.engine.telemetry:
            self.engine.telemetry.log_event(
                EventCategory.CONSTRUCTION,
                "construction_skip_reason",
                {
                    "reason": reason, 
                    "context": context or {}
                },
                turn=self.engine.turn_counter,
                faction=faction
            )

    def process_construction_cycle(self, f_name: str, faction_mgr: 'Faction', owned_planets: List['Planet'], budget: int, mode: str) -> int:
        # PURE INSOLVENCY CHECK - STOP ALL SPENDING
        # Exception: Allow construction in RECOVERY mode (for economic buildings)
        if faction_mgr.requisition < 0 and mode != "RECOVERY":
            self._log_skip_reason(f_name, "insolvency", {"requisition": faction_mgr.requisition})
            return 0
            
        spent = 0

        working_budget = budget
        if working_budget < bal.CONST_EMERGENCY_BUDGET_THRESHOLD and faction_mgr.requisition > bal.CONST_EMERGENCY_BUDGET_THRESHOLD:
            working_budget = bal.CONST_EMERGENCY_BUDGET_THRESHOLD
            
        for p in owned_planets:
            if spent >= working_budget and faction_mgr.requisition < bal.CONST_EMERGENCY_BUDGET_THRESHOLD: 
                break 
                
            # Allow multi-build if in Total War OR if we are wealthy (Deep Pockets)
            max_builds = 1
            if mode == "TOTAL_WAR" or faction_mgr.requisition > 5000:
                max_builds = 99

            build_iter = 0
            while build_iter < max_builds:
                current_cap = working_budget - spent
                # Ensure high priority projects can tap into reserved funds if wealthy
                if faction_mgr.requisition > bal.CONST_HIGH_PRIORITY_THRESHOLD:
                    current_cap = max(current_cap, bal.CONST_HIGH_PRIORITY_THRESHOLD)
                
                res = self._process_planet_construction(p, f_name, faction_mgr, current_cap, mode)
                total_cost, budget_cost = res if isinstance(res, tuple) else (res, res if res > 0 else 0)
                
                if total_cost == 0: 
                    break
                    
                spent += budget_cost # Only count budget cost against working_budget
                build_iter += 1

        # Phase 14: Starbase Construction (Use remaining budget)
        # Pre-compute fleet locations for O(1) checks in starbase logic
        fleet_locations = {}
        for fleet in self.engine.fleets:
            if fleet.faction == f_name and not fleet.is_destroyed:
                 # If multiple fleets at same node, just keep one (sufficient for presence check)
                 fleet_locations[fleet.location] = fleet
                 
        spent += self._process_starbase_construction(f_name, faction_mgr, owned_planets, working_budget - spent, fleet_locations)

        # Track idle construction slots and queue efficiency
        if self.engine.telemetry:
            total_slots = 0
            used_slots = 0
            total_queue_items = 0
            building_type_counts = {"Economy": 0, "Military": 0, "Research": 0, "Infrastructure": 0}
            
            for p in owned_planets:
                # Calculate total slots
                if hasattr(p, 'provinces') and p.provinces:
                    for node in p.provinces:
                        total_slots += node.building_slots
                        used_slots += len(node.buildings)
                        total_queue_items += sum(1 for q in p.construction_queue if q.get("node_id") == node.id)
                else:
                    total_slots += p.building_slots
                    used_slots += len(p.buildings)
                    total_queue_items += len(p.construction_queue)
                
                # Categorize buildings
                # Categorize buildings (Track ACTIVE construction only)
                from src.core.constants import get_building_category
                
                # Check planet construction queue
                for item in p.construction_queue:
                    b_id = item.get("building_id")
                    if b_id:
                        category = get_building_category(b_id)
                        building_type_counts[category] += 1
            
            idle_slots = max(0, total_slots - used_slots - total_queue_items)
            queue_efficiency = 1.0 - (idle_slots / total_slots) if total_slots > 0 else 1.0
            
            # Record metrics
            # If there is ANY construction, record it broken down by type
            # If NO construction but we have activity/idleness to report, record as "None"
            
            has_construction = sum(building_type_counts.values()) > 0
            
            if has_construction:
                for building_type, count in building_type_counts.items():
                    if count > 0:
                        self.engine.telemetry.metrics.record_construction_activity(
                            f_name,
                            building_type,
                            idle_slots,
                            queue_efficiency
                        )
            elif idle_slots > 0 or total_slots > 0:
                # Log idle state even if no construction
                self.engine.telemetry.metrics.record_construction_activity(
                    f_name,
                    "None",
                    idle_slots,
                    queue_efficiency
                )
        
        # Log construction queue analysis
        self._log_construction_queue_analysis(f_name, owned_planets)
        
        return spent

    def _process_planet_construction(self, p: 'Planet', faction_key: str, faction_mgr: 'Faction', remaining_budget: int, mode: str) -> int:
        total_slots = 0
        built_count = 0
        if hasattr(p, 'provinces') and p.provinces:
            for node in p.provinces:
                total_slots += node.building_slots
                built_count += len(node.buildings) + sum(1 for q in p.construction_queue if q.get("node_id") == node.id)
        else:
            total_slots = p.building_slots
            built_count = len(p.buildings) + len(p.construction_queue)
        
        # Pre-calculate existing buildings across all nodes
        existing_buildings = list(p.buildings)
        if hasattr(p, 'provinces') and p.provinces:
            for node in p.provinces:
                existing_buildings.extend(node.buildings)

        # [FIX] Include queued buildings to prevent infinite duplicate queuing
        for item in p.construction_queue:
            if "building_id" in item:
                existing_buildings.append(item["building_id"])

        # Upgrade Check
        if hasattr(p, 'provinces') and p.provinces:
            for node in p.provinces:
                for b_id in node.buildings:
                    b_data = get_building_database().get(b_id)
                    upgrade_target = b_data.get("upgrade_to") if b_data else None
                    
                    if upgrade_target and upgrade_target in get_building_database():
                        up_data = get_building_database().get(upgrade_target)
                        if not up_data: continue
                        
                        req_techs = up_data.get("prerequisites", [])
                        has_tech = all(faction_mgr.has_tech(t) for t in req_techs)
                        
                        char_cost = up_data.get("cost", 1000)
                        cost = int(char_cost * faction_mgr.get_modifier("building_cost_mult", 1.0))
                        
                        if has_tech and faction_mgr.can_afford(cost) and cost <= remaining_budget:
                            node.buildings.remove(b_id)
                            task = {"id": upgrade_target, "turns_left": up_data.get("turns", 2), "node_id": node.id}
                            p.construction_queue.append(task)
                            faction_mgr.deduct_cost(cost)
                            faction_mgr.track_construction(cost)
                            
                            # Telemetry for Building Upgrade Event
                            self._log_building_upgrade_event(faction_key, p, b_id, upgrade_target, cost, up_data.get("turns", 2))
                            
                            # Telemetry for Expenses
                            if self.engine.telemetry:
                                self.engine.telemetry.record_resource_spend(
                                    faction_key,
                                    cost,
                                    category="Construction",
                                    source_planet=p.name
                                )

                            if self.engine.logger:
                                self.engine.logger.economy(f"[UPGRADE] {p.owner} upgrading {b_id} -> {upgrade_target} on {p.name}")
                            return cost, cost
        else:
            for b_id in list(p.buildings):
                b_data = get_building_database().get(b_id)
                upgrade_target = b_data.get("upgrade_to") if b_data else None
                
                if upgrade_target and upgrade_target in get_building_database():
                     up_data = get_building_database().get(upgrade_target)
                     if not up_data: continue
                     
                     req_techs = up_data.get("prerequisites", [])
                     has_tech = all(faction_mgr.has_tech(t) for t in req_techs)
                     base_cost = up_data.get("cost", 1000)
                     cost = int(base_cost * faction_mgr.get_modifier("building_cost_mult", 1.0))
                     
                     if has_tech and faction_mgr.can_afford(cost) and cost <= remaining_budget:
                         p.buildings.remove(b_id)
                         task = {"id": upgrade_target, "turns_left": up_data.get("turns", 2)}
                         p.construction_queue.append(task)
                         faction_mgr.deduct_cost(cost)
                         faction_mgr.track_construction(cost)
                         
                         # Telemetry for Building Upgrade Event
                         self._log_building_upgrade_event(faction_key, p, b_id, upgrade_target, cost, up_data.get("turns", 2))
                         
                         # Telemetry for Expenses
                         if self.engine.telemetry:
                             self.engine.telemetry.record_resource_spend(
                                 faction_key,
                                 cost,
                                 category="Construction",
                                 source_planet=p.name
                             )

                         if self.engine.logger:
                             self.engine.logger.economy(f"[UPGRADE] {p.owner} upgrading {b_id} -> {upgrade_target} on {p.name}")
                         return cost, cost

        if built_count >= total_slots:
            return 0
            
        possible_buildings = []
        for bid, data in get_building_database().items():
            b_faction = data.get("faction") or "All"
            if b_faction in ["All", "Global", "Neutral"] or b_faction == faction_key or faction_key.startswith(b_faction):
                possible_buildings.append(bid)
                
        if not possible_buildings:
            return 0
            
        affordable_buildings = []
        # We need the node we are targeting to check its max_tier
        target_node = None
        if hasattr(p, 'provinces') and p.provinces:
            # Enforce 4-Hex Spacing Rule
            existing_cities = [n for n in p.provinces if len(n.buildings) > 0]
            
            for node in p.provinces:
                # Basic Slot Check
                if len(node.buildings) + sum(1 for q in p.construction_queue if q.get("node_id") == node.id) >= node.building_slots:
                     continue

                # Rule Check: Valid City Location?
                if len(node.buildings) > 0:
                     # Existing city expansion is always allowed regardless of terrain
                     target_node = node
                     break
                
                # New settlement restrictions
                if getattr(node, 'terrain_type', None) in ["Mountain", "Water"]:
                     continue
                
                is_valid_loc = True
                for city in existing_cities:
                     if hasattr(city, 'hex_coords') and hasattr(node, 'hex_coords'):
                          dist = getattr(city.hex_coords, 'distance', lambda x: 999)(node.hex_coords)
                          if dist < 4:
                               is_valid_loc = False
                               break
                
                if is_valid_loc:
                     target_node = node
                     break
            
            # If it's a hex planet and we couldn't find a valid target node, abort construction
            if not target_node:
                return 0, 0
        
        node_max_tier = target_node.max_tier if target_node else 1

        for c in possible_buildings:
            b_data = get_building_database().get(c, {})
            if b_data.get("faction") == "Global":
                continue
                
            # Node Tier Constraint
            # [FIX] Orbital buildings ignore ground node tier limits
            is_orbital = False
            desc = b_data.get("effects", {}).get("description", "")
            b_name = b_data.get("name", "")
            if "Unlocks Space Ship Construction" in desc or b_data.get("naval_slots", 0) > 0:
                is_orbital = True
            elif any(keyword in b_name for keyword in ["Shipyard", "Station", "Dock", "Orbital", "Void"]):
                is_orbital = True

            if not is_orbital and b_data.get("tier", 1) > node_max_tier:
                continue

            # Tech Constraint
            prereqs = b_data.get("prerequisites", [])
            if prereqs and not all(faction_mgr.has_tech(t) for t in prereqs):
                continue

            base_cost = b_data.get("cost", 1000)
            cost = int(base_cost * faction_mgr.get_modifier("building_cost_mult", 1.0))
            if faction_mgr.can_afford(cost):
                # Filter Duplicates: Don't add if already on planet (unless it's an economic building)
                cat = get_building_category(c)
                if cat in ["Military", "Research"] and c in existing_buildings:
                    continue
                affordable_buildings.append(c)
        
        candidates = affordable_buildings if affordable_buildings else []
        
        is_crisis = mode in ["CRISIS", "RECOVERY"]
        
        # Dynamic Income Building Detection
        income_buildings = []
        military_starters = [] # Re-populating dynamic military too
        
        for cand in candidates:
            b_data = get_building_database().get(cand, {})
            eff = b_data.get("effects", {}).get("description", "")
            
            # Income / Mines
            if "Requisition" in eff or "Mining" in eff or "Trade" in eff or "tax" in eff.lower():
                income_buildings.append(cand)
                
            # Military Starters (Barracks equivalents from effect)
            if "Rank for" in eff or "Garrison" in eff or "unlocks" in b_data or "Unlocks" in eff:
                 military_starters.append(cand)

        # Pre-calculate existing buildings across all nodes
        existing_buildings = list(p.buildings)
        if hasattr(p, 'provinces') and p.provinces:
            for node in p.provinces:
                existing_buildings.extend(node.buildings)
        planetside_count = len(existing_buildings)

        # Ensure we have at least defaults if parsing fails (fallback)
        if not military_starters:
             military_starters = ["Barracks", "PDF Barracks", "Bunker Network"]

        # DEBUG: New Colony Diagnosis
        if planetside_count < 2 and faction_mgr.requisition > 20000:
             with open("debug_construction.txt", "a") as f:
                 f.write(f"DEBUG_NEW_COLONY: {p.name} ({p.owner}) Candidates: {len(candidates)}\n")
                 f.write(f"  Income BPs: {len(income_buildings)} Military Starters: {len(military_starters)}\n")
                 f.write(f"  Sample Cand: {candidates[:5]}\n")
        
        target_b = None
        decision_rationale = "No Candidate Found"
        
        # --- PHASE 0: COLONIZATION STARTER PACK ---
        
        # 1. Resource Priority (If < 1 resource building)
        has_resource = any(b in existing_buildings for b in income_buildings)
        if mode == "EXPANSION" and not has_resource:
             res_opts = [b for b in candidates if b in income_buildings]
             if res_opts:
                 res_opts.sort()
                 # Only prioritize if we are relatively safe or very poor
                 if not hasattr(p, 'is_sieged') or not p.is_sieged:
                     target_b = get_stream("economy").choice(res_opts)
                     decision_rationale = "Colonization Protocol (Resource)"
                     if self.engine.logger: self.engine.logger.economy(f"[CONSTRUCTION] New Colony Protocol (Resource) on {p.name}: {target_b}")

        # 2. Military Priority (If < 1 military building and we have resources or skipped resource)
        if not target_b and not any(b in existing_buildings for b in military_starters):
             starters_for_me = [b for b in candidates if b in military_starters]
             if starters_for_me: 
                 starters_for_me.sort()
                 target_b = get_stream("economy").choice(starters_for_me)
                 decision_rationale = "Colonization Protocol (Military)"
                 if self.engine.logger: self.engine.logger.economy(f"[CONSTRUCTION] New Colony Protocol (Military) on {p.name}: {target_b}")
        # ------------------------------------------

        # Phase 1: Ensure at least ONE military starter exists (Redundant backup)
        if not any(b in existing_buildings for b in military_starters):
             starters_for_me = [b for b in candidates if b in military_starters]
             if starters_for_me: 
                 starters_for_me.sort()
                 target_b = get_stream("economy").choice(starters_for_me)
                 decision_rationale = "Military Baseline (Defense)"
        
        navy_infra = ["Shipyard", "Orbital Dock", "Deep Space Foundry", "Raider Drydock", "Air Caste Dock"]
        
        # Phase 2: If wealthy, push for Navy Infra or MORE military
        # Phase 2: If wealthy, push for Navy Infra or MORE military
        if not target_b:
             # Identify Navy Infra dynamically
             navy_candidates = []
             for b in candidates:
                 if b in navy_infra and b not in existing_buildings:
                     navy_candidates.append(b)
                 else:
                     # Dynamic check
                     b_data = get_building_database().get(b, {})
                     eff = b_data.get("effects", {}).get("description", "")
                     if ("Unlocks Space Ship Construction" in eff or "shipyard" in eff.lower()) and b not in existing_buildings:
                         navy_candidates.append(b)
             
             if navy_candidates: 
                 navy_candidates.sort()
                 target_b = get_stream("economy").choice(navy_candidates)
                 decision_rationale = "Navy Infrastructure Expansion"
             
             # If still no target and we are STUPID rich, build another military building if slots allow
             if not target_b and faction_mgr.requisition > 50000:
                  mil_opts = [b for b in candidates if b in military_starters]
                  # Allow duplicates if many slots
                  if mil_opts and total_slots > 4:
                       mil_opts.sort()
                       target_b = get_stream("economy").choice(mil_opts)
                       decision_rationale = "Wealth Overflow (Military)"
        
        if not target_b and is_crisis:
            income_opts = [b for b in candidates if b in income_buildings]
            if income_opts:
                income_opts.sort()
                target_b = get_stream("economy").choice(income_opts)
                decision_rationale = "Crisis Recovery (Economic)"
                
        # Phase 4: Research Drive (Batch 13)
        # If RP income is 0 or very low (< 50), prioritize research if affordable
        # Also if we are rich (> 10k Req), build more research
        current_rp = getattr(faction_mgr, 'research_income', 0)
        should_boost_tech = current_rp < 50 or faction_mgr.requisition > 10000
        
        if not target_b and should_boost_tech:
            research_cands = []
            for b_id in candidates:
                b_data = get_building_database().get(b_id, {})
                cat = get_building_category(b_id)
                # Check category or output
                if cat == "Research" or "research_output" in b_data:
                    research_cands.append(b_id)
                    
            if research_cands:
                 # Filter: Don't spam if we already have one on this planet and slots are tight?
                 # For now, just build if valid
                 research_cands.sort()
                 target_b = get_stream("economy").choice(research_cands)
        
        if not target_b and candidates:
            # [Phase 1] Planet Specialization Logic
            # Filter candidates based on Role (CORE vs FRONTIER)
            
            role = getattr(p, 'role', 'CORE') # Default to CORE
            
            # Define Priorities
            # CORE: Economy, Research, Navy, Shipyards
            # FRONTIER: Defense, Military, Repairs, Bunkers
            
            def get_role_score(b_id):
                score = 0
                cat = get_building_category(b_id)
                b_data = get_building_database().get(b_id, {})
                eff = b_data.get("effects", {}).get("description", "")
                
                if role == "CORE":
                    if cat in ["Economy", "Research"]: score += 10
                    if "shipyard" in eff.lower() or "orbital" in eff.lower(): score += 5
                    if cat == "Defense": score -= 5 # Core worlds don't need heavy bunkers usually
                    
                elif role == "FRONTIER":
                    if cat == "Defense": score += 15
                    if "repair" in eff.lower() or "garrison" in eff.lower(): score += 10
                    if cat == "Research": score -= 10 # Risky to put labs on front line
                    if cat == "Economy": score -= 2
                    
                return score
            
            # Sort candidates by score + mild randomness
            random_stream = get_stream("economy")
            scored_opts = []
            for c in candidates:
                score = get_role_score(c)
                scored_opts.append((c, score))
            
            scored_opts.sort(key=lambda x: x[1] + random_stream.random() * 5, reverse=True)
            
            # Pick top 3 weighted
            top_candidates = [opt[0] for opt in scored_opts[:3]]
            target_b = random_stream.choice(top_candidates) if top_candidates else scored_opts[0][0]
            decision_rationale = f"Planet Specialization ({role})"
            
        # [PHASE 6] Decision Logging ($DEEP_TRACER)
        if target_b and self.decision_logger:
             # Prep considered options for logging
             options_considered = []
             # Collect at least 3 interesting ones if they exist
             logged_count = 0
             if 'scored_opts' in locals():
                  for b_id, score in scored_opts[:3]:
                       options_considered.append({
                           "action": f"BUILD:{b_id}",
                           "score": score,
                           "rationale": f"Role Match ({role})"
                       })
             else:
                  # If we picked via a specific Phase (Resource/Military priority), just log that one
                  options_considered.append({
                      "action": f"BUILD:{target_b}",
                      "score": 1.0,
                      "rationale": decision_rationale
                  })

             self.decision_logger.log_decision(
                 "PRODUCTION",
                 p.owner,
                 {
                     "planet": p.name,
                     "mode": mode,
                     "budget": remaining_budget,
                     "requisition": faction_mgr.requisition,
                     "slots_info": f"{built_count}/{total_slots}",
                     "plan_id": getattr(faction_mgr, 'strategic_context', {}).get("plan_id"),
                     "root_goal": getattr(faction_mgr, 'strategic_context', {}).get("root_goal")
                 },
                 options_considered,
                 f"BUILD:{target_b}",
                 "Selected"
             )
            
        db_entry = get_building_database().get(target_b, {})
        cost = db_entry.get("cost", 1000)
        
        # Spending Logic with Starter Exception
        allowed_override = (
            target_b in military_starters 
            and faction_mgr.can_afford(cost) 
            and faction_mgr.requisition > cost * 2.0 # Ensure we don't go broke
        )


        # SUSTAINABILITY CHECK: Prevent Death Spiral
        # If we are running a deficit or this building triggers one, BLOCK non-economic buildings
        econ_cache = self.engine.economy_manager.faction_econ_cache.get(faction_key, {})
        if econ_cache:
            income = econ_cache.get("income", 0)
            upkeep = econ_cache.get("total_upkeep", 0)
            net_income = income - upkeep
            
            new_upkeep = db_entry.get("maintenance", 0)
            
            # Allow military buildings ONLY if we are rich (buffer > 5000) despite deficit (e.g. wart chest)
            # otherwise if (Net - New) < 0, restrict to Economy only
            if (net_income - new_upkeep) < 0 and faction_mgr.requisition < 5000:
                 cat = get_building_category(target_b)
                 # Check explicitly for Requisition output in data or description
                 is_economic = (
                     cat == "Economy" 
                     or "requisition_output" in db_entry 
                     or "tax" in db_entry.get("effects", {}).get("description", "").lower()
                     or "income" in db_entry.get("effects", {}).get("description", "").lower()
                 )
                 
                 if not is_economic:
                     # Soft Rejection
                     return 0, 0

        if (faction_mgr.can_afford(cost) and cost <= remaining_budget) or allowed_override:
             override_msg = " (Starter Priority)" if (allowed_override and cost > remaining_budget) else ""
             if faction_mgr.construct_building(p, target_b):
                self.engine.faction_reporter.log_event(p.owner, "construction", f"Started constructing {target_b} on {p.name}{override_msg}")
                if self.engine.logger:
                    self.engine.logger.economy(f"[BUILD] {p.owner} developing {p.name}: {target_b} (Mode: {mode}){override_msg}")
                self.engine.telemetry.log_event(
                    EventCategory.CONSTRUCTION,
                    "building_started",
                    {
                        "building_id": target_b, 
                        "building_type": get_building_category(target_b),
                        "building": target_b, 
                        "planet": p.name
                    },
                    turn=self.engine.turn_counter,
                    faction=p.owner
                )
                
                # Telemetry for Expenses (Resource Transactions)
                self.engine.telemetry.record_resource_spend(
                    p.owner,
                    cost,
                    category="Construction",
                    source_planet=p.name
                )
                
                # Assign to node if applicable
                if target_node:
                    p.construction_queue[-1]["node_id"] = target_node.id
                    
                # FIX: Deduct Cost!
                faction_mgr.deduct_cost(cost)
                faction_mgr.track_construction(cost)

                # MECHANICS HOOK
                if hasattr(self.engine, 'mechanics_engine'):
                     context = {"faction": faction_mgr, "planet": p, "building": target_b}
                     self.engine.mechanics_engine.apply_mechanics(p.owner, "on_building_constructed", context)
                     
                budget_deducted = cost if not (allowed_override and cost > remaining_budget) else 0
                return cost, budget_deducted
        elif mode in ["EXPANSION", "CONSOLIDATION", "DEVELOPMENT", "BOOM"] and faction_mgr.can_afford(cost) and faction_mgr.requisition > 3000:
             if faction_mgr.construct_building(p, target_b):
                self.engine.faction_reporter.log_event(p.owner, "construction", f"Started constructing {target_b} on {p.name} (Stockpile Fund)")
                if self.engine.logger:
                    self.engine.logger.economy(f"[BUILD] {p.owner} developing {p.name}: {target_b} (Stockpile Spending)")
                self.engine.telemetry.log_event(
                    EventCategory.CONSTRUCTION,
                    "building_started",
                    {
                        "building_id": target_b, 
                        "building_type": get_building_category(target_b),
                        "building": target_b, 
                        "planet": p.name, 
                        "fund": "stockpile"
                    },
                    turn=self.engine.turn_counter,
                    faction=p.owner
                )
                
                # Telemetry for Expenses (Resource Transactions)
                self.engine.telemetry.record_resource_spend(
                    p.owner,
                    cost,
                    category="Construction",
                    source_planet=p.name
                )
                # Assign to node if applicable
                if target_node:
                    p.construction_queue[-1]["node_id"] = target_node.id
                return cost, 0
                
        else:
             pass
        return 0, 0

    def process_queues_for_faction(self, f_name: str) -> None:
        """Helper to process queues for all owned planets."""
        owned_planets = self.engine.planets_by_faction.get(f_name, [])
        for p in owned_planets:
            p.process_queue(self.engine)

    def _is_strategic_system(self, system: 'StarSystem', faction_mgr: 'Faction', owned_planets: List['Planet']) -> bool:
        """Determines if a system is worth a Starbase investment."""
        # 1. Is it the Capital?
        for p in owned_planets:
            if p.system == system and p.name == faction_mgr.home_planet_name:
                return True
                
        # 2. Is it a Gateway System? (FluxPoint/Portal)
        gateways = [n for n in system.nodes if n.type in ["FluxPoint", "Portal"]]
        if gateways:
            # If it's a hub (connects to many paths), it's a primary choke
            for g in gateways:
                # Check degree (connections to other nodes)
                # Gateways usually have 1 connection to the system and 1+ connections to other systems.
                # If it's a major junction (3+ connections total), it's a vital choke.
                if len(getattr(g, 'edges', [])) >= 3:
                    return True
            return True
        
        # 3. Is it a Border System? (Presence on Frontier)
        # Simplified: If any node connects to a system NOT owned by us.
        # This is high-value for defense stations.
        for node in system.nodes:
            for edge in getattr(node, 'edges', []):
                target_node = edge.target
                if hasattr(target_node, 'system') and target_node.system != system:
                    # Choke Point identified (Bridge to another system)
                    return True

        # 4. Is it a High-Value Economy (2+ Planets)?
        p_count = sum(1 for p in owned_planets if p.system == system)
        if p_count >= 2:
            return True
            
        return False

    def _process_starbase_construction(self, f_name: str, faction_mgr: 'Faction', owned_planets: List['Planet'], remaining_budget: int, fleet_locations: Dict[Any, Any] = None) -> int:
        """
        [Phase 14] Starbase Construction Logic.
        AI attempts to build or upgrade Starbases in owned systems.
        Prioritizes Capital > Choke Points > Border Systems.
        """
        from src.models.starbase import Starbase
        
        spent = 0
        if not fleet_locations: fleet_locations = {}
        # Loosen budget restrictions if faction is very wealthy
        min_exec_budget = 1000
        if faction_mgr.requisition > 20000:
            min_exec_budget = 500
            
        if remaining_budget < min_exec_budget: return 0
        
        # 1. Identify Candidate Systems
        candidate_systems = set()
        # Add systems where we own planets
        for p in owned_planets:
            if hasattr(p, 'system'):
                candidate_systems.add(p.system)
        
        # Add systems that are strategic gateways/chokes (even if no planets owned)
        for system in self.engine.systems:
            if any(n.type in ["FluxPoint", "Portal"] for n in system.nodes):
                # We consider it a candidate if it's "close" to our territory 
                # or if we already have a presence there.
                # For now, let's include ALL gateway systems to allow expansion.
                candidate_systems.add(system)
                
        # 2. Iterate and Evaluate
        candidates = list(candidate_systems)
        # Deterministic shuffle
        get_stream("economy").shuffle(candidates)
        
        for system in candidates:
            if spent >= remaining_budget: 
                break
            
            # Evaluate EACH planet for a potential starbase
            for p in system.planets:
                if p.owner != f_name: continue
                if spent >= remaining_budget: break
                
                target_node = getattr(p, 'node_reference', None)
                if not target_node: continue
                
                # OPTIMIZATION: Use pre-computed map instead of O(N) linear scan
                friendly_fleet = fleet_locations.get(target_node)
                
                # Planet supports own construction
                has_support = True
                
                if p.starbase:
                    # Upgrade Logic
                    sb = p.starbase
                    if sb.tier >= 5: continue
                    
                    cost = 1000 * (sb.tier + 1)
                    if faction_mgr.can_afford(cost) and cost <= (remaining_budget - spent):
                        # Tech check...
                        has_tech = True
                        if sb.tier == 1: has_tech = any("Deep Space Defense" in t for t in faction_mgr.unlocked_techs)
                        elif sb.tier == 2: has_tech = any("Fortress Doctrine" in t for t in faction_mgr.unlocked_techs)
                        elif sb.tier == 3: has_tech = any("Void Citadels" in t for t in faction_mgr.unlocked_techs)
                        
                        # SUSTAINABILITY CHECK (Starbase)
                        econ_cache = self.engine.economy_manager.faction_econ_cache.get(f_name, {})
                        if econ_cache:
                             income = econ_cache.get("income", 0)
                             upkeep = econ_cache.get("total_upkeep", 0)
                             net = income - upkeep
                             # Starbases are huge drains. Block if unstable unless VERY rich.
                             if net < 0 and faction_mgr.requisition < 10000:
                                 continue
                        
                        if has_tech:
                            if sb.upgrade():
                                faction_mgr.requisition -= cost
                                spent += cost
                                self.engine.faction_reporter.log_event(f_name, "construction", f"Upgraded Starbase at {p.name} to Tier {sb.tier}")
                                if self.engine.logger:
                                    self.engine.logger.economy(f"[STARBASE] {f_name} upgraded base at {p.name} to Tier {sb.tier} (-{cost}R)")
                                
                                # Log Telemetry
                                self._log_starbase_deployment(f_name, p.name, sb.tier, cost, "Upgraded", "completed")
                else:
                    # New Construction Logic
                    cost = 2000
                    if faction_mgr.can_afford(cost) and cost <= (remaining_budget - spent):
                         # SUSTAINABILITY CHECK (New Starbase)
                        econ_cache = self.engine.economy_manager.faction_econ_cache.get(f_name, {})
                        if econ_cache:
                             income = econ_cache.get("income", 0)
                             upkeep = econ_cache.get("total_upkeep", 0)
                             net = income - upkeep
                             if net < 0 and faction_mgr.requisition < 15000:
                                 continue

                        # Check for construction ship or local capability?
                        # For simplicity, we assume if we own the planet, we can build a starbase in orbit.
                        # AI DESIGN HOOK
                        designer = getattr(self.engine, 'design_service', None)
                        if not designer:
                            from src.services.ship_design_service import ShipDesignService
                            designer = ShipDesignService(self.ai_manager)
                        
                        design = designer.generate_starbase_design(f_name, 1) # Tier 1
                        
                        new_sb = Starbase(f"{p.name} Station", f_name, system, tier=1, 
                                         under_construction=True, design_data=design)
                        p.starbase = new_sb
                        system.starbases.append(new_sb)
                        
                        # Create Static Fleet
                        fid = f"SB_{p.name}_{f_name}"
                        engine_fleet = self.engine.create_fleet(f_name, target_node, units=[new_sb], fid=fid)
                        engine_fleet.is_scout = False
                        
                        faction_mgr.deduct_cost(cost)
                        faction_mgr.track_construction(cost)
                        spent += cost
                        if self.engine.logger:
                            self.engine.logger.economy(f"[CONSTRUCTION] {f_name} started Starbase at {p.name} (-{cost} Req)")
                            
                        # Log Telemetry
                        self._log_starbase_deployment(f_name, p.name, 1, cost, "New Construction", "started")
            
            # Additional logic for deep space nodes (FluxPoint/Portal/Asteroid/Nebula)
            # Find all nodes that are strategic but not planets
            strategic_nodes = [n for n in system.nodes if n.type in ["FluxPoint", "Portal", "AsteroidField", "Nebula"]]
            for node in strategic_nodes:
                if spent >= remaining_budget: break
                
                # Check for existing starbase/structure at this node
                # OPTIMIZATION: Iterate system.starbases (small list) instead of all engine fleets (huge list)
                existing_sb = None
                if hasattr(system, 'starbases'):
                    for sb in system.starbases:
                        if sb.is_destroyed: continue
                        # Check location via fleet reference
                        if sb.fleet and sb.fleet.location == node:
                            existing_sb = sb
                            break
                
                if existing_sb:
                    # Upgrade logic for node-based starbase
                    sb = existing_sb
                    if sb.faction != f_name: continue
                    
                    # Mining/Research Stations don't upgrade yet
                    if sb.unit_class != "Starbase": continue
                    
                    if sb.tier >= 5: continue
                    
                    cost = 1000 * (sb.tier + 1)
                    if faction_mgr.can_afford(cost) and cost <= (remaining_budget - spent) and faction_mgr.requisition > cost * 3.0:
                        # Tech check...
                        has_tech = True
                        if sb.tier == 1: has_tech = any("Deep Space Defense" in t for t in faction_mgr.unlocked_techs)
                        elif sb.tier == 2: has_tech = any("Fortress Doctrine" in t for t in faction_mgr.unlocked_techs)
                        elif sb.tier == 3: has_tech = any("Void Citadels" in t for t in faction_mgr.unlocked_techs)
                        if has_tech:
                            sb.upgrade()
                            faction_mgr.deduct_cost(cost)
                            spent += cost
                            # Log Telemetry
                            self._log_starbase_deployment(f_name, f"Deep Space {node.name}", sb.tier, cost, "Deep Space Upgrade", "completed")
                    continue
                
                # Need fleet support for new deep space SB
                # OPTIMIZATION: Use pre-computed map
                friendly_fleet = fleet_locations.get(node)
                if not friendly_fleet: continue
                
                # STRUCTURE DEFINITION
                struct_type = "Starbase"
                cost = 1000
                name_suffix = "Station"
                
                # Asteroid Mining Logic
                if node.type == "AsteroidField":
                    struct_type = "MiningStation"
                    cost = 500
                    name_suffix = "Mining Platform"
                
                # Nebula Research Logic
                elif node.type == "Nebula":
                    struct_type = "ResearchOutpost"
                    cost = 750
                    name_suffix = "Research Hub"

                # Listening Post Logic (Flux Nodes)
                elif node.type == "FluxPoint":
                    struct_type = "ListeningPost"
                    cost = 750
                    name_suffix = "Listening Post"
                
                if faction_mgr.can_afford(cost) and cost <= (remaining_budget - spent) and faction_mgr.requisition > (cost * 2.0):
                    # For mining stations, we want to expand aggressively if we have the budget
                    
                    # AI DESIGN HOOK
                    designer = getattr(self.engine, 'design_service', None)
                    if not designer:
                        from src.services.ship_design_service import ShipDesignService
                        designer = ShipDesignService(self.ai_manager)
                    
                    design = designer.generate_starbase_design(f_name, 1)
                    
                    new_struct = Starbase(f"{node.name} {name_suffix}", f_name, system, 
                                         tier=1, under_construction=True, design_data=design)
                    new_struct.unit_class = struct_type # Override class
                    
                    system.starbases.append(new_struct)
                    fid = f"STR_{node.id}_{f_name}"
                    self.engine.create_fleet(f_name, node, units=[new_struct], fid=fid)
                    faction_mgr.deduct_cost(cost)
                    spent += cost
                    if self.engine.logger:
                        self.engine.logger.economy(f"[CONSTRUCTION] {f_name} started {struct_type} at {node.name}")
                    # Log Telemetry
                    self._log_starbase_deployment(f_name, f"Deep Space {node.name}", 1, cost, "Deep Space New", "started")
        return spent

    def process_starbase_queues(self, f_name: str) -> None:
        """[Phase 18] Advances starbase construction if a fleet is present."""
        for system in self.engine.systems:
            for sb in system.starbases:
                if sb and sb.faction == f_name and sb.is_under_construction:
                    # Find the SB's location fleet to check the specific node
                    sb_fleet = next((f for f in self.engine.fleets if any(u == sb for u in f.units)), None)
                    if not sb_fleet: continue
                    
                    target_node = sb_fleet.location
                    
                    # Planet support check
                    is_owned_planet_node = False
                    if hasattr(target_node, 'type') and target_node.type == "Planet":
                        p_obj = target_node.metadata.get("object")
                        if p_obj and p_obj.owner == f_name:
                            is_owned_planet_node = True
                    
                    has_constructor = False
                    for f in self.engine.fleets:
                        if f.faction == f_name and f.location == target_node and not f.is_destroyed:
                            if any(getattr(u, 'unit_class', '') == 'constructor' for u in f.units):
                                has_constructor = True
                                break
                    
                    if has_constructor:
                        sb.turns_left -= 1
                        if sb.turns_left <= 0:
                            sb.finalize_construction()
                    else:
                        if self.engine.logger:
                            self.engine.logger.economy(f"[STATION] Construction stalled at {target_node.name} - No Construction Ship present.")

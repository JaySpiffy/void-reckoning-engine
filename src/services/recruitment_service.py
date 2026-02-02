import random
from typing import List, Optional, Tuple, TYPE_CHECKING, Any
from src.utils.telemetry_helper import TelemetryHelper
from src.reporting.telemetry import EventCategory
from src.models.fleet import Fleet
from src.models.army import ArmyGroup
from src.models.unit import Unit
from src.factories.unit_factory import UnitFactory
from src.core.constants import FLEET_COMMISSION_COST, FLEET_COMMISSION_THRESHOLD, get_building_database
from src.core import balance as bal


if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine
    from src.models.faction import Faction
    from src.models.planet import Planet

class RecruitmentService:
    """
    Handles operational logic for recruiting units and commissioning fleets.
    """
    def __init__(self, engine: 'CampaignEngine', rng: random.Random = None):
        self.engine = engine
        # self.rng replaced by RNGManager
        self.telemetry = TelemetryHelper(engine)

    def _log_skip_event(self, f_name: str, r_type: str, skipped: List[dict], caps: dict = None):
        """Logs aggregated recruitment skip reasons."""
        if not self.engine.telemetry or not skipped: return
        
        self.engine.telemetry.log_event(
            EventCategory.ECONOMY,
            "recruitment_skip_reason",
            {
                "recruitment_type": r_type,
                "skipped_units": skipped,
                "sustainability_check_failed": caps.get("sustainability", False) if caps else False,
                "insolvency_check_failed": caps.get("insolvency", False) if caps else False,
                "cap_exceeded": caps.get("cap_type") if caps else None
            },
            turn=self.engine.turn_counter,
            faction=f_name
        )

    def process_fleet_commissioning(self, f_name: str, faction_mgr: 'Faction', owned_planets: List['Planet'], budget: int, mode: str = "EXPANSION") -> int:
        """
        Generic recruitment (Legacy/Fallback or explicit Commissioning).
        Currently maps to the 'Commission New Fleet' logic from EconomyManager.
        """
        spent = 0
        if not owned_planets: return 0
        
        # Check for invasions to prioritize defense
        all_threatened = [p for p in owned_planets if any(ag.faction != f_name for ag in p.armies if not ag.is_destroyed)]
        is_under_attack = len(all_threatened) > 0
        
        base_commission_cost = FLEET_COMMISSION_COST
        cost = int(base_commission_cost * faction_mgr.get_modifier("recruitment_cost_mult", 1.0))
        max_recruits = bal.RECRUIT_BATCH_SIZE_MAX 
        count = 0
        
        # Override Budget if Stockpile is HUGE
        # Phase 106: Disable override during CRISIS or RECOVERY to prevent debt-scrap-recruit death spiral
        # Phase 108: Harden - Stockpile override ONLY works if requisition > 0. 
        # Prevents "spending your way out of debt" which causes deep negative requisition.
        is_crisis = mode in ["CRISIS"]
        is_recovery = mode == "RECOVERY"
        
        stockpile_override = faction_mgr.requisition > (cost * bal.RECRUIT_STOCKPILE_OVERRIDE_MULT) and not is_crisis
        if faction_mgr.requisition <= 0:
            stockpile_override = False # Strictly forbid override if in debt
            
        # Early Exit: Hard Insolvency Check
        # EXCEPTION: If in RECOVERY mode, we allow spending ONLY if budget permits (Grants etc.) 
        # AND requisition is not deeply negative.
        if faction_mgr.requisition < FLEET_COMMISSION_THRESHOLD and not stockpile_override and not is_recovery:
            if self.engine.telemetry:
                 self.engine.telemetry.log_event(
                     EventCategory.ECONOMY,
                     "recruitment_skip_reason",
                     {
                         "reason": "insolvency", 
                         "service": "fleet",
                         "context": {"requisition": faction_mgr.requisition, "threshold": FLEET_COMMISSION_THRESHOLD}
                     },
                     turn=self.engine.turn_counter,
                     faction=f_name
                 )
            return 0
            
        recruited_fleets_count = 0
        
        while spent < budget and count < max_recruits:
            # Inline Check (Shadowing Protection)
            # Phase 108: Cannot recruit shell if requisition < 0 (must recover first)
            if faction_mgr.requisition < 0:
                break
                
            if faction_mgr.requisition < FLEET_COMMISSION_THRESHOLD and not stockpile_override and not is_recovery:
                break
                
            # Check Budget
            if (spent + cost) > budget and not stockpile_override:
                break
                
            # Smart AI: Sustainability Check (User Request)
            # Don't commission if projected upkeep exceeds 90% of income (Crash prevention)
            # (Unless in TOTAL_WAR mode)

            
            # 1. Choose Spawn Point
            # User Request: Prioritize growing fleets to MAX (100) before spamming small ones.
            # Check existing fleets for capacity
            existing_fleets = [f for f in self.engine.fleets_by_faction.get(f_name, []) if not f.is_destroyed]
            total_current = sum(len(f.units) for f in existing_fleets)
            total_capacity = len(existing_fleets) * self.engine.max_fleet_size
            
            # If we have fleets and they are less than 70% full, DON'T COMMISSION NEW ONES
            # Instead, let process_ship_production fill them up.
            # MAX_FLEET_SIZE based commissioning logic
            # If we have fleets and they are less than 70% full, usually DON'T COMMISSION NEW ONES
            # BUT if the fleet cap is massive (e.g. 400), a 20% full fleet (80 ships) is already a viable force.
            # We should check absolute numbers too.
            if existing_fleets and total_capacity > 0:
                fill_ratio = total_current / total_capacity
                
                # Dynamic Threshold: The larger the max_fleet_size, the lower the ratio needed to justify new fleets.
                # If max size is > 100, we accept 30% fill as "functional" to start a new one.
                threshold = 0.70
                if self.engine.max_fleet_size > 100:
                    threshold = 0.30
                if self.engine.max_fleet_size > 300:
                    threshold = 0.15
                    
                if fill_ratio < threshold and not is_under_attack:
                    # Exception: If we have very few fleets (e.g. < 3), allow commissioning to get presence
                    # Also exception: If we are WEALTHY, we can afford parallel tracks
                    # [BALANCE] Lowered threshold to 50x cost to encourage spending surplus
                    wealthy_override = faction_mgr.requisition > (cost * 50)
                    
                    if len(existing_fleets) >= 3 and not wealthy_override:
                        if self.engine.logger and count == 0: # Log once
                            self.engine.logger.economy(f"[SMART_AI] {f_name} skipping commission to reinforce existing fleets (Fill: {fill_ratio:.2f} < {threshold})")
                        return spent

            from src.utils.rng_manager import get_stream
            rng = get_stream("economy")
            
            if all_threatened:
                all_threatened.sort(key=lambda p: p.name)
                spawn_point = rng.choice(all_threatened)
            else:
                owned_planets.sort(key=lambda p: p.name)
                spawn_point = rng.choice(owned_planets)
            
            # Phase 17b: Node-Based Locking
            if getattr(spawn_point, 'is_sieged', False):
                # if f_name == "Hegemony" and self.engine.logger: self.engine.logger.economy(f"Cannot recruit at {spawn_point.name} - Node is SIEGED.")
                count += 1 
                continue

            faction_mgr.deduct_cost(cost)
            spent += cost
            self.engine.faction_reporter.log_event(f_name, "recruitment", f"Commissioned new fleet at {spawn_point.name}")
            
            # Telemetry for Expenses
            if self.engine.telemetry:
                self.engine.telemetry.record_resource_spend(
                    f_name,
                    cost,
                    category="Recruitment",
                    source_planet=spawn_point.name
                )
            
            # MECHANICS HOOK (Recruitment)
            if hasattr(self.engine, 'mechanics_engine'):
                context = {"faction": faction_mgr, "unit": None, "cost": cost} # Fleet shell commission
                self.engine.mechanics_engine.apply_mechanics(f_name, "on_unit_recruited", context)

            # Delegate to engine/asset_manager for ID and registration
            new_fleet = self.engine.create_fleet(f_name, spawn_point, fid=None)
            
            # Track Composition
            comp_counts = {}

            base_f = self._get_base_faction(f_name)
            if base_f in self.engine.unit_blueprints and self.engine.unit_blueprints[base_f]:
                bps = sorted(self.engine.unit_blueprints[base_f], key=lambda u: u.name)
                # Phase 9 Refactor: Increase initial fleet size from 5 to 12
                initial_size = 12
                # Reduce slightly if low budget? No, we rely on 'can_afford' check below.
                
                for _ in range(initial_size):
                    u = rng.choice(bps)
                    
                    # [FIX] Check affordability per unit to prevent massive overspend debt spiral
                    # Phase 108: Forbid unit recruitment if requisition < 0
                    if faction_mgr.requisition < 0 or (not faction_mgr.can_afford(u.cost) and not stockpile_override):
                        break
                        
                    new_fleet.add_unit(u)
                    
                    # [FIX] Deduct actual cost of the unit!
                    faction_mgr.deduct_cost(u.cost)
                    spent += u.cost
                    
                    faction_mgr.track_recruitment(u.cost, count=1)
                    comp_counts[u.name] = comp_counts.get(u.name, 0) + 1
                    
                recruited_fleets_count += 1
                    
                # Telemetry for Expenses (Fleet Reinforcement Units)
                if self.engine.telemetry:
                    self.engine.telemetry.record_resource_spend(
                        f_name,
                        u.cost,
                        category="Recruitment",
                        source_planet=spawn_point.name
                    )
            
            # Registration handled by create_fleet
            # self.engine.fleets.append(new_fleet)
            
            # Format Composition String
            comp_str = ", ".join([f"{v}x {k}" for k, v in comp_counts.items()])
            
            msg = f"[COMMISSION] {f_name} commissioned reinforcement fleet {new_fleet.id} at {spawn_point.name} ({comp_str})"
            if stockpile_override: msg += " (Stockpile Override)"
            if self.engine.logger:
                self.engine.logger.economy(msg)
            
            if is_under_attack and spawn_point not in all_threatened:
                target_planet = rng.choice(all_threatened)
                new_fleet.move_to(target_planet, engine=self.engine)
                if self.engine.logger:
                    self.engine.logger.economy(f"[REINFORCE] {new_fleet.id} heading to front-line at {target_planet.name}")
            
            self.engine.telemetry.log_event(
                EventCategory.ECONOMY,
                "fleet_commissioned",
                {"fleet_id": new_fleet.id, "location": spawn_point.name, "cost": cost, "override": stockpile_override, "composition": comp_counts},
                turn=self.engine.turn_counter,
                faction=f_name
            )
            count += 1
        return spent

    def _classify_ship_blueprint(self, bp) -> str:
        """Determines the class of a ship blueprint for composition purposes."""
        # Use explicit class if available
        if getattr(bp, "unit_class", None):
             return bp.unit_class
             
        tags = bp.abilities.get("Tags", []) if hasattr(bp, "abilities") else []
        name = bp.name.lower()
        
        if "Battleship" in tags or "Battleship" in name or "Titan" in tags:
            return "Battleship"
        elif "Grand Cruiser" in tags or "Cruiser" in tags or "Cruiser" in name:
             return "Cruiser"
        return "Escort"

    def _classify_army_blueprint(self, bp) -> str:
        """Determines the role of an army blueprint."""
        # Use explicit tactical roles if available
        roles = getattr(bp, "tactical_roles", [])
        if roles:
             if "Anti-Tank" in roles or "Armor" in roles: return "Armor"
             if "Artillery" in roles: return "Artillery"
             if "Titan" in roles: return "Titan"
             
        tags = bp.abilities.get("Tags", []) if hasattr(bp, "abilities") else []
        traits = getattr(bp, "traits", [])
        name = bp.name.lower()
        
        if "Titan" in tags or "Super-Heavy" in tags or bp.cost > 1000:
             return "Titan"
        if "Tank" in tags or "Vehicle" in tags or "Armor" in tags or "Monster" in tags:
             return "Armor"
        if "Artillery" in tags or "Ranged" in tags:
             return "Artillery"
        if "Scout" in traits or "Infiltrator" in tags:
             return "Scout"
             
        return "Infantry"

    def _select_blueprint_by_composition(self, available_bps, ratios, rng) -> Any:
        """Selects a blueprint based on desired composition ratios, handling unavailability."""
        # 1. Group Available Blueprints
        grouped = {}
        for bp in available_bps:
            # Detect if Ship or Army
            if getattr(bp, "is_ship", lambda: False)() or "Ship" in getattr(bp, "abilities", {}).get("Tags", []):
                cls = self._classify_ship_blueprint(bp)
            else:
                cls = self._classify_army_blueprint(bp)
                
            if cls not in grouped: grouped[cls] = []
            grouped[cls].append(bp)
            
        # 2. Filter Ratios to what is actually available
        valid_ratios = {k: v for k, v in ratios.items() if k in grouped and grouped[k]}
        
        if not valid_ratios:
             # Fallback: Just pick random
             return rng.choice(available_bps)
             
        # 3. Normalize
        total_weight = sum(valid_ratios.values())
        keys = list(valid_ratios.keys())
        probs = [valid_ratios[k] / total_weight for k in keys]
        
        # 4. Roll
        selected_class = rng.choices(keys, weights=probs, k=1)[0]
        return rng.choice(grouped[selected_class])


    def process_ship_production(self, f_name: str, faction_mgr: 'Faction', owned_planets: List['Planet'], budget: int, mode: str = "EXPANSION") -> int:
        """
        Phase 37: Naval Expansion
        Builds ships and reinforces fleets via queue.
        """
        spent = 0
        if not owned_planets: return 0
        
        # 1. Get Naval Blueprints (Refactored)
        available_bps = self._get_available_blueprints(f_name, faction_mgr)
        if not available_bps: return 0
        
        avg_cost = sum(u.cost for u in available_bps) // len(available_bps)
        
        # Phase 63: Dynamic Recruitment Cap (Industrial Saturation)
        infra_cap = bal.RECRUIT_NAVY_CAP_BASE 
        
        # Discover Navy Infrastructure dynamically
        db = get_building_database()
        
        skipped_log = []
        skip_caps = {}
        
        for p in owned_planets:
            p_buildings = list(p.buildings)
            if hasattr(p, 'provinces') and p.provinces:
                for node in p.provinces:
                    p_buildings.extend(node.buildings)
                    
            for b_id in p_buildings:
                if b_id in ["Orbital Dock", "Shipyard", "Deep Space Foundry", "Raider Drydock"]:
                    infra_cap += 2
                elif b_id in db:
                    b_data = db[b_id]
                    eff = b_data.get("effects", {}).get("description", "")
                    if "Unlocks Space Ship Construction" in eff or "shipyard" in eff.lower():
                        infra_cap += 2
                    elif "Naval Capacity" in eff:
                         infra_cap += 1
                            
        max_recruits = int(infra_cap * faction_mgr.navy_recruitment_mult)
        # High Surplus Logic (Phase 16: Nerfed 10x -> 2x)
        # [BALANCE] Restored to 4x for actual surplus spending
        is_wealthy = faction_mgr.requisition > (avg_cost * 50)
        if is_wealthy:
             max_recruits *= 4
        
        # Scaling limit based on max_fleet_size (allow building ~10% of a full fleet per turn if rich)
        # Instead of hard cap 20, use max(20, max_fleet_size * 0.1)
        scale_limit = max(20, self.engine.max_fleet_size // 10)
        
        # [BALANCE] If wealthy, allow bursting up to 50% of fleet size or 100 ships
        if is_wealthy:
            scale_limit = max(scale_limit, min(100, self.engine.max_fleet_size // 2))
            
        max_recruits = max(1, min(max_recruits, scale_limit))
        count = 0
        

        
        # Early Exit
        is_crisis = mode in ["CRISIS", "RECOVERY"]
        if faction_mgr.requisition < FLEET_COMMISSION_THRESHOLD and not is_crisis:
            self._log_skip_event(f_name, "navy", [], {"insolvency": True})
            return 0
            
        while count < max_recruits:
            is_crisis = mode in ["CRISIS", "RECOVERY"]
            # Phase 108: Hard block on production if in debt
            if faction_mgr.requisition < 0:
                break

            if (spent + avg_cost) > budget:
                # Debt Protection (Inline)
                if is_crisis or faction_mgr.requisition < bal.ECON_STOCKPILE_OVERRIDE_THRESHOLD:
                    skipped_log.append({"unit_id": "generic_ship", "skip_reason": "budget_exceeded", "cost": avg_cost, "available_budget": budget - spent})
                    break
            

                
            from src.utils.rng_manager import get_stream
            rng = get_stream("economy")
            
            # --- SMART COMPOSITION LOGIC ---
            # Desired Ratios (Baseline)
            navy_ratios = {
                "Battleship": 0.15,
                "Cruiser": 0.35,
                "Escort": 0.50
            }
            
            # Dynamic Tactics Adjustment (User Request)
            tactics = getattr(faction_mgr, "preferred_tactics", "STANDARD")
            
            if tactics == "SWARM":
                 navy_ratios["Escort"] += 0.30
                 navy_ratios["Cruiser"] -= 0.10
            elif tactics == "ELITE":
                 navy_ratios["Battleship"] += 0.20
                 navy_ratios["Cruiser"] += 0.10
                 navy_ratios["Escort"] -= 0.30
            elif tactics == "CARRIER": 
                 navy_ratios["Cruiser"] += 0.20 
                 
            # [PHASE 5] Procedural Ship Design Integration
            # Instead of picking from static blueprints, we decide a CLASS and DESIGN it.
            use_procedural = hasattr(self.engine, 'ai_manager') and self.engine.ai_manager
            bp = None
            
            if use_procedural:
                # CONSTRUCTOR PRIORITY
                if faction_mgr.get_constructor_count() < 1:
                    target_class = "Escort" # Use escort hull for constructor
                    target_role = "Constructor"
                else:
                    # 1. Pick Class based on Ratios
                    classes = list(navy_ratios.keys())
                    weights = [navy_ratios[k] for k in classes]
                    
                    target_class = rng.choices(classes, weights=weights, k=1)[0]
                    
                    # 2. Pick Role (Sub-selection)
                    target_role = "General"
                    
                    # [PHASE 24] Interdiction Logic
                    pref = getattr(faction_mgr, 'design_preference', 'BALANCED')
                    if pref == "INTERDICTION":
                         roll = rng.random()
                         if roll < 0.3: target_role = "Brawler"
                         elif roll < 0.6: target_role = "Sniper"
                         else: target_role = "General"
                    elif pref == "ANTI_SHIELD":
                         target_role = "Sniper"
                    elif pref == "ANTI_ARMOR":
                         target_role = "Brawler"
                    else:
                        roll = rng.random()
                        if roll < 0.3: target_role = "Brawler"
                        elif roll < 0.6: target_role = "Sniper"
                
                # 3. Generate Design
                try:
                    # [PHASE 5] Use central design service
                    designer = getattr(self.engine, 'design_service', None)
                    if not designer:
                        from src.services.ship_design_service import ShipDesignService
                        designer = ShipDesignService(self.engine.ai_manager)
                    
                    design_data = designer.generate_design(f_name, target_class, target_role)
                    
                    # 4. Inflate to Ship/Unit Object (Blueprint)
                    from src.models.unit import Ship
                    # Map stats to Ship constructor args
                    s_stats = design_data.get('stats', {})
                    
                    # Base Hull Stats (Simplification)
                    hull_map = {
                        "Escort": {"hp": 150, "armor": 10, "ma": 30, "md": 30, "shield": 50},
                        "Cruiser": {"hp": 500, "armor": 12, "ma": 40, "md": 20, "shield": 200},
                        "Battleship": {"hp": 1200, "armor": 14, "ma": 50, "md": 10, "shield": 500}
                    }
                    base = hull_map.get(target_class, hull_map["Escort"])
                    
                    bp = Ship(
                        name=design_data['name'],
                        ma=base['ma'], md=base['md'],
                        hp=base['hp'], armor=base['armor'],
                        damage=0, # Determined by components
                        abilities={"Tags": ["Ship", target_class]},
                        faction=f_name,
                        cost=design_data['cost'],
                        shield=base['shield'] + s_stats.get('shield', 0),
                        unit_class="constructor" if target_role == "Constructor" else target_class, 
                        components_data=design_data['components'] 
                    )
                except Exception as e:
                    if self.engine.logger: self.engine.logger.error(f"Design Gen Failed: {e}")
                    bp = None

            # Fallback to Legacy if Procedural Failed or Disabled
            if not bp:
                 bp = self._select_blueprint_by_composition(available_bps, navy_ratios, rng)
            # -------------------------------

            cost = int(bp.cost * faction_mgr.get_modifier("recruitment_cost_mult", 1.0))
            
            if not faction_mgr.can_afford(cost):
                skipped_log.append({"unit_id": bp.name, "skip_reason": "not_affordable", "cost": cost, "available_budget": faction_mgr.requisition})
                break 
                
            # 3. Choose Location / Starbase (Phase 16: Moved to Starbases)
            # [FIX] Phase 14: Use new colonies with shipyards too
            prod_stations = self._get_ship_production_sites(f_name, faction_mgr, owned_planets)
            
            # Phase 16: Filter for Starbases with available production slots
            # [FIX] Increased buffer from +2 to +20 to allow large batch queuing
            prod_stations = [s for s in prod_stations if len(s.unit_queue) < (s.naval_slots + 20)]
            
            if not prod_stations: 
                skipped_log.append({"unit_id": bp.name, "skip_reason": "no_production_slots", "cost": cost, "available_budget": -1})
                break
                
            # Smart Selection: Prefer stations where we already have a fleet (Reinforce Only)
            my_fleets = [f for f in self.engine.fleets_by_faction.get(f_name, []) if not f.is_destroyed]
            
            # Map system->fleet
            fleets_by_system = {}
            for f in my_fleets:
                # Check occupancy
                if len(f.units) >= self.engine.max_fleet_size: continue
                
                # Check location match (Fleet at node reference of planet/station?)
                # Stations usually tracked by System object.
                sys = f.location.system if hasattr(f.location, 'system') else None
                if sys:
                    if sys.name not in fleets_by_system: fleets_by_system[sys.name] = []
                    fleets_by_system[sys.name].append(f)

            reinforce_candidates = [s for s in prod_stations if s.system.name in fleets_by_system]
            
            if reinforce_candidates:
                target_station = rng.choice(reinforce_candidates)
            else:
                target_station = rng.choice(prod_stations)
            target_planet = next((p for p in owned_planets if p.system == target_station.system), owned_planets[0])
            target_fleet = None
            
            my_fleets = [f for f in self.engine.fleets_by_faction.get(f_name, []) if not f.is_destroyed]
            fleets_at_loc = [f for f in my_fleets if f.location == target_planet.node_reference and len(f.units) < self.engine.max_fleet_size]
            
            if fleets_at_loc:
                fleets_at_loc.sort(key=lambda x: x.id)
                target_fleet = rng.choice(fleets_at_loc)
                                
            # 5. Build / Queue
            faction_mgr.deduct_cost(cost)
            spent += cost
            faction_mgr.track_recruitment(cost, count=1)
            
            # Telemetry (Refactored)
            self.telemetry.log_resource_spend(f_name, cost, "Recruitment", target_planet.name)
            
            # Mechanic Hook
            if hasattr(self.engine, 'mechanics_engine'):
                context = {"faction": faction_mgr, "unit": None, "cost": cost, "blueprint": bp} 
                self.engine.mechanics_engine.apply_mechanics(f_name, "on_unit_recruited", context)

            build_turns = self.engine.calculate_build_time(bp)
            
            job = {
                "bp": bp, # Saves the actual object as prototype? No, usually separate. 
                          # ConstructionService might assume bp is a template and clone it?
                          # If passing unique 'bp' object here, we must ensure it persists safely.
                          # Ideally we serialize it or pass components_data.
                "turns_left": build_turns,
                "type": "fleet",
                "target_fleet_id": target_fleet.id if target_fleet else None,
                "node_reference": target_station.system.get_primary_node()
            }
            target_station.unit_queue.append(job)
            
            self.telemetry.log_event(
                EventCategory.CONSTRUCTION,
                "unit_production_started",
                {
                    "unit": bp.name, 
                    "unit_type": "navy", 
                    "location": target_station.name, 
                    "cost": cost,
                    "turn": self.engine.turn_counter
                },
                turn=self.engine.turn_counter,
                faction=f_name
            )
            count += 1
            
        self._log_skip_event(f_name, "navy", skipped_log, skip_caps)
        return spent

    def process_army_production(self, f_name: str, faction_mgr: 'Faction', owned_planets: List['Planet'], budget: int, mode: str = "EXPANSION") -> int:
        spent = 0
        if not owned_planets: return 0
        
        # 1. Get Army Blueprints (Refactored)
        land_bps = self._get_available_army_blueprints(f_name, faction_mgr)
        if not land_bps: 
            return 0

        avg_cost = sum(u.cost for u in land_bps) // len(land_bps) if land_bps else 100
        
        # Phase 62: Industrial Army Scaling (Simplified Infra Count)
        infra_cap = 1
        facilities = ["Barracks", "HQ", "Coven", "Stronghold", "Forge", "Chamber", "Hub", "Pool", "Crypt", "Pits", "Academy", "Cysts", "Yard", "Shrine", "Den", "Platform", "Foundry", "Assembly", "Manufactorum"]
        
        # Quick Scan for Infra Cap
        for p in owned_planets:
            p_buildings = list(p.buildings)
            if hasattr(p, 'provinces') and p.provinces:
                 for node in p.provinces: p_buildings.extend(node.buildings)
            for b_id in p_buildings:
                if any(kw in b_id for kw in facilities): infra_cap += 2 # Simplified weight
        
        max_recruits = int(infra_cap * faction_mgr.army_recruitment_mult)
        # Phase 16: Nerfed 10x -> 2x
        if faction_mgr.requisition > (avg_cost * 100):
             max_recruits *= 2
        max_recruits = max(2, min(max_recruits, 1000)) 
        
        skipped_log = []
        skip_caps = {}
        
        count = 0
        from src.utils.rng_manager import get_stream
        rng = get_stream("economy")

        while count < max_recruits:
            # [FIX] Global Army Cap Check
            # Prevent army spam that crashes the economy, but respect Configuration!
            current_armies = getattr(faction_mgr, 'armies', [])
            active_army_count = len([ag for ag in current_armies if not ag.is_destroyed])
            
            # Use strict global constant for hard-hard cap (e.g. 9999) to prevent engine memory overflow
            # But do NOT use max_land_army_size from config, because that is now the PER-STACK limit.
            global_hard_cap = getattr(self.engine, 'max_land_units', 9999)
            
            if active_army_count >= global_hard_cap:
                if self.engine.logger and count == 0:
                    self.engine.logger.economy(f"[CAP] {f_name} at GLOBAL HARD LIMIT ({active_army_count}/{global_hard_cap}). Stopping recruitment.")
                skipped_log.append({"unit_id": "generic_army", "skip_reason": "global_cap_reached", "cost": avg_cost})
                break

            is_crisis = mode in ["CRISIS", "RECOVERY"]
            if (spent + avg_cost) > budget:
                if is_crisis or faction_mgr.requisition < (avg_cost * 5): 
                    skipped_log.append({"unit_id": "generic_army", "skip_reason": "budget_exceeded", "cost": avg_cost, "available_budget": budget - spent})
                    break
            
            # [SMART_AI] Sustainability Check for Army Production
            if mode not in ["TOTAL_WAR", "EXPANSION"]:
                est_upkeep = int(avg_cost * bal.UNIT_UPKEEP_RATIO)
                total_added_upkeep = count * est_upkeep
                
                # Fetch maintenance stats from Engine cache
                econ_data = self.engine.economy_manager.faction_econ_cache.get(f_name, {})
                f_income = econ_data.get("income", 0)
                f_army_upkeep = econ_data.get("army_upkeep", 0)
                f_fleet_upkeep = econ_data.get("fleet_upkeep", 0)
                f_infra_upkeep = econ_data.get("infrastructure_upkeep", 0)
                f_total_upkeep = econ_data.get("total_upkeep", 0)

                # Check against Army Maintenance Cap (12.5%)
                projected_army_upkeep = f_army_upkeep + total_added_upkeep
                if projected_army_upkeep > (f_income * bal.MAINT_CAP_ARMY):
                    if self.engine.logger and count == 0:
                        self.engine.logger.economy(f"[SMART_AI] {f_name} army upkeep would exceed cap ({bal.MAINT_CAP_ARMY*100}%).")
                    skipped_log.append({"unit_id": "generic_army", "skip_reason": "sustainability_cap_army", "cost": avg_cost})
                    break


                
                
            # land_bps.sort(key=lambda x: x.name)
            
            # --- SMART COMPOSITION LOGIC ---
            army_ratios = {
                "Infantry": 0.55,
                "Armor": 0.25,
                "Artillery": 0.10,
                "Scout": 0.08,
                "Titan": 0.02
            }
            
            # Dynamic Tactics (Army)
            tactics = getattr(faction_mgr, "preferred_tactics", "STANDARD")
            if tactics == "SWARM":
                army_ratios["Infantry"] += 0.30
                army_ratios["Titan"] = 0.0
            elif tactics == "ELITE": # Steel-Bound Syndicate
                army_ratios["Armor"] += 0.25
                army_ratios["Titan"] += 0.05
                army_ratios["Infantry"] -= 0.20
            elif tactics == "SIEGE": # Iron Warriors style
                army_ratios["Artillery"] += 0.25
                army_ratios["Armor"] += 0.10
                
            bp = self._select_blueprint_by_composition(land_bps, army_ratios, rng)
            # -------------------------------
            
            cost = int(bp.cost * faction_mgr.get_modifier("recruitment_cost_mult", 1.0))
            if not faction_mgr.can_afford(cost):
                skipped_log.append({"unit_id": bp.name, "skip_reason": "not_affordable", "cost": cost, "available_budget": faction_mgr.requisition})
                break
                
            # Infrastructure Check (Phase 18)
            eff_tier = getattr(bp, "tier", 1)
            # Re-infer for gating
            if eff_tier == 1:
                if bp.cost > 2000: eff_tier = 3
                elif bp.cost > 800: eff_tier = 2
                
            # 2. Choose Location
            req_b = getattr(bp, "required_building", None)
            prod_planets = self._get_army_production_planets(owned_planets, req_b)
            
            # Filter for Tier (Phase 18) AND Queue Capacity (User Request: Slots)
            prod_planets = [p for p in prod_planets if any(node.max_tier >= eff_tier for node in p.provinces)]
            
            # [FIX] Filter out planets with full queues (Solves infinite recruiting hang)
            prod_planets = [p for p in prod_planets if len(p.unit_queue) < p.max_queue_size]
            
            if not prod_planets: 
                # If no world can CURRENTLY support this tier OR has slots, move to next bp
                skipped_log.append({"unit_id": bp.name, "skip_reason": "no_production_slots_available", "cost": cost, "available_budget": -1})
                count += 1
                continue
                
            target_planet = rng.choice(prod_planets)
            target_node = target_planet.node_reference
            
            # Province Node Logic
            if hasattr(target_planet, 'provinces') and target_planet.provinces:
                cap = next((n for n in target_planet.provinces if n.type == "Capital" or n.type == "ProvinceCapital"), None)
                target_node = cap if cap else rng.choice(target_planet.provinces)

            # 3. Recruit
            faction_mgr.deduct_cost(cost)
            spent += cost
            faction_mgr.track_recruitment(cost, count=1)
            
            self.telemetry.log_resource_spend(f_name, cost, "Recruitment", target_planet.name)
            
            # Mechanic Hook
            if hasattr(self.engine, 'mechanics_engine'):
                context = {"faction": faction_mgr, "unit": None, "cost": cost, "blueprint": bp} 
                self.engine.mechanics_engine.apply_mechanics(f_name, "on_unit_recruited", context)
            
            build_turns = self.engine.calculate_build_time(bp)
            job = {
                "bp": bp,
                "turns_left": build_turns,
                "type": "army",
                "node_reference": target_node
            }
            target_planet.unit_queue.append(job)

            self.telemetry.log_event(
                EventCategory.CONSTRUCTION,
                "unit_production_started",
                {
                    "unit": bp.name, 
                    "unit_type": "army", 
                    "location": target_planet.name, 
                    "cost": bp.cost,
                    "turn": self.engine.turn_counter
                },
                turn=self.engine.turn_counter,
                faction=f_name
            )
            
            count += 1
            
        self._log_skip_event(f_name, "army", skipped_log, skip_caps)
        return spent

    def _get_base_faction(self, f_name: str) -> str:
        """Strips numeric suffix from cloned factions for blueprint lookup."""
        if " " in f_name:
            parts = f_name.split(" ")
            if parts[-1].isdigit():
                return " ".join(parts[:-1])
        return f_name

    def _get_available_blueprints(self, f_name: str, faction_mgr: 'Faction') -> List[Any]:
        """Helper to filter valid naval blueprints based on tech/tier."""
        base_f = self._get_base_faction(f_name)
        blueprints = self.engine.unit_blueprints.get(base_f, [])
        navy_bps = [bp for bp in blueprints if getattr(bp, "is_ship", lambda: False)() or "Ship" in bp.abilities.get("Tags", []) or "Cruiser" in bp.name or "Battleship" in bp.name or "Escort" in bp.name or "Frigate" in bp.name]
        
        if not navy_bps: return []
        
        tech_metrics = self.engine.tech_manager.calculate_tech_tree_depth(f_name, faction_mgr.unlocked_techs)
        tier_breakdown = tech_metrics.get("tier_breakdown", {})
        
        available_bps = []
        for bp in navy_bps:
            eff_tier = getattr(bp, "tier", 1)
            # Cost inference logic
            if eff_tier == 1:
                if bp.cost > 30000: eff_tier = 4
                elif bp.cost > 15000: eff_tier = 3
                elif bp.cost > 5000: eff_tier = 2

            # Tech Checks
            reqs = getattr(bp, 'required_tech', [])
            if not reqs:
                tm_req = self.engine.tech_manager.get_required_tech_for_unit(f_name, bp.name)
                if tm_req: reqs = [tm_req]
                
            if reqs:
                if all(faction_mgr.has_tech(t) for t in reqs):
                    available_bps.append(bp)
            else:
                # Procedural Tier Check
                allowed = False
                if eff_tier <= 1: allowed = True
                elif eff_tier == 2 and (tier_breakdown.get(2, 0) >= 1 or tier_breakdown.get(3, 0) >= 1): allowed = True
                elif eff_tier >= 3 and (tier_breakdown.get(3, 0) >= 1 or tier_breakdown.get(4, 0) >= 1): allowed = True
                
                if allowed: available_bps.append(bp)
                
        return available_bps

    def _get_production_planets(self, owned_planets: List['Planet'], required_building: str = None) -> List['Planet']:
        """Helper to find planets capable of building ships, filtering for specific requirements."""
        prod_planets = []
        for p in owned_planets:
            has_shipyard = False
            # Check for shipyard infrastructure
            for b in p.buildings:
                 if b in ["Orbital Dock", "Shipyard", "Deep Space Foundry", "Raider Drydock", "Air Caste Dock"]:
                     has_shipyard = True; break
                 
                 # Dynamic lookup
                 b_data = self.engine.universe_data.get_building_database().get(b, {})
                 desc = b_data.get("effects", {}).get("description", "")
                 if "Unlocks Space Ship Construction" in desc or "shipyard" in desc.lower():
                     has_shipyard = True; break
                     
            if has_shipyard and not getattr(p, 'is_sieged', False):
                if required_building and required_building != "None":
                    # Strict Check
                    has_req = (required_building in p.buildings)
                    if not has_req and hasattr(p, 'provinces'):
                         for node in p.provinces:
                             if required_building in node.buildings:
                                 has_req = True; break
                    if has_req: prod_planets.append(p)
                else:
                    prod_planets.append(p)
                    
    
    def _get_available_army_blueprints(self, f_name: str, faction_mgr: 'Faction') -> List[Any]:
        """Helper to filter valid army blueprints."""
        base_f = self._get_base_faction(f_name)
        blueprints = self.engine.army_blueprints.get(base_f, [])
        
        if not blueprints:
             blueprints = self.engine.unit_blueprints.get(base_f, [])
             
        if not blueprints: return []
        
        land_bps = [bp for bp in blueprints if not getattr(bp, 'is_ship', lambda: False)() and "Ship" not in bp.abilities.get("Tags", [])]

        # STRICT FILTER: Exclude Naval Types (redundant check for "Land Frigates")
        # Ensure we don't accidentally recruit ships as armies
        naval_types = ["ship", "frigate", "destroyer", "cruiser", "battleship", "escort", "fighter", "strike_craft", "transport"]
        valid_fps = []
        for bp in land_bps:
            # Check type attribute (handle dict or object)
            b_type = getattr(bp, "type", "infantry")
            if isinstance(b_type, str): b_type = b_type.lower()
            
            # Check Tags
            tags = getattr(bp, "abilities", {}).get("Tags", [])
            
            if b_type in naval_types: continue
            if "Ship" in tags or "Frigate" in tags: continue
            
            # Additional Check: If it uses Ship class (unlikely here but safe)
            if hasattr(bp, "is_ship") and bp.is_ship(): continue
            
            valid_fps.append(bp)
            
        land_bps = valid_fps
        
        # Filter by Tech Requirements (Strict Depth Check)
        tech_metrics = self.engine.tech_manager.calculate_tech_tree_depth(f_name, faction_mgr.unlocked_techs)
        tier_breakdown = tech_metrics.get("tier_breakdown", {})
        
        valid_land_bps = []
        for bp in land_bps:
            eff_tier = getattr(bp, "tier", 1)
            # Infer Tier from Cost if default
            if eff_tier == 1:
                if bp.cost > 2000: eff_tier = 3 # Super Heavy
                elif bp.cost > 800: eff_tier = 2 # Elite/Heavy
            
            allowed = False
            if eff_tier <= 1:
                allowed = True
            elif eff_tier == 2:
                 if tier_breakdown.get(2, 0) >= 1 or tier_breakdown.get(3, 0) >= 1: allowed = True
            elif eff_tier >= 3:
                 if tier_breakdown.get(3, 0) >= 1 or tier_breakdown.get(4, 0) >= 1: allowed = True
            
            if allowed:
                # NEW Phase 18: Infrastructure Check
                if faction_mgr and hasattr(faction_mgr, 'owned_planets'):
                     # This check is a bit broad since we filter blueprints before 
                     # we know the target planet. But we can ensure that SOME planet 
                     # has the infrastructure before offering the unit.
                     # Actually, a better place is to check during the loop in process_army_recruitment.
                     pass
                valid_land_bps.append(bp)
                
        return valid_land_bps

    def _get_army_production_planets(self, owned_planets: List['Planet'], required_building: str = None) -> List['Planet']:
        """Helper to find planets capable of raising armies."""
        facilities = {
            "Barracks": 1, "HQ": 4, "Coven": 4, 
            "Stronghold": 8, "Forge": 8,
            "Chamber": 4, "Hub": 4, "Pool": 4,
            "Crypt": 4, "Pits": 2, "Academy": 6, 
            "Cysts": 4, "Yard": 4, "Shrine": 4, 
            "Den": 4, "Platform": 4, "Foundry": 8, "Assembly": 6,
            "Training": 4, "Temple": 4, "Citadel": 8, "War": 4, "Military": 4,
            "Outpost": 2, "Garrison": 4, "Fortress": 10, "Keep": 6
        }
        
        prod_planets = []
        for p in owned_planets:
            has_infra = False
            
            # Check Planet Surface
            for b in p.buildings:
                if any(kw in b for kw in facilities): 
                    has_infra = True; break
                
                b_data = self.engine.universe_data.get_building_database().get(b, {})
                eff = b_data.get("effects", {}).get("description", "")
                if b_data.get("unlocks") or "Garrison" in eff or "Rank for" in eff or "Unlocks" in eff:
                    has_infra = True; break
            
            # Check Provinces if Surface check failed (or just check generally?)
            # Logic in old code checked both for capacity, but here for simplified boolean "has_infra"
            if not has_infra and hasattr(p, 'provinces') and p.provinces:
                 for node in p.provinces:
                     for b in node.buildings:
                         if b in facilities: has_infra = True; break
                         
                         b_data = self.engine.universe_data.get_building_database().get(b, {})
                         eff = b_data.get("effects", {}).get("description", "")
                         if b_data.get("unlocks") or "Garrison" in eff or "Rank for" in eff or "Unlocks" in eff:
                             has_infra = True; break
                     if has_infra: break
            
            if has_infra: 
                # Strict Requirement Check
                if required_building and required_building != "None":
                     has_req = (required_building in p.buildings)
                     if not has_req and hasattr(p, 'provinces'):
                         for node in p.provinces:
                             if required_building in node.buildings:
                                 has_req = True; break
                     if has_req: prod_planets.append(p)
                else:
                    prod_planets.append(p)
        
        # Filter Sieged
        return [p for p in prod_planets if not getattr(p, 'is_sieged', False)]

    def _get_ship_production_sites(self, f_name: str, faction_mgr: 'Faction', owned_planets: List['Planet']) -> List[Any]:
        """Returns Starbases and Planets with shipyard capacity."""
        sites = []
        
        # 1. Active Starbases
        for s in self.engine.systems:
            for sb in s.starbases:
                if sb.faction == f_name and sb.is_alive():
                    if sb.naval_slots > 0 or sb.tier >= 1:
                        sites.append(sb)
                        
        # 2. Planets with Shipyards (New Colonies)
        for p in owned_planets:
            # Check naval slots (calculated in Planet.recalc_stats based on buildings)
            if p.naval_slots > 0 and not getattr(p, 'is_sieged', False):
                # Only add if not already covered by a Starbase? 
                # Starbase and Planet are separate production queues, so we can add both!
                sites.append(p)
                
        return sites

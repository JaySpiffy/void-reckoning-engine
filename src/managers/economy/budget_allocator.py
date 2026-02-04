from typing import TYPE_CHECKING, Dict, Any, Optional
from src.core.constants import COLONIZATION_REQ_COST
from src.reporting.telemetry import EventCategory
from src.utils.profiler import profile_method

if TYPE_CHECKING:
    from src.core.interfaces import IEngine
    from src.models.faction import Faction
    from src.services.recruitment_service import RecruitmentService
    from src.services.construction_service import ConstructionService

class BudgetAllocator:
    """
    Handles budget distribution and spending execution.
    """
    def __init__(self, engine: 'IEngine', recruitment_service: 'RecruitmentService', construction_service: 'ConstructionService', rng: Any = None):
        self.engine = engine
        self.recruitment_service = recruitment_service
        self.construction_service = construction_service
        self.rng = rng

    @profile_method
    def execute_budget(self, f_name: str, faction_mgr: 'Faction', econ_data: dict) -> None:
        """
        Distributes income to budgets and executes spending.
        """
        income = econ_data["income"]
        upkeep = econ_data["upkeep"]
        
        # [PHASE 7] VASSAL TRIBUTE
        # If this faction is a Vassal, 20% of GROSS income goes to Overlord
        tribute_paid = 0
        overlord_name = None
        if hasattr(self.engine, 'diplomacy'):
            treaties = self.engine.diplomacy.treaty_coordinator.treaties.get(f_name, {})
            for other_f, state in treaties.items():
                if state == "Overlord":
                    overlord_name = other_f
                    tribute_paid = int(income * 0.20)
                    income -= tribute_paid
                    
                    # Add to Overlord
                    overlord_mgr = self.engine.get_faction(overlord_name)
                    if overlord_mgr:
                        overlord_mgr.add_income(tribute_paid)
                        if self.engine.logger:
                            self.engine.logger.economy(f"[TRIBUTE] {overlord_name} received {tribute_paid} Req from Vassal {f_name}")
                    break

        # Fix: Ensure broken-out upkeep stats are available from cache
        # (ResourceHandler provides them, but hydrate might not copy them all)
        # Checking _hydrate_cached_econ in EconomyManager... it maps most.
        # Adding defaults here just in case.
        econ_data.setdefault("fleet_upkeep", 0)
        econ_data.setdefault("army_upkeep", 0)
        econ_data.setdefault("infrastructure_upkeep", 0)
        
        margin = econ_data["margin"]
        active_mode = econ_data["active_mode"]
        
        # Inject for services (RecruitmentService sustainability check)
        faction_mgr.income = income
        faction_mgr.upkeep = upkeep
        owned_planets = self.engine.planets_by_faction.get(f_name, [])
        total_planets = len(owned_planets) 

        # Calculate Allocations (Accumulative)
        total_inflow = max(0, income - upkeep)

        # [COLONIZATION FIX] Force Savings
        if active_mode["name"] == "EXPANSION" and faction_mgr.requisition < COLONIZATION_REQ_COST:
            # If we need to colonize but are poor, save 80% of inflow
            savings_rate = 0.8
            saved_amount = int(total_inflow * savings_rate)
            total_inflow -= saved_amount
        
        # Initialize budgets if missing (Runtime safety)
        if not hasattr(faction_mgr, 'budgets'):
            faction_mgr.budgets = {"research": 0, "construction": 0, "navy": 0, "army": 0}
            
        # Prevent "Budget Debt" from stalling wealthy factions
        # If a budget bucket is negative, reset it to 0 so new income/stimulus is usable.
        for k in faction_mgr.budgets:
            if faction_mgr.budgets[k] < 0:
                faction_mgr.budgets[k] = 0
        
        # Migration path for old saves/objects
        if "recruitment" in faction_mgr.budgets:
            val = faction_mgr.budgets.pop("recruitment", 0)
            faction_mgr.budgets["navy"] += int(val * 0.4)
            faction_mgr.budgets["army"] += int(val * 0.6)

        # 1. Distribute Income (Revised Step 3: Growth Funds & Debt)
        import src.core.balance as bal
        
        # Calculate Total Maintenance Load
        # We need categorized upkeep but it's likely pre-calced in econ_data
        fleet_upkeep = econ_data.get("fleet_upkeep", 0)
        army_upkeep = econ_data.get("army_upkeep", 0)
        infra_upkeep = econ_data.get("infrastructure_upkeep", 0)
        
        # Determine Growth Funds
        # Growth Funds = Income - (All Upkeep) ... basically Net Income
        # But we want to budget based on "Available Room to Expand"? 
        # No, the plan says: "Only income remaining after the 12.5% maintenance caps is considered Growth Funds"
        # Wait, if upkeep < 12.5%, do we reserve the rest or free it?
        # "Total allowed maintenance should not exceed 37.5%."
        
        # Let's interpret: Total Inflow IS Growth Funds (Net Income).
        # We just need to check if we are ALLOWED to add more upkeep to a category.
        
        # Phase 11: Priority Debt Clearance
        growth_funds = total_inflow
        if faction_mgr.requisition < 0:
            # If in debt, 100% of net profit must go to debt clearance before any new spending.
            # Phase 108: Forfeit all existing stagnant budgets to debt clearance.
            for k in list(faction_mgr.budgets.keys()):
                if faction_mgr.budgets[k] > 0:
                    forfeited = faction_mgr.budgets[k]
                    faction_mgr.requisition += forfeited
                    faction_mgr.budgets[k] = 0
                    if self.engine.logger:
                        self.engine.logger.economy(f"[DEBT_FORFEIT] {f_name} forfeited {forfeited}R from {k} budget to pay down debt.")

            if growth_funds > 0:
                faction_mgr.requisition += growth_funds
                if self.engine.logger:
                    self.engine.logger.economy(f"[DEBT] {f_name} applied {growth_funds} net profit to debt. New Req: {faction_mgr.requisition}")
                growth_funds = 0
            else:
                # Still bleeding money? Growth funds already <= 0
                pass
             
        # Distribute remaining Growth Funds
        if growth_funds > 0:
            # Check Caps before allocating "Growth" money to specific buckets
            # If a category is OVER CAP, it gets 0 allocation for new stuff.
            
            inc_base = max(1, income)
            
            can_fund_navy = (fleet_upkeep / inc_base) < bal.MAINT_CAP_NAVY
            can_fund_army = (army_upkeep / inc_base) < bal.MAINT_CAP_ARMY
            # Construction handles Infra cap check locally usually, but we can throttle budget
            can_fund_infra = (infra_upkeep / inc_base) < bal.MAINT_CAP_INFRA
            
            # Normal Ratios
            r_con = active_mode["budget"]["construction"]
            r_res = active_mode["budget"]["research"]
            r_rec = active_mode["budget"]["recruitment"]
            
            # If blocked, redistribute? or just burn/save?
            # Creating a naive redistribution for now:
            # If Navy blocked, dump to Economy (Construction) to grow income.
            
            # If blockade redistribution (Navy/Army capped)
            decision_type = "standard"
            redist_amount = 0
            
            if not can_fund_navy or not can_fund_army:
                decision_type = "redistributed_capped"
                shift_val = (r_rec * 0.5)
                r_con += shift_val 
                r_rec *= 0.5
                redist_amount = int(growth_funds * shift_val)
            
            # Allocation
            con_alloc = int(growth_funds * r_con)
            res_alloc = int(growth_funds * r_res)
            
            faction_mgr.budgets["construction"] += con_alloc
            faction_mgr.budgets["research"] += res_alloc
            
            # [CLEVER LOGIC] Granular Military Budget support
            # If the mode provides explicit Navy/Army ratios, use them.
            # Otherwise, fall back to the "Recruitment" blob split.
            r_navy = active_mode["budget"].get("navy", 0.0)
            r_army = active_mode["budget"].get("army", 0.0)
            
            if r_navy > 0 or r_army > 0:
                # Explicit Allocation
                navy_alloc = int(growth_funds * r_navy)
                army_alloc = int(growth_funds * r_army)
            else:
                # Legacy Fallback (Recruitment Blob)
                recruit_alloc = int(growth_funds * r_rec)
                navy_alloc = int(recruit_alloc * 0.45) if can_fund_navy else 0
                army_alloc = int(recruit_alloc * 0.55) if can_fund_army else 0

            # Apply Allocations (with Cap Checks)
            if can_fund_navy:
                faction_mgr.budgets["navy"] += navy_alloc
            
            if can_fund_army:
                faction_mgr.budgets["army"] += army_alloc
                
            # Maintenance Cap Warning (Telemetry)
            total_upkeep = econ_data.get("upkeep", 0)
            income = econ_data.get("income", 1)
            upkeep_pct = total_upkeep / income if income > 0 else 1.0
            
            if self.engine.telemetry and upkeep_pct > 0.35:
                 # Log every 5 turns or if critical (>0.5)
                 is_critical = upkeep_pct > 0.5
                 if is_critical or (self.engine.turn_counter % 5 == 0):
                     self.engine.telemetry.log_event(
                         EventCategory.ECONOMY,
                         "maintenance_cap_warning",
                         {
                             "caps": {
                                 "navy": {"current": 0.0, "limit": 0.125, "pct_used": 0.0}, # TODO: Calculate these properly if needed, for new just logging state
                                 "total": {"current": total_upkeep, "limit": income * 0.375, "pct_used": upkeep_pct}
                             },
                             "warning_level": "critical" if is_critical else "approaching" if upkeep_pct > 0.35 else "none",
                             "categories_over_limit": [k for k, v in {"navy": not can_fund_navy, "army": not can_fund_army}.items() if v],
                             "projected_cap_exceeded": False
                         },
                         turn=self.engine.turn_counter,
                         faction=f_name
                     )

            # Log Allocation Decision
            if self.engine.telemetry:
                 self.engine.telemetry.log_event(
                     EventCategory.ECONOMY,
                     "budget_allocation_decision",
                     {
                         "mode": active_mode["name"],
                         "growth_funds_available": growth_funds,
                         "allocations": {
                             "construction": {"allocated": con_alloc, "reason": "standard"},
                             "research": {"allocated": res_alloc, "reason": "standard"},
                             "navy": {"allocated": navy_alloc, "blocked": not can_fund_navy, "reason": "cap_exceeded" if not can_fund_navy else "standard"},
                             "army": {"allocated": army_alloc, "blocked": not can_fund_army, "reason": "cap_exceeded" if not can_fund_army else "standard"}
                         },
                         "redistributions": [{"from": "navy", "to": "construction", "amount": navy_alloc, "reason": "redistributed_due_to_cap"} if not can_fund_navy else {}],
                         "sustainability_checks": {
                             "passed": can_fund_navy and can_fund_army,
                             "checks": [
                                 {"check": "navy_cap", "result": can_fund_navy},
                                 {"check": "army_cap", "result": can_fund_army},
                                 {"check": "infra_cap", "result": can_fund_infra}
                             ]
                         }
                     },
                     turn=self.engine.turn_counter,
                     faction=f_name
                 )
            
        # --- Research Progression (Parallel Slot Support) ---
        if "research_income" in econ_data:
            rp_in = econ_data["research_income"]
            faction_mgr.research_income = rp_in
            faction_mgr.research_points += rp_in

            # 1. Ensure slots are filled (Up to 3)
            while len(faction_mgr.active_projects) < 3 and faction_mgr.research_queue:
                new_proj = faction_mgr.research_queue.pop(0)
                faction_mgr.active_projects.append(new_proj)
                if self.engine.logger:
                    self.engine.logger.info(f"[Research] {f_name} started parallel project: {new_proj.tech_id}")

            # Legacy compatibility for UI/other modules
            if faction_mgr.active_projects:
                faction_mgr.active_research = faction_mgr.active_projects[0]
            else:
                faction_mgr.active_research = None

            # 2. Distribute Research Points
            if faction_mgr.active_projects:
                num_slots = len(faction_mgr.active_projects)
                shared_rp = faction_mgr.research_points / num_slots
                faction_mgr.research_points = 0.0 # Reset points as we distribute them
                
                completed_indices = []
                for i, proj in enumerate(faction_mgr.active_projects):
                    # Invest the shared portion
                    overflow = proj.invest(int(shared_rp))
                    faction_mgr.research_points += float(overflow) # Return any unused points (e.g. if completed)

                    if proj.is_complete:
                        faction_mgr.unlock_tech(proj.tech_id, turn=self.engine.turn_counter, tech_manager=self.engine.tech_manager)
                        if self.engine.logger:
                            self.engine.logger.info(f"[Research] {f_name} COMPLETED {proj.tech_id}!")
                        completed_indices.append(i)

                # Remove completed projects
                for index in sorted(completed_indices, reverse=True):
                    faction_mgr.active_projects.pop(index)
                
                # Update legacy pointer
                faction_mgr.active_research = faction_mgr.active_projects[0] if faction_mgr.active_projects else None
            # Phase 14: Research Queue Analysis
            if self.engine.turn_counter % 5 == 0:
                self._log_research_queue_analysis(f_name, faction_mgr)

        # --- Finalize Turn Stats ---
        # Sustainability Cap Override (Hegemony flavor / Safety)
        is_total_war = active_mode["name"] == "TOTAL_WAR"
        upkeep_ratio = upkeep / income if income > 0 else 1.0
        
        # Phase 42: Infrastructure Desperation Check
        if f_name == "Hegemony" and self.engine.logger:
             b = faction_mgr.budgets
             self.engine.logger.economy(f"{f_name} Mode: {active_mode['name']}. Budgets: Navy:{b.get('navy')} Army:{b.get('army')} Con:{b['construction']} Res:{b['research']} [Net In: {total_inflow}]")
        
        # Apply Income/Expense to Physical Treasury
        faction_mgr.add_income(income)
        faction_mgr.deduct_cost(upkeep)
        
        # Telemetry for Resource Chart
        self._log_economy_telemetry(f_name, faction_mgr, econ_data, total_inflow)

        # [STIMULUS] Inject stockpile funds if income is low but vault is full
        self._inject_stimulus_budget(f_name, faction_mgr, total_inflow, active_mode)

        # 3. Spend Budgets - STRICT: No spending if in debt!
        if faction_mgr.requisition > 0:
            self._spend_budgets(f_name, faction_mgr, owned_planets, active_mode)

    def _log_research_queue_analysis(self, f_name: str, faction_mgr: 'Faction'):
        """Logs research queue state for analysis (Metric #1)."""
        if not self.engine.telemetry: return
        
        queue_data = []
        # Support for list of objects or dicts (Legacy vs New)
        queue_list = faction_mgr.research_queue if hasattr(faction_mgr, 'research_queue') else []
        for i, proj in enumerate(queue_list):
            tech_id = getattr(proj, 'tech_id', str(proj))
            cost = getattr(proj, 'total_cost', 0)
            acc = getattr(proj, 'accumulated_points', 0)
            queue_data.append({
                "tech_id": tech_id,
                "position": i + 1,
                "cost": cost,
                "progress_pct": (acc / cost * 100) if cost > 0 else 0
            })
            
        active_data = None
        if faction_mgr.active_research:
            proj = faction_mgr.active_research
            tech_id = getattr(proj, 'tech_id', 'unknown')
            cost = getattr(proj, 'total_cost', 0)
            acc = getattr(proj, 'accumulated_points', 0)
            active_data = {
                "tech_id": tech_id,
                "cost": cost,
                "progress_pct": (acc / cost * 100) if cost > 0 else 0
            }
            
        self.engine.telemetry.log_event(
            EventCategory.TECHNOLOGY,
            "research_queue",
            {
                "faction": f_name,
                "active_research": active_data,
                "queue": queue_data,
                "total_queued": len(queue_data),
                "is_starving": len(queue_data) == 0 and active_data is None
            },
            turn=self.engine.turn_counter,
            faction=f_name
        )

    def _inject_stimulus_budget(self, f_name: str, faction_mgr: 'Faction', total_inflow: int, active_mode: dict) -> None:
        """
        Injects additional budget from the requisition stockpile if the faction is wealthy
        but has low current-turn income (which would otherwise stall construction/recruitment).
        """
        # Thresholds
        WEALTH_THRESHOLD = 50000  # "Wealthy" definition
        STIMULUS_CAP = 10000      # Max injection per turn to prevent total liquidation
        
        # Only inject if we have money but no flow
        if faction_mgr.requisition > WEALTH_THRESHOLD and total_inflow < 2000:
            
            # Determine available "free" cash (safety buffer of 20k)
            available_liquid = faction_mgr.requisition - 20000
            
            if available_liquid > 0:
                # Calculate injection amount (10% of liquid or Cap)
                injection = min(int(available_liquid * 0.10), STIMULUS_CAP)
                
                if injection > 500: # Minimum worthwhile injection
                    # Distribute Injection based on Mode logic (simplified 40/40/20 split)
                    
                    con_share = int(injection * 0.40)
                    navy_share = int(injection * 0.40)
                    army_share = int(injection * 0.20)
                    
                    # Apply
                    faction_mgr.budgets["construction"] += con_share
                    faction_mgr.budgets["navy"] += navy_share
                    faction_mgr.budgets["army"] += army_share
                    
                    # Log (Debug for now, maybe economy log later)
                    if self.engine.logger:
                        self.engine.logger.economy(f"[STIMULUS] {f_name} injected {injection} Req from stockpile (Req: {faction_mgr.requisition}). Con:+{con_share} Navy:+{navy_share} Army:+{army_share}")


    def _spend_budgets(self, f_name, faction_mgr, owned_planets, active_mode = {"name": "EXPANSION", "budget": {"recruitment": 0.5, "construction": 0.3, "research": 0.2}}):
        spent = {"recruit": 0, "construct": 0, "research": 0}
        
        # A. Research (Active Spending)
        budget_res = faction_mgr.budgets["research"]
        if budget_res > 0 and faction_mgr.requisition > 0:
            s_res = self.process_active_research_spending(f_name, faction_mgr, budget_res)
            faction_mgr.budgets["research"] -= s_res
            spent["research"] = s_res
            
        # B. Construction
        budget_con = faction_mgr.budgets["construction"]
        if budget_con > 0 and faction_mgr.requisition > 0:
            s_con = self.construction_service.process_construction_cycle(f_name, faction_mgr, owned_planets, budget_con, active_mode["name"])
            faction_mgr.budgets["construction"] -= s_con
            spent["construct"] = s_con
            
        # C. Recruitment
        # Process Fleet Shells (Commissioning)
        budget_navy = faction_mgr.budgets.get("navy", 0)
        if budget_navy > 0 and faction_mgr.requisition > 0:
             s_comm = self.recruitment_service.process_fleet_commissioning(f_name, faction_mgr, owned_planets, budget_navy, active_mode["name"])
             faction_mgr.budgets["navy"] -= s_comm
             spent["recruit"] += s_comm
             
        # Process Ship Production (Queue)
        budget_navy = faction_mgr.budgets.get("navy", 0)
        if budget_navy > 0 and faction_mgr.requisition > 0:
             s_ship = self.recruitment_service.process_ship_production(f_name, faction_mgr, owned_planets, budget_navy, active_mode["name"])
             faction_mgr.budgets["navy"] -= s_ship
             spent["recruit"] += s_ship
             
        # Process Army Production (Queue)
        budget_army = faction_mgr.budgets.get("army", 0)
        # DEBUG PRINT
        if faction_mgr.requisition > 20000:
             # print(f"DEBUG_BUDGET: {f_name} Army Budget: {budget_army}, Req: {faction_mgr.requisition}")
             with open("debug_army.txt", "a") as f:
                 f.write(f"DEBUG_BUDGET: {f_name} Army Budget: {budget_army}, Req: {faction_mgr.requisition}\n")
             
        if budget_army > 0 and faction_mgr.requisition > 0:
             s_army = self.recruitment_service.process_army_production(f_name, faction_mgr, owned_planets, budget_army, active_mode["name"])
             faction_mgr.budgets["army"] -= s_army
             spent["recruit"] += s_army
             
    @profile_method
    def process_active_research_spending(self, f_name: str, faction_mgr: 'Faction', budget: int) -> int:
        """
        Handles active spending of Requisition to unlock technologies.
        [REFACTOR] Requisition 'buying' of tech is disabled. RP is the only currency.
        This method now simply returns 0 as no Requisition is spent on tech directly.
        """
        # In the new Stellaris-style system, you cannot buy tech with money.
        # You can only invest RP which is generated by infrastructure.
        return 0
            
    def _log_economy_telemetry(self, f_name, faction_mgr, econ_data, net_inflow):
        if not self.engine.telemetry: return
        
        income = econ_data["income"]
        upkeep = econ_data["upkeep"]
        
        self.engine.telemetry.log_event(
            EventCategory.ECONOMY,
            "income_collected",
            {
                "amount": income, 
                "upkeep": upkeep, 
                "net": net_inflow,
                "tribute_paid": tribute_paid if 'tribute_paid' in locals() else 0,
                "overlord": overlord_name if 'overlord_name' in locals() else None,
                "breakdown": econ_data.get("income_by_category", {})
            },
            turn=self.engine.turn_counter,
            faction=f_name
        )
        
        # Detailed metrics
        if econ_data:
            for category, amount in econ_data.get("income_by_category", {}).items():
                if amount > 0:
                    self.engine.telemetry.metrics.record_resource_gain(f_name, float(amount), category=category)
        
        if econ_data.get("military_upkeep", 0) > 0:
            self.engine.telemetry.metrics.record_upkeep_cost(f_name, float(econ_data["military_upkeep"]), upkeep_type="military")
            
        if econ_data.get("infrastructure_upkeep", 0) > 0:
            self.engine.telemetry.metrics.record_upkeep_cost(f_name, float(econ_data["infrastructure_upkeep"]), upkeep_type="infrastructure")

        self.engine.telemetry.record_economic_snapshot(f_name, income, upkeep, faction_mgr.requisition)

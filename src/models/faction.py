import random
from typing import List, Dict, Optional, Any
from src.core.constants import get_building_database

class Faction:
    def __init__(self, name, personality_id=None, universe_name=None, uid=None, logger=None, initial_req=0):
        """
        Initializes a Faction entity, tracking economy and performance stats.
        
        Args:
            name (str): Faction name (key).
            personality_id (str): Optional ID linking to AI personality module.
            universe_name (str): The universe context for dynamic loading.
            uid (str): Optional GUID for the faction (dual-passport system).
            logger: Optional logger instance.
            initial_req (int): Starting Requisition count.
        """
        from src.utils.guid_generator import generate_legacy_guid
        
        self.name = name
        self.universe_name = universe_name
        self.logger = logger
        
        # Dual-Passport System: Support both legacy 'id' (name) and new 'uid' (GUID)
        self.uid = uid if uid else generate_legacy_guid("FACTION", name)
        self.initial_requisition = initial_req
        self.requisition = initial_req
        self.budgets = {
            "research": 0,
            "construction": 0,
            "navy": 0,
            "army": 0
        }
        self.armies = [] # List of ArmyGroup objects
        self.fleets = [] # List of Fleet objects
        
        # --- Research System (Batch 13) ---
        self.research_points = 0.0 # Current stockpile
        self.research_income = 0.0 # Per-turn generation
        self.research_queue = []   # List[ResearchProject]
        self.active_projects = []  # List[ResearchProject] - Support for parallel research (up to 3 slots)
        self.active_research = None # Deprecated: Use active_projects[0] if needed for legacy compatibility
        
        self.unlocked_techs = ["Headquarters", "None"] # Default start techs
        self.tech_unlocked_turns = {"Headquarters": 0, "None": 0}
        self.home_planet_name = None # Capital planet name
        
        # --- Fog of War / Intelligence (Phase 7) ---
        self.visible_planets = set()  # Currently in view (real-time data)
        self.known_planets = set()    # Discovered (memory of existence)
        self.known_factions = set()   # Encountered
        
        # --- Phase 100: Intelligence & Exploration ---
        self.intelligence_memory = {} # {planet_name: {last_seen_turn, last_owner, strength, income, threat}}
        self.explored_systems = set() # System names fully scouted
        self.exploration_frontier = [] # Priority queue of (score, system_ref)
        self.last_exploration_update = 0
        self.fleet_intel = {} # {fleet_id: {faction, power, location, last_seen_turn}}
        
        # Phase 105: Strategic Planning Data
        self._learned_personality = None # Backing field for property
        self.active_strategic_plan = None # Reference to StrategicPlan object
        self.strategic_posture = "BALANCED" # EXPANSION, CONSOLIDATION, DEFENSIVE
        self.design_preference = "BALANCED" # ANTI_SHIELD, ANTI_ARMOR, AREA_EFFECT
        self.posture_changed_turn = 0
        self.rally_points = {} # {zone_id: planet_name}
        
        # --- Data-Driven Quirks (Universe-Agnostic) ---
        self.diplomacy_bonus = 0     # e.g., for Federation
        self.retreat_threshold_mod = 0.0 # e.g., -0.2 for Marauders
        self.research_multiplier = 1.0
        self.evasion_rating = 0.0    # e.g., 0.5 for Aaether-kini
        self.casualty_plunder_ratio = 0.0 # e.g., 0.2 for Drukhari
        
        # [QUIRK] Recruitment Multipliers (replacing balance.py hardcodes)
        self.navy_recruitment_mult = 1.0 # default
        self.army_recruitment_mult = 1.0
        self.biomass_hunger = 0.0
        self.threat_affinity = 0.0
        
        # New AI Personality Quirks (Phase 61)
        self.personality_id = personality_id
        
        # Phase 61: Load Personality immediately if ID is present
        # This ensures all quirks are synced before simulation starts
        # Phase 61: Load Personality immediately if ID is present
        if self.personality_id and (hasattr(self, 'universe_name') and self.universe_name):
            self.load_from_registry(self.personality_id, self.universe_name)
        elif self.personality_id:
             # Try to load without universe name if possible (global context?)
             # For now, just skip and warn
             pass

        self.expansion_focus = "balanced"
        self.claim_cost_mult = 1.0
        self.robot_upkeep_mult = 1.0
        self.on_kill_effect = None
        self.preferred_tactics = "STANDARD"
        self.carrier_bias = False
        self.admiral_skill_bias = 1.0
        self.tax_efficiency = 1.0
        self.navy_maintenance_mult = 1.0
        
        # Phase XXX: Adaptive Learning System
        self.learning_history = {
            'plan_outcomes': [],  # List of {plan_id, goal, success, turns_taken, planets_gained, planets_lost}
            'target_outcomes': [],  # List of {target_name, attempted_turn, captured_turn, cost, value}
            'battle_outcomes': [],  # List of {turn, location, won, power_ratio, casualties}
            'personality_mutations': [],  # List of {turn, trait, old_value, new_value, reason}
            'performance_window': [],  # Last 10 turns: {turn, planets_owned, total_power, req_balance, battles_won}
            'intel_events': [] # List of {turn, amount, source, reason}
        }
        self.intel_points = 0 # Currency for hybrid tech research
        self.pending_adaptations = [] # Queue of {tech_id, cost, progress}
        self.last_adaptation_turn = 0
        self.adaptation_cooldown = 10  # Minimum turns between adaptations
        self.adaptation_cooldown = 10  # Minimum turns between adaptations
        self.poor_performance_streak = 0  # Consecutive turns of poor performance
        self.learned_personality = None # Persisted FactionPersonality object
        
        # --- Technology Acquisition (Phase 8) ---
        self.salvaged_blueprints = {}  # {blueprint_id: {quality, salvage_turn, source_faction}}
        self.stolen_blueprints = {}    # {blueprint_id: {theft_turn, source_faction}}
        self.shared_blueprints = {}    # {blueprint_id: {share_turn, source_faction}}
        
        # --- Advanced Espionage (Phase 2) ---
        self.spy_networks = {} # {target_faction_name: SpyNetwork}
        
        # --- Faction Mechanics (Phase 8) ---
        self.conviction_stacks = 0     # Templars of the Flux
        self.biomass_pool = 0          # Bio-Tide Collective
        self.biomass_consumed = 0      # Stat tracking
        self.reanimations_count = 0    # Algorithmic Hierarchy
        self.reanimations_count = 0    # Algorithmic Hierarchy
        self.raid_income_this_turn = 0 # Nebula Drifters
        
        # --- Weaponry (Phase 5) ---
        self.weapon_registry = {} # {id: stats_dict}
        
        # --- Analytics Tracking (Phase 6) ---
        self.stats = {
            # Cumulative
            "total_req_income": 0,
            "total_req_expense": 0,
            "buildings_constructed": 0,
            "units_recruited": 0,
            "units_lost": 0,
            "battles_fought": 0,
            "battles_won": 0,
            "battles_drawn": 0,
            "damage_dealt": 0,
            "flux_storms": 0,
            
            # Turn-Based (Reset each turn)
            "turn_req_income": 0,
            "turn_req_expense": 0,
            "turn_construction_spend": 0,
            "turn_recruitment_spend": 0,
            "turn_units_recruited": 0,
            "turn_units_lost": 0,
            "turn_damage": 0,
            "turn_battles_fought": 0,
            "turn_battles_won": 0,
            "turn_diplomacy_actions": 0,
            "turn_constructions_completed": 0,
        }

        # --- Generic Mechanics System (Phase 9) ---
        self.mechanics = {} # {mechanic_id: config_dict}
        self.temp_modifiers = {} # {modifier_key: value} e.g. {"research_speed_mult": 1.2}
        self.passive_modifiers = {} # {modifier_key: aggregate_delta} e.g. {"global_damage_mult": 0.1}
        if self.universe_name:
            self._load_assigned_mechanics()

    def _load_assigned_mechanics(self):
        """Loads mechanics assigned to this faction from the universe registry."""
        import os
        import json
        
        # Path is somewhat hardcoded based on directory structure convention
        # universes/{universe}/factions/mechanics_registry.json
        # We assume CWD is project root or we can find it relative to this file?
        # Ideally using a tailored config loader, but direct file access for now.
        
        registry_path = f"universes/{self.universe_name}/factions/mechanics_registry.json"
        
        if not os.path.exists(registry_path):
            # Try absolute path from project root if running from src
            registry_path = os.path.join(os.getcwd(), registry_path)
            
        if os.path.exists(registry_path):
            try:
                with open(registry_path, 'r') as f:
                    data = json.load(f)
                    
                assignments = data.get("assignments", {}).get(self.name, [])
                all_mechanics = {m["id"]: m for m in data.get("mechanics", [])}
                
                for mech_id in assignments:
                    if mech_id in all_mechanics:
                        self.add_mechanic(mech_id, all_mechanics[mech_id])
                        
            except Exception as e:
                print(f"[Faction] Failed to load mechanics for {self.name}: {e}")

    def add_mechanic(self, mechanic_id, config):
        """Activates a mechanic for this faction."""
        self.mechanics[mechanic_id] = config

    def has_mechanic(self, mechanic_id):
        """Checks if a mechanic is active."""
        return mechanic_id in self.mechanics

    def get_mechanic_config(self, mechanic_id):
        """Returns the config for a specific mechanic."""
        return self.mechanics.get(mechanic_id, {})

    def get_modifier(self, key, default=1.0):
        """
        Standardized accessor for faction-wide modifiers.
        Combines persistent quirks with temporary mechanic bonuses.
        """
        # 1. Start with quirk-based attribute if it exists
        base_val = getattr(self, key, default)
        
        # 2. Add passive technology modifiers (+10% -> 0.1)
        passive_delta = self.passive_modifiers.get(key, 0.0)
        
        # 3. Multiply by temporary mechanic modifier if present
        # Note: keys in temp_modifiers usually end in '_mult' or match exactly
        temp_mult = self.temp_modifiers.get(key, 1.0)
        
        return base_val * (1.0 + passive_delta) * temp_mult

    def reset_turn_stats(self):
        """Resets turn-based counters at the start of a new turn."""
        for k in self.stats:
            if k.startswith("turn_"):
                self.stats[k] = 0
        
    def unlock_tech(self, tech_name, turn=0, tech_manager=None):
        if self.logger:
            self.logger.info(f"[Tech] {self.name} is unlocking technology: {tech_name}")
            
        if tech_name not in self.unlocked_techs:
            self.unlocked_techs.append(tech_name)
            self.tech_unlocked_turns[tech_name] = turn
            
            # Apply Passive Effects (Phase 107)
            if tech_manager:
                effects = tech_manager.get_tech_effects(tech_name)
                if not effects and self.logger:
                    self.logger.debug(f"[Tech] No effects found for {tech_name}")
                
                for e_str in effects:
                    mod = tech_manager.parse_effect_to_modifier(e_str)
                    if mod:
                        key, val = mod
                        self.passive_modifiers[key] = self.passive_modifiers.get(key, 0.0) + val
                        msg = f"[Tech] {self.name} applied PASSIVE: {tech_name} -> {key} ({val:+})"
                        if self.logger:
                            self.logger.info(msg)
                        else:
                            # Fallback if logger not initialized (unlikely in sim)
                            print(msg)
                    else:
                        # Warning for failed parse already handled in TechManager or could log here
                        pass
            elif tech_name != "None":
                 # Low-priority warning if tech_manager is missing for a real tech
                 if self.logger:
                     self.logger.debug(f"[Faction] unlock_tech('{tech_name}') called without tech_manager; skipping passives.")            
    def earn_intel(self, amount, source="combat", reason="Contact with enemy"):
        """Increments intel points and logs event."""
        self.intel_points += amount
        self.learning_history.setdefault('intel_events', []).append({
            'turn': getattr(self, 'current_turn', 0),
            'amount': amount,
            'source': source,
            'reason': reason
        })
        msg = f"[INTEL] {self.name} earned {amount} IP from {source}"
        if self.logger:
            self.logger.info(msg)
        else:
            print(msg)

    def spend_intel(self, amount, tech_id):
        """Deducts intel points if available."""
        if self.intel_points >= amount:
            self.intel_points -= amount
            return True
        return False

    def queue_adaptation(self, tech_id, cost, research_turns=3):
        """Adds a hybrid tech to the adaptation queue."""
        self.pending_adaptations.append({
            "tech_id": tech_id,
            "cost": cost,
            "turns_left": research_turns,
            "status": "pending"
        })

    def register_salvaged_blueprint(self, blueprint_id, quality, source_faction, turn):
        self.salvaged_blueprints[blueprint_id] = {
            "quality": quality,
            "salvage_turn": turn,
            "source_faction": source_faction
        }
        
    def register_stolen_blueprint(self, blueprint_id, source_faction, turn):
        self.stolen_blueprints[blueprint_id] = {
            "theft_turn": turn,
            "source_faction": source_faction
        }
        
    def register_shared_blueprint(self, blueprint_id, source_faction, turn):
        self.shared_blueprints[blueprint_id] = {
            "share_turn": turn,
            "source_faction": source_faction
        }
        
    def get_all_acquired_blueprints(self):
        return {
            "salvaged": self.salvaged_blueprints,
            "stolen": self.stolen_blueprints,
            "shared": self.shared_blueprints
        }
            
    def has_tech(self, tech_name):
        return tech_name in self.unlocked_techs

        
    def add_income(self, req):
        self.requisition += req
        
        # Track
        self.stats["total_req_income"] += req
        self.stats["turn_req_income"] += req
        
    def construct_building(self, planet, building_id):
        # Validation
        if building_id not in get_building_database():
            return False
            
        b_data = get_building_database()[building_id]
        cost = b_data.get("cost", 1000)
        
        # Check Affordability
        if not self.can_afford(cost):
            return False
            
        # Determine Placement Type
        is_orbital = False
        desc = b_data.get("effects", {}).get("description", "")
        if "Unlocks Space Ship Construction" in desc or b_data.get("naval_slots", 0) > 0 or "Shipyard" in b_data.get("name", ""):
            is_orbital = True

        b_tier = b_data.get("tier", 1)
            
        # Check Slots on Nodes (Preferred for Ground)
        target_node = None
        if hasattr(planet, 'provinces') and planet.provinces and not is_orbital:
            # Prioritize Capital -> Hubs -> Others
            sorted_nodes = sorted(planet.provinces, key=lambda n: (n.type != "Capital", n.type != "ProvinceCapital"))
            
            for node in sorted_nodes:
                # Tier Check
                if b_tier > getattr(node, 'max_tier', 5):
                     continue

                # Phase 17c: Granular Siege Locking (Node Siege)
                if getattr(node, 'is_sieged', False):
                    continue
                    
                # Check actual slots on the node
                queued_count = sum(1 for q in planet.construction_queue if q.get("node_id") == node.id)
                if len(node.buildings) + queued_count < node.building_slots:
                    target_node = node
                    break
        
        # Fallback for abstract planets (Orbit/Global) OR if no ground slots found
        if not target_node:
             # If it's a ground building and we have provinces but no slots, we should arguably FAIL rather than putting it in orbit?
             # But the user said "mines and so on" which are ground.
             # If strictly Orbit-only logic is desired for "Planet" slot, we check IS_ORBITAL.
             # However, current engine uses planet.buildings as overflow for ground too.
             # But user explicitly said "space doc on space part... ground troops in cities".
             # So if it's Ground (not is_orbital) and we found no node slots, we should Fail/Return False?
             # Or treat "Planet" as "High Orbit" which can hold anything?
             # Let's try attempting to respect the separation.
             
             if not is_orbital and hasattr(planet, 'provinces') and planet.provinces:
                 # If we have provinces (Map Mode) but couldn't place it, implies full.
                 # Do not spill over to Orbit unless it's truly orbital.
                 return False

             # Phase 17c: Orbital Siege blocks abstract buildings
             if getattr(planet, 'is_sieged', False):
                 return False
                 
             if len(planet.buildings) + len(planet.construction_queue) >= planet.building_slots:
                return False
             
        # Execute
        self.deduct_cost(cost)
        self.track_construction(cost) # Analytics Hook
        
        task = {
            "id": building_id,
            "turns_left": b_data.get("turns", 2)
        }
        if target_node:
            task["node_id"] = target_node.id
            
        planet.construction_queue.append(task)
        return True
        
    def can_afford(self, cost_req):
        return self.requisition >= cost_req
        
    def deduct_cost(self, cost_req):
        self.requisition -= cost_req
        
        # Track Generic Expense
        self.stats["total_req_expense"] += cost_req
        self.stats["turn_req_expense"] += cost_req

    def track_construction(self, cost):
        """Explicit tracker for construction to categorize expense."""
        self.stats["buildings_constructed"] += 1
        self.stats["turn_construction_spend"] += cost
        
    def track_recruitment(self, cost, count=1):
        """Explicit tracker for recruitment."""
        self.stats["units_recruited"] += count
        self.stats["turn_units_recruited"] += count
        self.stats["turn_recruitment_spend"] += cost


    def serialize_learning_data(self):
        """Returns learning history as JSON-serializable dict."""
        data = {
            'learning_history': self.learning_history,
            'last_adaptation_turn': self.last_adaptation_turn,
            'poor_performance_streak': self.poor_performance_streak,
            'intel_points': self.intel_points,
            'pending_adaptations': self.pending_adaptations,
            'salvaged_blueprints': self.salvaged_blueprints,
            'stolen_blueprints': self.stolen_blueprints,
            'shared_blueprints': self.shared_blueprints,
            # Mechanics
            'conviction_stacks': self.conviction_stacks,
            'biomass_pool': self.biomass_pool
        }
        if self.learned_personality:
            # Handle conversion if it's an object or already a dict
            if hasattr(self.learned_personality, 'to_dict'):
                data['learned_personality'] = self.learned_personality.to_dict()
            elif hasattr(self.learned_personality, '__dict__'):
                data['learned_personality'] = self.learned_personality.__dict__
            else:
                data['learned_personality'] = self.learned_personality
        data["id"] = self.name
        data["uid"] = self.uid
        return data

    @property
    def is_alive(self) -> bool:
        """
        Determines if the faction is still active in the game.
        """
        return not getattr(self, '_is_eliminated', False)

    def mark_eliminated(self):
        """Marks the faction as eliminated."""
        self._is_eliminated = True

    def load_learning_data(self, data):
        """Restores learning history from saved data."""
        self.learning_history = data.get('learning_history', self.learning_history)
        self.last_adaptation_turn = data.get('last_adaptation_turn', 0)
        self.poor_performance_streak = data.get('poor_performance_streak', 0)
        self.intel_points = data.get('intel_points', 0)
        self.pending_adaptations = data.get('pending_adaptations', [])
        self.salvaged_blueprints = data.get('salvaged_blueprints', {})
        self.stolen_blueprints = data.get('stolen_blueprints', {})
        self.shared_blueprints = data.get('shared_blueprints', {})
        
        # Mechanics
        self.conviction_stacks = data.get('conviction_stacks', 0)
        self.biomass_pool = data.get('biomass_pool', 0)
        
        # We store the dict here; the AI manager will rehydrate it into a FactionPersonality object
        self.learned_personality = data.get('learned_personality')

    def load_from_registry(self, personality_id: str, universe_name: str):
        """
        Attempts to load personality definition from the active universe registry.
        """
        try:
             import importlib
             module_name = f"universes.{universe_name}.ai_personalities"
             
             # Check if module is already loaded to avoid reload overhead
             if module_name in sys.modules:
                 module = sys.modules[module_name]
             else:
                 module = importlib.import_module(module_name)
                 
             if hasattr(module, "get_personality"):
                 p = module.get_personality(personality_id)
                 if p:
                     self.learned_personality = p
                     msg = f"Loaded AI Personality '{p.name}' for {self.name}"
                     if self.logger:
                         self.logger.info(msg)
                     else:
                         print(msg)
                 else:
                     msg = f"Warning: Personality '{personality_id}' not found in {module_name}"
                     if self.logger:
                         self.logger.warning(msg)
                     else:
                         print(msg)
        except Exception as e:
             msg = f"Failed to load personality {personality_id} from {universe_name}: {e}"
             if self.logger:
                 self.logger.error(msg)
             else:
                 print(msg)



    def get_constructor_count(self) -> int:
        """Returns the number of active construction ships."""
        count = 0
        for fleet in getattr(self, 'fleets', []):
            if fleet.is_destroyed: continue
            for unit in fleet.units:
                if getattr(unit, 'unit_class', '') == 'constructor':
                    count += 1
        return count

    @property
    def learned_personality(self):
        """Returns the active personality profile."""
        return self._learned_personality

    @learned_personality.setter
    def learned_personality(self, value):
        """Updates personality and synchronizes data-driven quirks."""
        self._learned_personality = value
        
        # Sync attributes if personality has them
        attrs_to_sync = [
            'diplomacy_bonus', 'retreat_threshold_mod', 'research_multiplier',
            'evasion_rating', 'casualty_plunder_ratio',
            'navy_recruitment_mult', 'army_recruitment_mult',
            'biomass_hunger', 'threat_affinity',
            'expansion_focus', 'claim_cost_mult', 'robot_upkeep_mult',
            'on_kill_effect', 'preferred_tactics', 'carrier_bias',
            'admiral_skill_bias', 'tax_efficiency', 'navy_maintenance_mult'
        ]
        
        if value:
            for attr in attrs_to_sync:
                if hasattr(value, attr):
                    setattr(self, attr, getattr(value, attr))
                elif isinstance(value, dict) and attr in value:
                    setattr(self, attr, value[attr])

    def set_learned_personality(self, personality):
        """Legacy wrapper for backward compatibility."""
        self.learned_personality = personality

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Faction':
        """Hydrates a Faction from a dictionary (Save V2)."""
        faction = cls(
            name=data["name"],
            uid=data.get("uid"),
            initial_req=data.get("initial_requisition", 0)
        )
        faction.requisition = data.get("requisition", faction.requisition)
        faction.budgets = data.get("budgets", faction.budgets)
        faction.research_points = data.get("research_points", 0.0)
        faction.research_income = data.get("research_income", 0.0)
        
        # Hydrate Research Projects
        from src.models.research_project import ResearchProject
        
        # Load legacy active_research if present
        legacy_active = data.get("active_research")
        if legacy_active:
             if isinstance(legacy_active, dict):
                 faction.active_projects.append(ResearchProject.parse_obj(legacy_active))
             else:
                 faction.active_projects.append(legacy_active)
        
        # Load new active_projects
        active_proj_data = data.get("active_projects", [])
        for p_data in active_proj_data:
            if isinstance(p_data, dict):
                faction.active_projects.append(ResearchProject.parse_obj(p_data))
            else:
                faction.active_projects.append(p_data)
        
        # Deduplicate and Cap at 3
        faction.active_projects = faction.active_projects[:3]
        if faction.active_projects:
            faction.active_research = faction.active_projects[0]

        faction.research_queue = []
        for q_data in data.get("research_queue", []):
            if isinstance(q_data, dict):
                faction.research_queue.append(ResearchProject.parse_obj(q_data))
            else:
                faction.research_queue.append(q_data)
                faction.home_planet_name = data.get("home_planet_name")
        
        faction.stats = data.get("stats", faction.stats)
        faction.passive_modifiers = data.get("passive_modifiers", {})
        faction.temp_modifiers = data.get("temp_modifiers", {})
        
        faction.load_learning_data(data)
        
        return faction

    def get_id(self) -> str:
        """
        Returns the faction's legacy identifier (name).
        Used for backward compatibility with existing save files.
        
        Returns:
            The faction name as a string.
        """
        return self.name

    def get_uid(self) -> str:
        """
        Returns the faction's unique GUID.
        Used for the new persistent identification system.
        
        Returns:
            The faction's GUID as a string.
        """
        return self.uid

    def to_dict(self) -> dict:
        """Serializes faction state for Save V2."""
        data = self.serialize_with_uid()
        data.update(self.serialize_learning_data())
        data["stats"] = self.stats
        data["passive_modifiers"] = self.passive_modifiers
        data["temp_modifiers"] = self.temp_modifiers
        return data

    def serialize_with_uid(self) -> dict:
        """
        Serializes faction data including both legacy id and new uid.
        Used for saving faction state with dual-passport support.
        
        Returns:
            A dictionary containing faction data with both id and uid.
        """
        data = {
            "id": self.name,  # Legacy identifier
            "uid": self.uid,  # New GUID
            "name": self.name,
            "universe_name": self.universe_name,
            "requisition": self.requisition,
            "budgets": self.budgets,
            "research_points": self.research_points,
            "research_income": self.research_income,
            "research_queue": [p.dict() if hasattr(p, 'dict') else p for p in self.research_queue],
            "active_projects": [p.dict() if hasattr(p, 'dict') else p for p in self.active_projects],
            "active_research": self.active_research.dict() if hasattr(self.active_research, 'dict') else self.active_research,
            "unlocked_techs": self.unlocked_techs,
            "home_planet_name": self.home_planet_name,
            "personality_id": self.personality_id
        }
        return data

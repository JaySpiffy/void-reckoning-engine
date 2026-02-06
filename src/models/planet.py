import random
import math
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from src.core.simulation_topology import GraphNode
from src.core.hex_lib import Hex, HexGrid
from src.models.hex_node import HexNode
from src.models.unit import Unit
from src.factories.unit_factory import UnitFactory
from src.core.universe_data import UniverseDataManager
from src.models.army import ArmyGroup
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.engine.simulate_campaign import CampaignEngine

class Planet:
    def __init__(self, name, system, orbit_index, base_req=1000):
        """
        Initializes a Planet entity.
        
        Args:
            name (str): Planet name.
            system (StarSystem): Parent system reference.
            orbit_index (int): Distance from star (1-10).
            base_req (int): Base requisition income.
        """
        self.name = name
        self.system = system # Reference to Parent System
        self.orbit_index = orbit_index # Distance from Star (1-10)
        self.owner = "Neutral"
        self.defense_level = 0
        self.building_slots = 0
        self.buildings = [] 
        self.construction_queue = [] # List of {'id': str, 'turns_left': int}
        self.unit_queue = [] # List of {'bp': UnitBlueprint, 'turns_left': int, 'type': 'fleet'|'army'}
        self.max_queue_size = 5 # Phase 16: Queue Limit
        
        # Procedural Generation
        universe_data = UniverseDataManager.get_instance()
        planet_classes = universe_data.get_planet_classes()
        self.planet_class = random.choice(list(planet_classes.keys()))
        
        # Base Stats (Configurable)
        self.base_income_req = base_req
        self.garrison_strength = 0
        self.armies = [] # List of ArmyGroup objects (Phase 16)
        self.is_sieged = False
        self.garrison_capacity = 1 # Added for Phase 101
        self.naval_slots = 0 # Added for Phase 104
        self.army_slots = 1  # Added for Phase 16
        self.role = "CORE" # [Phase 1] Economic Specialization: CORE vs FRONTIER
        self.starbase = None # Local orbital starbase unit
        self._provinces = None # [Optim] Lazy Load
        
        # Optimization R3: Pre-Index Building Stats
        self._building_cache = {"income": 0, "maintenance": 0, "research": 0}
        
        # Apply Modifiers
        self.recalc_stats()

    def refresh_building_cache(self):
        """Aggregates bonuses from buildings on this planet into the cache. (Optimized R3)"""
        universe_data = UniverseDataManager.get_instance()
        building_db = universe_data.get_building_database()
        
        income = 0
        maintenance = 0
        research = 0
        garrison = 0
        naval = 0
        
        for b_id in self.buildings:
            if b_id in building_db:
                data = building_db[b_id]
                income += data.get("income_req", 0)
                maintenance += data.get("maintenance", 0)
                
                if "research_output" in data:
                    research += data["research_output"]
                elif "Research" in data.get("category", "") or "Lab" in b_id:
                     research += 10
                     
                # Legacy/Abstract Building sync (if any)
                garrison += data.get("garrison_bonus", 0)
                naval = max(naval, data.get("naval_slots", 0))
        
        self._building_cache = {
            "income": income,
            "maintenance": maintenance,
            "research": research,
            "garrison": garrison,
            "naval": naval
        }
        
    def available_production_slots(self) -> int:
        """Returns the number of free slots in the unit queue (Phase 16)."""
        return max(0, self.max_queue_size - len(self.unit_queue))
        
    def recalc_stats(self):
        universe_data = UniverseDataManager.get_instance()
        planet_classes = universe_data.get_planet_classes()
        data = planet_classes[self.planet_class]
        
        self.income_req = int(self.base_income_req * data["req_mod"])
        self.defense_level = max(0, data["def_mod"]) # Base natural defense
        self.building_slots = data["slots"]
        
        # Phase 101: Garrison Capacity
        self.garrison_capacity = 1
        # Phase 16: Dynamic Queue & Slot Scaling (Infrastructure based)
        self.max_queue_size = 3 # Base for any colony
        self.naval_slots = 0
        self.army_slots = 1 # Base army for any colony
        
        # 1. Scan Provinces for Node Capacities
        if hasattr(self, 'provinces') and self.provinces:
            for node in self.provinces:
                # Optimized R3: Refresh node cache if missing
                if not hasattr(node, '_building_cache'):
                    node.refresh_building_cache()
                
                node_cache = node._building_cache
                
                if node.type == "Capital" and node.terrain_type != "Ruins":
                    self.max_queue_size += 7 # Capitals bring huge logistics
                    self.army_slots += 1
                    self.naval_slots += 1 # Hub for orbital traffic
                elif node.type == "ProvinceCapital" and node.terrain_type != "Ruins":
                    self.max_queue_size += 2 
                    self.army_slots += 0.5 
                
                # 2. Use Cached Node Building Stats (Optimized R3)
                self.garrison_capacity += node_cache.get("garrison", 0)
                self.naval_slots += node_cache.get("naval", 0)
                self.max_queue_size += node_cache.get("queue", 0)
                self.army_slots += node_cache.get("army", 0)
        
        # Ensure whole numbers for slots
        self.army_slots = int(self.army_slots)
        
        # 3. Use Cached Planet Building Stats (Optimized R3)
        if not hasattr(self, '_building_cache'):
            self.refresh_building_cache()
            
        planet_cache = self._building_cache
        self.garrison_capacity += planet_cache.get("garrison", 0)
        self.naval_slots = max(self.naval_slots, planet_cache.get("naval", 0))
        
        # Phase 18: Starbase Synergy
        if self.starbase and self.starbase.faction == self.owner:
            self.starbase.naval_slots += self.naval_slots
            # We don't remove naval_slots from planet, but planet recruitment uses starbase slots now
        
        # Special Case: Bio-Morph Desolation (Persists)
        # We need a flag for this really, checking income_req == 0 is shaky if a modifier makes it 0.
        # But for now, if it was already deserialized as 0, keep it? 
        # Actually initializing new object here, so desolation logic happens in campaign flow.
        
    def spawn_garrison(self, faction, max_count=15):
        """Create PDF based on defense level."""
        # Check against basic unit templates mock-up or real ones
        # For now, we will create generic PDF units on the fly
        garrison_units = []
        
        # Scaling based on Defense Level and Max Count
        # If max_count is 50, Level 1 -> 16, Level 3 -> 50
        per_level = max(5, int(max_count / 3))
        count = self.defense_level * per_level
        # Hard clamp
        count = min(count, max_count)
        
        for i in range(count):
            # Generic PDF Unit
            roll = random.randint(1, 100)
            if roll < 50:
                u = UnitFactory.create_pdf("Conscript", faction)
            elif roll < 85:
                 u = UnitFactory.create_pdf("Regular", faction)
            else:
                 u = UnitFactory.create_pdf("Elite", faction)
            garrison_units.append(u)
            
        return garrison_units
        
    # Optimization 4.2: Event-Driven Economy Caching
    def update_economy_cache(self):
        """Recalculates cached economic values (base + buildings). (Optimized R3)"""
        # 1. Base Income
        base_income = self.income_req
        
        # 2. Planet Buildings (Use Cache)
        if not hasattr(self, '_building_cache'):
            self.refresh_building_cache()
            
        building_income = self._building_cache["income"]
        infrastructure_upkeep = self._building_cache["maintenance"]
        research_income = self._building_cache["research"]
        
        # 3. Province Node Buildings (Use Caches)
        province_income = 0
        if hasattr(self, '_provinces') and self._provinces:
            for node in self._provinces:
                if not hasattr(node, '_building_cache'):
                    node.refresh_building_cache()
                
                node_cache = node._building_cache
                province_income += node_cache["income"]
                infrastructure_upkeep += node_cache["maintenance"]
                research_income += node_cache["research"]

        self._cached_econ_output = {
             "base": base_income,
             "buildings": building_income, 
             "provinces": province_income,
             "total_gross": base_income + building_income + province_income,
             "research_output": research_income
        }
        self._cached_maintenance = infrastructure_upkeep

    def generate_resources(self):
        # Optimization 4.2: Use Cached Values
        if not hasattr(self, '_cached_econ_output'):
            self.update_economy_cache()
            
        cached = self._cached_econ_output
        base_income = cached["base"]
        building_income = cached["buildings"]
        province_income = cached["provinces"]
        
        # Phase 17c: Granular Siege Locking (Income Penalty)
        # Apply modifiers DYNAMICALLY on top of cached base values
        if self.is_sieged:
            base_income = int(base_income * 0.5)
            building_income = int(building_income * 0.5)
            # Province income penalty logic is simpler if we assume global siege affects all for now, 
            # or we re-iterate nodes if granular siege is critical.
            # For O(1) speed, we apply a flat 50% to province income if the planet is sieged.
            # (Granular node-level siege checks would require iterating nodes again, defeating the cache purpose).
            province_income = int(province_income * 0.5)
            
        # [PHASE 14] Ruins Penalty (Zero Income for destroyed cities)
        if hasattr(self, 'provinces'):
            for node in self.provinces:
                if node.terrain_type == "Ruins":
                    # We can't easily subtract from cached totals without re-indexing,
                    # but since update_economy_cache is called when raze happens, 
                    # we should ensure update_economy_cache handles it.
                    pass

        total_req = base_income + building_income + province_income
                        
        # [PHASE 6] Planet Resource Production Trace (Telemetry omitted for perf in hot loop, handled by Manager)
        # ...

        result = {
            "req": total_req,
            "research": cached.get("research_output", 0), # Pass specific output
            "breakdown": {
                "base": base_income,
                "buildings": building_income,
                "provinces": province_income
            },
            "infrastructure_upkeep": getattr(self, '_cached_maintenance', 0)
        }
        return result

    def process_queue(self, engine):
        """Advances production of units."""
        # if not self.unit_queue: return  <-- BUG FIX: Don't block construction!
        
        # Phase 16: Army Production Scaling (Navy moved to Starbases)
        max_army = max(1, self.army_slots)
        
        # High Wealth Throughput Boost (Phase 16)
        if self.owner in engine.factions:
            f_mgr = engine.factions[self.owner]
            if f_mgr.requisition > 100000:
                max_army *= 2

        army_slots_used = 0
        navy_slots_used = 0
        
        # Construction Progress (Sequential)
        if hasattr(self, 'construction_queue') and self.construction_queue:
            # Only advance the first item in the queue
            task = self.construction_queue[0]
            task["turns_left"] -= 1
            
            if task["turns_left"] <= 0:
                 # It's done, pop it
                 self._complete_construction_task(self.construction_queue.pop(0), engine)

        # Unit Production Progress
        completed_indices = []
        for i, job in enumerate(self.unit_queue):
            job_type = job.get("type")
            
            # 1. Determine if this job can progress this turn
            can_progress = False
            if job_type == "army":
                if army_slots_used < max_army:
                    can_progress = True
                    army_slots_used += 1
            # [FIX] Phase 14: Enable Naval Production on Planets
            elif job_type == "fleet":
                # Use naval_slots (Base + Buildings + Starbase Bonus)
                # Shipyards usually process 1-2 ships in parallel
                max_navy = max(1, self.naval_slots) if self.naval_slots > 0 else 0
                
                # Check usage (we need to track navy_slots_used separately)
                if navy_slots_used < max_navy:
                    can_progress = True
                    navy_slots_used += 1
            
            if not can_progress:
                continue
                
            # 2. Siege check
            target_node = job.get("node_reference")
            if target_node and getattr(target_node, 'is_sieged', False):
                continue

            # 3. Progress Job
            job["turns_left"] -= 1
            
            if job["turns_left"] <= 0:
                completed_indices.append(i)
        
        # 4. Finalize Completed Jobs
        # We finalize them AFTER the progress loop to avoid modifying lists while iterating
        # (though we are just popping by index later)
        for i in completed_indices:
            self._finalize_job(self.unit_queue[i], engine)
            
        # 5. Remove completed jobs (in reverse order to preserve indices)
        for i in sorted(completed_indices, reverse=True):
            self.unit_queue.pop(i)

    def _complete_construction_task(self, task, engine):
        """Finalizes a building construction."""
        b_id = task["id"]
        node_id = task.get("node_id")
        
        target_container = self.buildings
        location_name = self.name
        
        if node_id and hasattr(self, 'provinces'):
            for node in self.provinces:
                if node.id == node_id:
                    target_container = node.buildings
                    location_name = f"{self.name} ({node.name})"
                    break
                    
        if b_id not in target_container:
            target_container.append(b_id)
            print(f"  > [BUILD] CONSTRUCTION COMPLETE: {b_id} on {location_name}")
            
            # Optimization R3: Update Stat Cache first
            if node_id:
                # Refresh specific node cache
                for node in self.provinces:
                    if node.id == node_id:
                        node.refresh_building_cache()
                        break
            else:
                # Refresh planet cache
                self.refresh_building_cache()
                
            # Optimization 4.2: Update Economy Cache
            self.update_economy_cache()
            
            if engine.telemetry:
                from src.core.constants import get_building_category
                engine.telemetry.log_event(
                    EventCategory.CONSTRUCTION,
                    "building_completed",
                    {
                        "building_id": b_id,
                        "building_type": get_building_category(b_id),
                        "building": b_id, 
                        "location": location_name, 
                        "planet": self.name
                    },
                    turn=engine.turn_counter,
                    faction=self.owner
                )

    def _finalize_job(self, job, engine):
        """Finalizes a production job and places the unit."""
        bp = job["bp"]
        job_type = job["type"]
        # print(f"  > [PROD] PRODUCTION COMPLETE: {bp.name} on {self.name} ({job_type})")
        
        if engine.telemetry:
            engine.telemetry.log_event(
                EventCategory.CONSTRUCTION,
                "unit_production_completed",
                {
                    "unit": bp.name, 
                    "type": job_type, 
                    "planet": self.name,
                    "turn": engine.turn_counter
                },
                turn=engine.turn_counter,
                faction=self.owner
            )
            
            engine.telemetry.log_event(
                EventCategory.CONSTRUCTION,
                "unit_created",
                {"unit": bp.name, "type": job_type, "planet": self.name},
                turn=engine.turn_counter,
                faction=self.owner
            )

        if engine.telemetry:
            engine.telemetry.log_event(
                EventCategory.CONSTRUCTION, 
                "unit_built", 
                {"unit": bp.name, "type": job_type, "location": self.name},
                turn=engine.turn_counter, 
                faction=self.owner
            )
        
        if job_type == "fleet":
            orbit_node = self.node_reference
            if not orbit_node: return
            
            target_fleet = None
            target_id = job.get("target_fleet_id")
            
            # Try to find precise target fleet
            if target_id:
                for f in engine.fleets:
                    if f.id == target_id and not f.is_destroyed:
                        target_fleet = f
                        break
            
            # Fallback to local merge
            if not target_fleet:
                for f in engine.fleets:
                    if f.faction == self.owner and f.location == orbit_node and not f.destination:
                        if len(f.units) < engine.max_fleet_size:
                            target_fleet = f
                            break
            
            if not target_fleet:
                # Use engine/asset_manager to generate deterministic ID
                fid = target_id # If None, AssetManager will generate one
                target_fleet = engine.create_fleet(self.owner, orbit_node, [], fid=fid)
                
            target_fleet.add_unit(bp)
            
        elif job_type == "army":
            # Phase 16: Spread spawns across military infrastructure
            spawn_nodes = [n for n in self.provinces if n.type in ["Capital", "ProvinceCapital"]]
            # Add nodes with military buildings
            for n in self.provinces:
                if any("Barracks" in b or "Academy" in b or "Training" in b for b in n.buildings):
                    if n not in spawn_nodes:
                        spawn_nodes.append(n)
            
            # Choose best node (Capital priority, then ProvinceCapital)
            # Or just pick the first available one where we have a building?
            # For simplicity, pick Capital if available, else a Province Capital
            spawn_node = next((n for n in spawn_nodes if n.type == "Capital"), None)
            if not spawn_node:
                spawn_node = next((n for n in spawn_nodes if n.type == "ProvinceCapital"), None)
            if not spawn_node and spawn_nodes:
                spawn_node = spawn_nodes[0]
            
            target_node = spawn_node if spawn_node else (self.provinces[0] if self.provinces else None)
            if not target_node: return
            
            # Clone Unit (Blueprints are templates)
            from src.combat.combat_simulator import Unit # Local import to be safe
            new_unit = UnitFactory.create_from_blueprint(bp, self.owner)
            
            target_army = None
            
            # Retrieve max_land_army_size from config (default 200)
            stack_limit = 200
            if hasattr(engine, 'game_config') and getattr(engine, 'game_config', None):
                 # Handle if game_config is dict or object
                 if isinstance(engine.game_config, dict):
                      stack_limit = engine.game_config.get("units", {}).get("max_land_army_size", 200)
                 elif hasattr(engine.game_config, 'units'):
                      stack_limit = getattr(engine.game_config.units, 'max_land_army_size', 200)

            for ag in self.armies:
                if ag.location == target_node and ag.faction == self.owner and not ag.is_destroyed:
                    if len(ag.units) < stack_limit:
                        target_army = ag
                        break
            
            if target_army:
                target_army.units.append(new_unit)
            else:
                # Use engine.create_army for deterministic ID and registration
                new_ag = engine.create_army(self.owner, target_node, [new_unit], aid=None)
                if target_node:
                    if not hasattr(target_node, 'armies'): target_node.armies = []
                    # create_army already appends to location.armies if it's a node/planet? 
                    # AssetManager: if hasattr(location, 'armies'): location.armies.append(a)
                    # AssetManager handles the appending to location armies.
                    # But capital_node might be the location.
                    pass 
                
                # Check if AssetManager added it to self.armies (Planet-level list)
                # AssetManager uses location.armies.
                # If location is capital_node, it adds to capital_node.armies.
                # It does NOT automatically add to planet.armies if location is a node.
                # So we need to ensure it's in self.armies too.
                if new_ag not in self.armies:
                     self.armies.append(new_ag)

    def __repr__(self):
        return f"{self.name} [{self.owner}] Res: {self.income_req}R"

    def to_dict(self) -> Dict[str, Any]:
        """Serializes planet state for Save V2."""
        return {
            "name": self.name,
            "owner": self.owner,
            "system_name": self.system.name if hasattr(self.system, "name") else str(self.system),
            "orbit_index": self.orbit_index,
            "base_income_req": self.base_income_req,
            "defense_level": self.defense_level,
            "building_slots": self.building_slots,
            "buildings": self.buildings,
            "construction_queue": self.construction_queue,
            "unit_queue": self.unit_queue,
            "is_sieged": self.is_sieged,
            "role": self.role,
            "armies": [a.to_dict() for a in self.armies],
            "starbase": self.starbase.to_dict() if self.starbase else None,
            "provinces": [p.to_dict() for p in self.provinces] if self._provinces else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], system: Any) -> 'Planet':
        """Hydrates a Planet from a dictionary (Save V2)."""
        planet = cls(
            name=data["name"],
            system=system,
            orbit_index=data.get("orbit_index", 1),
            base_req=data.get("base_income_req", 1000)
        )
        planet.owner = data.get("owner", "Neutral")
        planet.defense_level = data.get("defense_level", 0)
        planet.building_slots = data.get("building_slots", 0)
        planet.buildings = data.get("buildings", [])
        planet.construction_queue = data.get("construction_queue", [])
        planet.unit_queue = data.get("unit_queue", [])
        planet.is_sieged = data.get("is_sieged", False)
        planet.role = data.get("role", "CORE")
        
        # Starbase hydration
        sb_data = data.get("starbase")
        if sb_data:
            from src.models.starbase import Starbase
            planet.starbase = Starbase.from_dict(sb_data, system)
            
        # Provinces hydration (Lazy check)
        prov_data = data.get("provinces")
        if prov_data:
            from src.core.simulation_topology import GraphNode
            planet._provinces = [GraphNode.from_dict(p) for p in prov_data]
            # [NOTE] Edges are lost in basic Save V2 serialization for nodes.
            # Usually handled by re-generating topology if critical, or 
            # by a second pass in PersistenceManager if we add edge serialization.
            
        return planet

    @property
    def provinces(self):
        """Lazy loads the province graph only when needed."""
        if not hasattr(self, '_provinces') or self._provinces is None:
            self._generate_hex_map_lazy()
        return self._provinces

    @provinces.setter
    def provinces(self, value):
        self._provinces = value

    def _generate_hex_map_lazy(self):
        """Generates the internal Hex Grid (Gladius Style)."""
        self._provinces = []
        self.hex_map = {} # (q, r) -> HexNode
        
        # 1. Config
        # Scale map size with building slots (proxy for planet size)
        # 5 slots ~ 20 hexes (Radius 2-3)
        # 20 slots ~ 100 hexes (Radius 5-6)
        target_count = 20 + (self.building_slots * 10)
        
        # Calculate radius needed to fit target_count
        # Hex count = 3n(n+1) + 1
        # n ~ sqrt(count/3)
        radius = int(math.sqrt(target_count / 3.0)) + 1
        
        center_hex = Hex(0, 0)
        generated_hexes = list(HexGrid.get_spiral(center_hex, radius))
        
        # Limit to target count to avoid over-generation, but ensure full rings are cleaner?
        # Let's just use the full spiral for completeness of rings
        
        for i, h in enumerate(generated_hexes):
            # Hex Node
            node_id = f"{self.name}_H{h.q}_{h.r}"
            node = HexNode(node_id, h.q, h.r, self.name)
            
            # Determine Terrain/Type
            dist = h.length()
            
            if dist == 0:
                node.type = "Capital"
                node.terrain_type = "City"
                node.name = f"{self.name} Prime"
                node.building_slots = 7
                node.max_tier = 5
            elif dist <= 1:
                node.type = "ProvinceCapital"
                node.terrain_type = "City"
                node.name = f"District {i}"
                node.max_tier = 4
                node.building_slots = 5
            elif dist >= radius:
                node.type = "LandingZone"
                node.terrain_type = "Wasteland"
                node.name = f"Drop Site {h.q},{h.r}"
                node.building_slots = 3
                node.max_tier = 2
            else:
                # Mid-range: Mix of Plains, Ruins, Forests, Mountains, Water
                rng = random.random()
                if rng < 0.15: # 15% Ruins
                    node.terrain_type = "Ruins"
                    node.type = "Wasteland" # Mechanically
                    node.feature = "Ancient Ruins"
                elif rng < 0.35: # 20% Forest
                    node.terrain_type = "Forest"
                    node.type = "Province"
                elif rng < 0.45: # 10% Mountain
                    node.terrain_type = "Mountain"
                    node.type = "Wasteland"
                    node.feature = "Crystalline Peaks"
                elif rng < 0.55: # 10% Water
                    node.terrain_type = "Water"
                    node.type = "Wasteland"
                    node.feature = "Acid Ocean"
                else: # 45% Plains
                    node.terrain_type = "Plains"
                    node.type = "Province"
                node.name = f"Sector {h.q},{h.r}"
            
            node.metadata["object"] = self
            node.metadata["system"] = self.system
            
            # Storage
            self.hex_map[(h.q, h.r)] = node
            self._provinces.append(node)
            
        # [Implicit Edges]
        # In a hex grid, edges are implicit. We don't necessarily need to store GraphEdge objects 
        # unless the legacy pathfinder demands it. 
        # For compatibility, we SHOULD generate edges between neighbors so standard graph algo works.
        
        for h, node in self.hex_map.items():
            h_obj = Hex(h[0], h[1])
            for neighbor_hex in h_obj.get_neighbors():
                neighbor_key = (neighbor_hex.q, neighbor_hex.r)
                if neighbor_key in self.hex_map:
                    neighbor_node = self.hex_map[neighbor_key]
                    node.add_edge(neighbor_node, distance=1)


        # 3. Link Capital to Orbit
        capital_node = next((n for n in self._provinces if n.type == "Capital"), None)
        # Fix: Ensure self.node_reference exists (it should, as Planet is a node or has one)
        orbital_node = getattr(self, "node_reference", None) 
        
        if capital_node and orbital_node:
            orbital_node.add_edge(capital_node, distance=5)
            capital_node.add_edge(orbital_node, distance=5)

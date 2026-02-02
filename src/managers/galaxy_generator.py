
import os
import random
import math
import copy
from typing import Dict, List, Any, Optional

from src.factories.unit_factory import UnitFactory
from src.factories.unit_factory import UnitFactory
import src.core.config as config
import src.core.constants as constants
from src.core.constants import AGREEMENT_NUMERALS
from src.utils.name_generator import generate_system_name
from src.models.star_system import StarSystem
from src.models.planet import Planet
from src.models.fleet import Fleet
from src.models.army import ArmyGroup
from src.models.unit import Unit # Fallback
from src.utils.unit_parser import parse_unit_file
from src.utils.profiler import profile_method
from src.core.universe_data import UniverseDataManager
from pathlib import Path
import logging
import json

logger = logging.getLogger(__name__)

_galaxy_rng = random.Random()

def init_galaxy_rng(seed: Optional[int] = None):
    """Initializes the galaxy RNG with a specific seed."""
    _galaxy_rng.seed(seed)

import multiprocessing

def _generate_topology_worker(system_data):
    """
    Worker function for parallel topology generation.
    Args:
        system_data: Tuple (system_obj, force_flag)
    Returns:
        system_obj: The system object with generated nodes (though usually objects aren't mutated across processes easily without return).
                    Actually, passing objects across processes pickles them. 
                    We need to return the modified object.
    """
    system, force = system_data
    # Initialize RNG state for this process/system if needed, 
    # but generate_topology uses deterministic math or system-local state?
    # It uses math.sqrt(i) etc. It does NOT use global RNG for the spiral itself, only for 'flavor' types (asteroids/nebula).
    # flavor types use `i % 10`. So it is deterministic.
    # We can just call the method.
    system.generate_topology(force=force)
    
    # [FIX] Break circular references to avoid RecursionError during pickling
    system.connections = [] 
    for p in system.planets:
        p.system = None
        
    return system

class GalaxyGenerator:
    """
    Handles the creation of the galaxy map, star systems, and initial population.
    Also manages unit blueprints and initial fleet spawning.
    """
    def __init__(self):
        self.systems = []
        self.all_planets = []
        self.points_db = {}
        self.unit_blueprints = {}
        self.navy_blueprints = {}
        self.army_blueprints = {}
        self.portals = [] # Phase 22: Tracked PortalNode instances

    def load_points_db(self) -> None:
        uni_config = UniverseDataManager.get_instance().universe_config
        if uni_config:
            path = uni_config.factions_dir / "unit_points_database.md"
        else:
            path = os.path.join(config.DATA_DIR, "unit_points_database.md")
            
        if not os.path.exists(path):
            logger.warning("Points DB not found.")
            return
            
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip().startswith("|") or "Unit Name" in line or "---" in line:
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) < 6: continue
                
                faction = parts[1].replace('*', '').strip().replace(' ', '_')
                name = parts[2].strip()
                try:
                    cost = int(parts[4])
                    key = (faction, name)
                    self.points_db[key] = cost
                except ValueError:
                    continue
        logger.info(f"Loaded {len(self.points_db)} point costs from database.")

    @profile_method
    def load_blueprints(self) -> None:
        logger.info("Loading Unit Blueprints...")
        uni_config = UniverseDataManager.get_instance().universe_config
        if uni_config:
             root_dirs = [uni_config.factions_dir]
             units_path = uni_config.universe_root / "units"
             logger.info(f"[DEBUG] Checking units path: {units_path} (Exists: {units_path.exists()})")
             if units_path.exists():
                 root_dirs.append(units_path)
             else:
                 logger.warning(f"[DEBUG] Units path {units_path} does not exist!")
        else:
             root_dirs = [config.DATA_DIR]
             logger.info(f"[DEBUG] No uni_config, using default DATA_DIR: {config.DATA_DIR}")
        
        logger.info(f"[DEBUG] load_blueprints root_dirs: {root_dirs}")
        
        count = 0
        for root_dir in root_dirs:
            # logger.debug(f"[DEBUG] Walking root_dir: {root_dir}")
            for r, d, f in os.walk(root_dir):
                rel = os.path.relpath(r, root_dir)
                parts = rel.split(os.sep)
                if len(parts) >= 1 and parts[0] != ".":
                    faction = parts[0]
                else:
                    faction = None # Allow root files, faction will be derived from file content

                if faction and faction not in self.unit_blueprints:
                    self.unit_blueprints[faction] = []
                    self.navy_blueprints[faction] = []
                    self.army_blueprints[faction] = []

                f.sort() # Ensure deterministic file order
                for file in f:
                    if file == "TRAITS_GUIDE.md": continue
                    
                    # Determine faction from filename if still unknown (e.g. templars_of_the_flux_roster.json)
                    file_faction = faction
                    if not file_faction:
                        # weak heuristic: try to match known factions or just rely on content
                        # We will defer to content loading
                        pass

                    if file.endswith(".md"):
                        # MD files usually imply directory structure for faction, but let's handle safety
                        current_fac = file_faction or "Unknown" 
                        u = parse_unit_file(os.path.join(r, file), current_fac)
                        if u:
                             # If Unit has faction, use it
                             final_fac = u.faction if u.faction != "Unknown" else current_fac
                             
                             # Ensure register exists
                             if final_fac not in self.unit_blueprints:
                                self.unit_blueprints[final_fac] = []
                                self.navy_blueprints[final_fac] = []
                                self.army_blueprints[final_fac] = []
                                
                             self._process_loaded_unit(u, final_fac, count)
                             count += 1
                    elif file.endswith(".json"):
                        if file in ["blueprint_registry.json", "faction_dna.json", 
                                    "faction_registry.json", "mechanics_registry.json", 
                                    "mechanics_schema.json", "traits_registry.json",
                                    "ability_registry.json", "technology_registry.json",
                                    "tech_dna.json", "tech_unlock_map.json",
                                    "building_registry.json", "building_dna.json",
                                    "portal_config.json", "physics_profile.json",
                                    "game_data.json", "config.json",
                                    "weapon_registry.json", "weapon_dna.json"]:
                            continue

                        # JSON Unit/Roster Support
                        try:
                            # logger.debug(f"[DEBUG] Found JSON file: {file} in {r}")
                            filepath = os.path.join(r, file)
                            with open(filepath, 'r', encoding='utf-8') as jf:
                                data = json.load(jf)
                            
                            # print(f"[DEBUG] Loaded JSON data from {file}: {str(data)[:100]}...")
                                
                            units_to_process = []
                            if isinstance(data, list):
                                units_to_process = data
                            elif isinstance(data, dict):
                                # [FIX] Skip faction metadata files that aren't unit rosters
                                if "traits" in file.lower() and "faction" in file.lower():
                                    continue
                                    
                                if "name" in data and ("stats" in data or "base_stats" in data):
                                    units_to_process = [data]
                                else:
                                    units_to_process = list(data.values())
                                    
                            for u_data in units_to_process:
                                 if not isinstance(u_data, dict): continue
                                 
                                 # Detect Faction
                                 u_faction = u_data.get("faction", faction) # Prefer JSON, fallback to dir
                                 if not u_faction: 
                                     # Last resort: filename inference
                                     if "zealot" in file.lower(): u_faction = "Templars_of_the_Flux"
                                     # ... generic fallback
                                     else: u_faction = "Unknown"
                                     
                                 name = u_data.get("name", "Unknown")
                                 u_type = u_data.get("type", "Infantry")
                                 unit_class = u_data.get("unit_class", "infantry") 
                                 domain = u_data.get("domain", "ground")
                                 
                                 # Stats Extraction
                                 stats = u_data.get("base_stats", u_data.get("stats", {}))
                                 hp = stats.get("hp", 10)
                                 
                                 # Accuracy handling (BS/WS)
                                 # We use ma/md if present, else accuracy, else default 40
                                 ma = stats.get("ma") or stats.get("accuracy") or 40
                                 md = stats.get("md") or stats.get("accuracy") or 40
                                 
                                 damage = stats.get("damage", 5)
                                 armor = stats.get("armor", 0)
                                 cost = u_data.get("cost", 100)
                                 shield = stats.get("shield", 0)
                                 mv = stats.get("speed") or stats.get("movement") or 6
                                 
                                 traits = u_data.get("traits", [])
                                 abilities = u_data.get("abilities", {})
                                 
                                 # Detect Ship vs Regiment
                                 is_ship_unit = False
                                 naval_types = ["ship", "fighter", "frigate", "destroyer", "cruiser", "battleship", "titan", "escort", "grand_cruiser", "battlecruiser", "strike_craft", "transport"]
                                 
                                 if domain.lower() == "space":
                                     is_ship_unit = True
                                 elif any(nt in u_type.lower() for nt in naval_types):
                                     is_ship_unit = True
                                 elif "fleet" in u_type.lower():
                                     is_ship_unit = True

                                 u = None
                                 # Prepare Kwargs
                                 unit_kwargs = {
                                     "ma": ma,
                                     "md": md, # Note: Unit.__init__ kwargs handling for stats might use 'md' if StatsComponent created
                                     "hp": hp,
                                     "armor": armor,
                                     "damage": damage,
                                     "cost": cost,
                                     "unit_class": unit_class,
                                     "movement_points": mv,
                                     "expanded_stats": stats
                                 }
                                 
                                 # We need to ensure we don't pass args that cause conflicts or aren't used
                                 # Unit.__init__ stores kwargs.
                                 
                                 u = None
                                 if is_ship_unit:
                                     from src.models.unit import Ship
                                     u = Ship(name, u_faction, shield=shield, domain="space", **unit_kwargs)
                                 else:
                                     from src.models.unit import Regiment
                                     u = Regiment(name, u_faction, domain="ground", **unit_kwargs)
                                     
                                 # Manually inject Trait/Abilities Component
                                 if traits or abilities:
                                     from src.combat.components.trait_component import TraitComponent
                                     # Convert abilities dict {'Name': True} to what TraitComponent expects?
                                     # TraitComponent(traits, abilities)
                                     u.add_component(TraitComponent(traits=traits, abilities=abilities))
                                 
                                 # Handle Components Data (if present in JSON)
                                 comps_data = u_data.get("components")
                                 if comps_data:
                                     # Note: Intricate component parsing is handled by UnitFactory._finalize_unit or specific services
                                     pass 

                                     
                                 if "elemental_dna" in u_data:
                                     u.elemental_dna = u_data["elemental_dna"]
                                     
                                 if "blueprint_id" in u_data:
                                     u.blueprint_id = u_data["blueprint_id"]
                                 
                                 # Ensure faction list exists in dict
                                 if u_faction not in self.unit_blueprints:
                                    logger.info(f"[DEBUG] Registering new faction bucket: {u_faction}")
                                    self.unit_blueprints[u_faction] = []
                                    self.navy_blueprints[u_faction] = []
                                    self.army_blueprints[u_faction] = []

                                 self._process_loaded_unit(u, u_faction, count)
                                 logger.info(f"[DEBUG] Registered unit {u.name} for {u_faction}")
                                 count += 1
                        except Exception as e:
                            logger.error(f"[ERROR] Failed to load JSON unit file {file}: {e}")
                            import traceback
                            traceback.print_exc()

        logger.info(f"Loaded {count} unit blueprints.")
        
        # Phase: Faction Inheritance
        # Allow factions to inherit blueprints from another if defined in registry
        try:
            registry = UniverseDataManager.get_instance().get_faction_registry()
            # Ensure all factions in registry have entries
            for faction in registry:
                if faction not in self.unit_blueprints:
                    self.unit_blueprints[faction] = []
                    self.navy_blueprints[faction] = []
                    self.army_blueprints[faction] = []

            for faction, data in registry.items():
                parent = data.get("inherits")
                if parent:
                    if parent in self.unit_blueprints:
                        logger.info(f"Faction '{faction}' inherits units from '{parent}'")
                        # Use sets to avoid duplicates
                        existing_names = {u.name for u in self.unit_blueprints[faction]}
                        for u in self.unit_blueprints[parent]:
                            if u.name not in existing_names:
                                self.unit_blueprints[faction].append(u)
                                if u.is_ship():
                                    self.navy_blueprints[faction].append(u)
                                else:
                                    self.army_blueprints[faction].append(u)
                    else:
                        logger.warning(f"Faction '{faction}' inherits from '{parent}' but parent has no blueprints.")
        except Exception as e:
            logger.error(f"Faction inheritance failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
        # Ensure deterministic order of blueprints
        for faction in self.unit_blueprints:
            self.unit_blueprints[faction].sort(key=lambda u: u.name)
            self.navy_blueprints[faction].sort(key=lambda u: u.name)
            self.army_blueprints[faction].sort(key=lambda u: u.name)

    def _process_loaded_unit(self, u, faction, count):
         cost = 0
         key = (faction, u.name)
         if key in self.points_db:
             cost = self.points_db[key]
         
         if cost == 0:
             u_clean = u.name.lower().replace(" ", "")
             for (db_fac, db_name), db_cost in self.points_db.items():
                 # Matches if both are same faction or db_fac is generic?
                 # Assuming db points are specific
                 if db_fac == faction:
                     db_clean = db_name.lower().replace(" ", "")
                     if db_clean in u_clean or u_clean in db_clean:
                         cost = db_cost
                         break
             
         if cost == 0:
              cost = int(u.base_hp * 0.5 + u.base_ma + u.base_damage + u.base_armor * 2)
              if cost < 10: cost = 10
         
         if u.cost <= 0: u.cost = cost
         u.requisition_cost = u.cost
         
         # DNA System: Finalize unit (Applies traits from registry)
         UnitFactory._finalize_unit(u)
         
         # [Fix] Multi-Faction Registration
         target_factions = [f.strip() for f in u.faction.split(',')]
         if not target_factions or target_factions == [""]: target_factions = [faction]
         
         for target_f in target_factions:
             if target_f not in self.unit_blueprints:
                 self.unit_blueprints[target_f] = []
                 self.navy_blueprints[target_f] = []
                 self.army_blueprints[target_f] = []

             self.unit_blueprints[target_f].append(u)
             if u.is_ship():
                 self.navy_blueprints[target_f].append(u)
             else:
                 self.army_blueprints[target_f].append(u)

    @profile_method
    def generate_galaxy(self, num_systems=20, min_planets=1, max_planets=5, base_req=2500):
        logger.info(f"Generating Galaxy with {num_systems} Star Systems (Planets: {min_planets}-{max_planets})...")
        self.systems = []
        self.all_planets = []
        existing_coords = set()
        
        # 1. Generate Systems
        for i in range(num_systems):
            s_name = generate_system_name(i+1, rng=_galaxy_rng)
            while True:
                x = _galaxy_rng.randint(0, 100)
                y = _galaxy_rng.randint(0, 100)
                if (x,y) not in existing_coords:
                    existing_coords.add((x,y))
                    break
            
            system = StarSystem(s_name, x, y)
            self.systems.append(system)
            
            # 2. Generate Planets in System
            num_planets = _galaxy_rng.randint(min_planets, max_planets)
            for j in range(num_planets):
                p_name = f"{s_name} {AGREEMENT_NUMERALS[j]}" if j < len(AGREEMENT_NUMERALS) else f"{s_name} {j+1}"
                if j == 0: p_name = s_name 
                
                planet = Planet(p_name, system, j+1, base_req=base_req)
                system.add_planet(planet)
                self.all_planets.append(planet)
                
                if planet.owner != "Neutral":
                    starter_building = None
                    if planet.owner == "Hegemony": starter_building = "PDF Barracks"
                    elif planet.owner.startswith("Chaos"): starter_building = "Cultist Coven"
                    elif planet.owner == "Marauders": starter_building = "Raiders Huts"
                    elif planet.owner == "Aaether-kini": starter_building = "Aspect Shrine"
                    elif planet.owner == "Tau_Empire": starter_building = "Drone Hub"
                    elif planet.owner == "Hierarchs": starter_building = "Awakening Chamber"
                    elif planet.owner == "Bio-Morphs": starter_building = "Reclamation Pool"
                    
                    if starter_building and starter_building in constants.get_building_database():
                        planet.buildings.append(starter_building)
                
        # 3. Generate Flux Lanes (MST)
        if self.systems:
            connected = {self.systems[0]}
            unconnected = set(self.systems[1:])
            
            while unconnected:
                best_dist = 999999
                best_pair = (None, None)
                for c_node in connected:
                    for u_node in unconnected:
                         dist_sq = (c_node.x - u_node.x)**2 + (c_node.y - u_node.y)**2
                         if dist_sq < best_dist:
                             best_dist = dist_sq
                             best_pair = (c_node, u_node)
                
                if best_pair[0] and best_pair[1]:
                    s1, s2 = best_pair
                    s1.connections.append(s2)
                    s2.connections.append(s1)
                    connected.add(s2)
                    unconnected.remove(s2)
                else:
                     break

            for s1 in self.systems:
                others = sorted(self.systems, key=lambda s2: ((s1.x-s2.x)**2 + (s1.y-s2.y)**2) if s1!=s2 else 999999)
                for s2 in others[:3]:
                    if s2 not in s1.connections:
                        s1.connections.append(s2)
                        s2.connections.append(s1)

        # 4. Generate Internal Topologies (Parallelized)
        # Optimization 4.1: Use Multiprocessing
        try:
            # Prepare arguments
            tasks = [(s, False) for s in self.systems]
            
            # Use 75% of CPU cores or at least 1, max 8
            cpu_count = multiprocessing.cpu_count()
            workers = max(1, min(8, int(cpu_count * 0.75)))
            
            # Optimization 4.1: Use Multiprocessing
            # [FIX] Check if we are in a daemon process (daemon processes cannot have children)
            if multiprocessing.current_process().daemon:
                logger.warning("Running in daemon process, falling back to sequential topology generation.")
                raise ChildProcessError("Cannot spawn children from daemon process")
                
            # [FIX] Capture connection topology before parallel processing kills the references
            # We map System Name -> List of Connected System Names
            connection_map = {s.name: [c.name for c in s.connections] for s in self.systems}
            
            # Use "spawn" context if on Windows to avoid issues, though default is usually fine for simple objects
            logger.info(f"Generating Topologies in parallel with {workers} workers...")
            with multiprocessing.Pool(processes=workers) as pool:
                # Map works by pickling inputs and unpickling outputs
                # This replaces the original system objects with the returned ones (which have nodes populated)
                # Important: We must update references in self.all_planets because those planet objects point to OLD system objects.
                # Since StarSystem holds planets, and we get back a NEW system object with (presumably) NEW planet objects inside it?
                # Yes, pickle creates a deep copy of the structure being pickled usually.
                processed_systems = pool.map(_generate_topology_worker, tasks)
                
            # REFERENCE RE-BINDING
            # We must update self.systems
            self.systems = processed_systems
            
            # [FIX] Restore Connections from Map
            # The returned systems have valid nodes but empty connections (stripped in worker)
            new_sys_map = {s.name: s for s in self.systems}
            for s in self.systems:
                # Restore the object references using the new system objects
                if s.name in connection_map:
                    s.connections = [new_sys_map[c_name] for c_name in connection_map[s.name] if c_name in new_sys_map]
            
            
            # And we must update self.all_planets to point to the new planets inside the new systems
            # Otherwise other managers accessing self.all_planets will modify old stale objects
            
            self.all_planets = []
            for s in self.systems:
                # Re-bind system back-reference just in case (though it should be preserved)
                for p in s.planets:
                    p.system = s
                    self.all_planets.append(p)
                    
            logger.info("Parallel Topology Generation Complete.")
            
        except Exception as e:
            logger.warning(f"Parallel Generation Failed ({e}), falling back to sequential.")
            import traceback
            traceback.print_exc()
            # Fallback
            for s in self.systems:
                s.generate_topology()

        # 5. Link Inter-System Flux Gates
        # Re-sync connections after parallel generation (pickle artifacts)
        sys_map = {s.name: s for s in self.systems}
        for s in self.systems:
            s.connections = [sys_map[c.name] for c in s.connections]

        total_links = 0
        for s in self.systems:
            available_wps = [n for n in s.nodes if n.type == "FluxPoint"]
            for i, neighbor in enumerate(s.connections):
                if i < len(available_wps):
                    wp = available_wps[i]
                    wp.metadata["target_system"] = neighbor
                    wp.name = f"Gate to {neighbor.name}"
                else:
                    logger.warning(f"System {s.name} has more connections ({len(s.connections)}) than FluxPoints ({len(available_wps)})!")

        for s1 in self.systems:
            for s1_node in s1.nodes:
                if s1_node.type == "FluxPoint":
                    target_sys = s1_node.metadata.get("target_system")
                    if target_sys:
                         target_wp = next((n for n in target_sys.nodes if n.type == "FluxPoint" and n.metadata.get("target_system") == s1), None)
                         if target_wp:
                             if not any(e.target == target_wp for e in s1_node.edges):
                                 s1_node.add_edge(target_wp, distance=10)
                                 target_wp.add_edge(s1_node, distance=10)
                                 total_links += 1
                         else:
                             # This is a critical failure point for connectivity
                             logger.debug(f"Failed to find return gate in {target_sys.name} facing {s1.name}")

        logger.info(f"Galaxy Connectivity: Linked {total_links} inter-system flux gates.")
                                 
        # 6. Portal Generation (Phase 22)
        try:
            from src.core.simulation_topology import PortalNode
            uni_config = UniverseDataManager.get_instance().universe_config
            portal_cfg = uni_config.load_portal_config()
            
            if portal_cfg.get("enable_portals"):
                logger.info("Generating Portals from Configuration...")
                
                # Phase 22.5: Handle portal_pairs
                raw_portals = portal_cfg.get("portals", [])
                
                # If portal_pairs exists, we assume they define local portals paired to other universes
                # Format of a pair: { "local_id": "p1", "target_uni": "targets", "target_id": "p1", "local_coords": [...], "target_coords": [...] }
                # We translate this into the standard portal dict structure.
                for pair in portal_cfg.get("portal_pairs", []):
                    # Validate basic pair structure or skip
                    if "local_id" in pair and "target_uni" in pair:
                        new_portal = {
                            "portal_id": pair["local_id"],
                            "source_coords": pair.get("local_coords", [50, 50]),
                            "dest_universe": pair["target_uni"],
                            "dest_coords": pair.get("target_coords", [50, 50]),
                            "placement_strategy": pair.get("placement_strategy", "nearest_system")
                        }
                        raw_portals.append(new_portal)

                for p_def in raw_portals:
                    portal_id = p_def["portal_id"]
                    source_coords = p_def["source_coords"] # [x, y]
                    dest_uni = p_def["dest_universe"]
                    dest_coords = p_def["dest_coords"]
                    strategy = p_def.get("placement_strategy", "nearest_system")
                    
                    # Create the node using the new PortalNode class
                    portal_node = PortalNode(
                        node_id=f"portal_{portal_id}",
                        name=f"Portal to {dest_uni}",
                        portal_dest_universe=dest_uni,
                        portal_dest_coords=tuple(dest_coords),
                        portal_id=portal_id
                    )
                    portal_node.position = tuple(source_coords)
                    portal_node.metadata["placement_strategy"] = strategy
                    
                    # Find host system based on strategy
                    host_sys = None
                    if self.systems:
                        if strategy == "galactic_core":
                            host_sys = min(self.systems, key=lambda s: (s.x - 50)**2 + (s.y - 50)**2)
                        elif strategy == "border_region":
                            rim = [s for s in self.systems if s.x > 75 or s.y > 75 or s.x < 25 or s.y < 25]
                            candidates = rim if rim else self.systems
                            host_sys = min(candidates, key=lambda s: (s.x - source_coords[0])**2 + (s.y - source_coords[1])**2)
                        elif strategy == "exact_coords":
                            # Check if a system is extremely close (within 5 units)
                            nearest = min(self.systems, key=lambda s: (s.x - source_coords[0])**2 + (s.y - source_coords[1])**2)
                            dist = math.sqrt((nearest.x - source_coords[0])**2 + (nearest.y - source_coords[1])**2)
                            if dist < 5.0:
                                host_sys = nearest
                        else: # nearest_system
                            host_sys = min(self.systems, key=lambda s: (s.x - source_coords[0])**2 + (s.y - source_coords[1])**2)
                    
                    if host_sys:
                        host_sys.nodes.append(portal_node)
                        # Connect portal to nearest node in the system bidirectionally
                        if host_sys.nodes:
                            target = host_sys.nodes[0]
                            portal_node.add_bidirectional_edge(target, distance=5)
                        logger.info(f"Created Portal {portal_id} in {host_sys.name} (Strategy: {strategy}) -> {dest_uni}")
                    else:
                        # Standalone portal node (exact_coords with no close system)
                        # We still need to link it to the nearest system for connectivity
                        if self.systems:
                            nearest = min(self.systems, key=lambda s: (s.x - source_coords[0])**2 + (s.y - source_coords[1])**2)
                            portal_node.add_bidirectional_edge(nearest.nodes[0], distance=10)
                        logger.info(f"Created Standalone Portal {portal_id} at {source_coords} (Strategy: {strategy}) -> {dest_uni}")
                            
                    self.portals.append(portal_node)
        except Exception as e:
            logger.error(f"Portal Generation Failed: {e}")

        return self.systems, self.all_planets

    def link_cross_universe_portals(self, other_gen, other_universe_name: str):
        """Creates bidirectional edges between portals in different universes."""
        from src.core.simulation_topology import GraphEdge
        count = 0
        for p in self.portals:
            target_uni = p.metadata.get("portal_dest_universe")
            if target_uni == other_universe_name:
                p_id = p.metadata.get("portal_id")
                # Find matching portal in other universe
                match = next((op for op in other_gen.portals if op.metadata.get("portal_id") == p_id), None)
                
                if match:
                    # Create bidirectional edge with high cost for inter-universe travel
                    p.add_bidirectional_edge(match, distance=50)
                    count += 1
                    logger.info(f"Linked Portal {p_id} ({UniverseDataManager.get_instance().universe_name} <-> {other_universe_name})")
        return count

    @profile_method
    def spawn_start_fleets(self, engine, num_fleets_per_faction: int = 1) -> None:
        if engine.logger:
            engine.logger.info("Spawning Starting Fleets...")
            # Diagnostic RNG Check
            chk = _galaxy_rng.randint(0, 999999)
            engine.logger.debug(f"[RNG] GalaxyGenerator State Check: {chk}")
        habitable_systems = [s for s in self.systems if s.planets]
        _galaxy_rng.shuffle(habitable_systems)
        faction_starts: Dict[str, Planet] = {}
        placed_systems = []
        
        for i, faction in enumerate(engine.faction_manager.get_faction_names()):
            start_system = None
            attempts = 0
            while attempts < 100:
                if not habitable_systems: break
                
                min_dist = 25.0
                if attempts > 50: min_dist = 15.0
                if attempts > 75: min_dist = 10.0
                
                candidate = _galaxy_rng.choice(habitable_systems)
                
                if not placed_systems:
                    start_system = candidate
                else:
                    too_close = False
                    for existing in placed_systems:
                        dist = math.sqrt((candidate.x - existing.x)**2 + (candidate.y - existing.y)**2)
                        if dist < min_dist:
                            too_close = True
                            break
                    if not too_close:
                        start_system = candidate
                
                if start_system: break
                attempts += 1
                
            if not start_system and habitable_systems:
                start_system = _galaxy_rng.choice(habitable_systems)
            
            if start_system:
                habitable_systems.remove(start_system)
                placed_systems.append(start_system)
                
                home_planet = start_system.planets[0]
                if faction in engine.factions:
                    engine.factions[faction].home_planet_name = home_planet.name
                
                # [FIX] Explicitly set System Owner for Dashboard Visibility
                start_system.owner = faction
                
                # Unification
                for sys_planet in start_system.planets:
                     engine.update_planet_ownership(sys_planet, faction)
                     
                     is_capital = (sys_planet == home_planet)
                     cap_node = None 
                     
                     if hasattr(sys_planet, 'provinces'):
                        for node in sys_planet.provinces:
                            if node.type == "Capital":
                                cap_node = node
                                if is_capital:
                                    node.tier = 2
                                    node.building_slots = 8
                                else:
                                    node.tier = 1
                                    node.building_slots = 4
                            elif node.type == "ProvinceCapital":
                                node.tier = 1
                                node.building_slots = 4
                
                     faction_reg = UniverseDataManager.get_instance().get_faction_registry()
                     starting_data = faction_reg.get(faction, {})
                     seed_b = starting_data.get("starting_building", "Bunker Network")
                     # 1. Place Ground Infrastructure (Capital City)
                     ground_buildings = [seed_b]
                     if is_capital:
                         ground_buildings.extend(["Administratum Hub", "Promethium Relay"])
                         
                         # [RESEARCH FIX] Ensure at least one research building is seeded
                         research_b = None
                         db = UniverseDataManager.get_instance().get_building_database()
                         for b_key, b_val in db.items():
                             if b_val.get("faction") == faction or b_val.get("faction") == faction.replace(" ", "_"):
                                 # We use the keyword logic from constants.py
                                 from src.core.constants import categorize_building
                                 if categorize_building(b_key, b_val) == "Research" and b_val.get("tier", 1) == 1:
                                     research_b = b_key
                                     break
                         
                         if research_b:
                             ground_buildings.append(research_b)
                         
                         if starting_data.get("use_starting_bunkers", True):
                             ground_buildings.append("Bunker Network")
                             
                     ground_target = cap_node.buildings if cap_node else sys_planet.buildings
                     ground_slots = cap_node.building_slots if cap_node else sys_planet.building_slots
                     
                     for b in ground_buildings:
                         if len(ground_target) < ground_slots:
                             ground_target.append(b)

                     # 2. Place Space Infrastructure (Orbit)
                     # Dynamic Shipyard Injection
                     shipyard_b = "Orbital Dock" # Fallback
                     
                     # Find a building for this faction that unlocks ships
                     db = UniverseDataManager.get_instance().get_building_database()
                     for b_key, b_val in db.items():
                         if b_val.get("faction") == faction or b_val.get("faction") == faction.replace(" ", "_"):
                             desc = b_val.get("effects", {}).get("description", "")
                             if "Unlocks Space Ship Construction" in desc:
                                 shipyard_b = b_key
                                 break
                     
                     
                     if not shipyard_b or shipyard_b == "Orbital Dock":
                         # Check if "Spaceport" exists as a generic fallback
                         if "Spaceport" in db: shipyard_b = "Spaceport"
                         else: shipyard_b = "Orbital Dock"

                     # Space infrastructure always goes to the Planet object (Orbit)
                     space_target = sys_planet.buildings
                     space_slots = sys_planet.building_slots
                     
                     # Force add if empty, otherwise respect slots
                     if len(space_target) < space_slots:
                         space_target.append(shipyard_b)
                     elif space_slots > 0:
                        # Overwrite last slot if full but critical
                        space_target[-1] = shipyard_b
                
                # 3. Place Initial Starbase Units (One per Owned Planet)
                from src.models.starbase import Starbase
                for sys_planet in start_system.planets:
                    if sys_planet.owner == faction:
                        new_sb = Starbase(f"{sys_planet.name} Station", faction, start_system, tier=1, under_construction=False)
                        sys_planet.starbase = new_sb
                        start_system.starbases.append(new_sb)
                        
                        # Wrap in static fleet for upkeep and combat
                        # Place fleet at the planet's orbital node
                        target_node = sys_planet.node_reference
                        if target_node:
                            engine.create_fleet(faction, target_node, units=[new_sb], fid=f"SB_{sys_planet.name}_{faction}")
                
                faction_starts[faction] = home_planet
                if engine.logger:
                    engine.logger.campaign(f"[SYSTEM] {faction} claims {start_system.name}")
            else:
                continue

            for i in range(num_fleets_per_faction):
                start_node = faction_starts[faction]
                fleet = Fleet(f"{faction} Battlefleet {i+1}", faction, start_node)
                
                navies = engine.navy_blueprints.get(faction, [])
                if engine.logger:
                     engine.logger.debug(f"[SPAWN] {faction} Navies available: {len(navies)} (First: {navies[0].name if navies else 'None'})")
                
                if navies:
                    # [FIX] Filter for Starter Ships only (Corvettes/Frigates) to respect Tech Progression
                    starter_ships = [s for s in navies if s.unit_class.lower() in ["corvette", "frigate", "fighter", "scout", "transport"]]
                    if not starter_ships: 
                        starter_ships = navies # Fallback if no low-tier defined
                    
                    num_ships = _galaxy_rng.randint(3, 5)
                    for _ in range(num_ships):
                        ship = _galaxy_rng.choice(starter_ships)
                        fleet.add_unit(ship)

                armies = engine.army_blueprints.get(faction, [])
                if not armies: armies = engine.unit_blueprints.get(faction, [])
                
                if armies:

                    ground_units = []
                    for _ in range(10):
                        bp = _galaxy_rng.choice(armies)
                        new_unit = copy.deepcopy(bp)
                        # Ensure DNA is intact/finalized if deepcopy missed anything or for safety
                        UnitFactory._finalize_unit(new_unit)
                        ground_units.append(new_unit)
                    
                    cap_node = next((n for n in start_node.provinces if n.type == "Capital"), start_node.provinces[0])
                    ag = ArmyGroup(f"{faction} Expeditionary Force {i+1}", faction, ground_units, cap_node)
                    start_node.armies.append(ag)
                    
                    if engine.logger:
                        engine.logger.debug(f"[SPAWN] embarking {ag.id} onto {fleet.id} (Size: {ag.get_total_size()})")

                    # Ensure fleet has capacity before attempting embark to avoid error logs
                    needed_capacity = ag.get_total_size()
                    
                    # Safety loop to add transports if needed
                    while fleet.transport_capacity < needed_capacity:
                         transport = next((u for u in engine.unit_blueprints.get(faction, []) if hasattr(u, 'transport_capacity') and u.transport_capacity > 0), None)
                         if not transport:
                             transport = UnitFactory.create_transport(faction)
                             transport.transport_capacity = 4 # Fallback defaults
                         fleet.add_unit(transport)

                    if not engine.battle_manager.embark_army(fleet, ag):
                        engine.logger.warning(f"[SPAWN] Failed to embark {ag.id} onto {fleet.id} despite capacity check (Cap: {fleet.transport_capacity} vs Need: {needed_capacity})")

                engine.register_fleet(fleet)

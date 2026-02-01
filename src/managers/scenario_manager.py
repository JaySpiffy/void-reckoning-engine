import os
import json
import random
import math
from typing import Dict, Any, List, Optional
from src.models.star_system import StarSystem
from src.models.planet import Planet
from src.models.faction import Faction
from src.core.constants import AGREEMENT_NUMERALS
from src.models.unit import Unit

class ScenarioManager:
    """
    Handles loading campaign scenarios from configuration files and 
    applying starting conditions to the galaxy.
    """
    def __init__(self, engine: Any):
        self.engine = engine
        self.logger = engine.logger

    def load_campaign_from_config(self, config_path: str) -> bool:
        """Loads a fresh campaign from a structure config file."""
        if not os.path.exists(config_path):
             self.logger.error(f"Campaign config not found: {config_path}")
             return False
             
        try:
            with open(config_path, 'r') as f:
                data = json.load(f)
                
            self.logger.campaign(f"Initializing Scenario: {data.get('name', 'Unknown')}")
            
            # 1. Starting Conditions
            sc = data.get("starting_conditions", {})
            self.apply_starting_conditions(sc)
            
            # 2. Victory Conditions
            self.engine.register_victory_conditions(data.get("victory_conditions", []))
            
            # 3. Missions
            self.engine.load_mission_sequence(data.get("missions", []))
            
            # 4. Economic Progression
            self.engine.stats_history = [] # Reset history for new scenario
            # (Note: economic_progression field might be used elsewhere)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load scenario config: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def apply_starting_conditions(self, conditions: Dict[str, Any]):
        """Sets up the galaxy and factions based on campaign conditions."""
        self.logger.campaign("[SCENARIO] Applying Starting Conditions...")
        
        # 1. Map Generation with Initializers
        map_state = conditions.get("map_state", {})
        initializers = map_state.get("initializers", [])
        
        if initializers:
             # Custom Seeding: Build specific systems from init defs
             self.engine.systems = []
             self.engine.all_planets = []
             
             self.logger.campaign(f"[SCENARIO] Seeding Galaxy with {len(initializers)} defined systems...")
             
             # Coordinate Tracker for collision avoidance
             existing_coords = set()
             rng_seed = self.engine.config.raw_config.get("simulation", {}).get("random_seed", 42)
             rng = random.Random(rng_seed)
             
             for idx, init_def in enumerate(initializers):
                 if isinstance(init_def, str): continue
                 
                 s_name = init_def.get("name", f"System {idx+1}")
                 
                 while True:
                    x = rng.randint(0, 100)
                    y = rng.randint(0, 100)
                    if (x,y) not in existing_coords:
                        existing_coords.add((x,y))
                        break
                        
                 system = StarSystem(s_name, x, y)
                 self.engine.systems.append(system)
                 
                 # Planets
                 planets_data = init_def.get("planets", [])
                 for p_idx, p_data in enumerate(planets_data):
                     p_name = p_data.get("name", f"{s_name} {AGREEMENT_NUMERALS[p_idx] if p_idx < len(AGREEMENT_NUMERALS) else p_idx+1}")
                     planet = Planet(p_name, system, p_idx+1, base_req=getattr(self.engine.config,'base_req', 2500))
                     
                     if "class" in p_data:
                         planet.type = p_data["class"]
                         
                     system.add_planet(planet)
                     self.engine.all_planets.append(planet)
             
             # Link Nodes
             self.engine.galaxy_generator.systems = self.engine.systems
             self.engine.galaxy_generator.all_planets = self.engine.all_planets
             self._link_seeded_systems(self.engine.systems, rng)
             
        else:
             # Default Gen
             count = map_state.get("systems", 30)
             self.engine.generate_galaxy(num_systems=count)
             
        # 2. Setup Factions & Assignments
        factions_config = conditions.get("factions", {})
        
        # Ensure Neutral exists
        if not self.engine.get_faction("Neutral"):
            from src.models.faction import Faction
            self.engine.add_faction(Faction("Neutral"))
            
        rng_seed = self.engine.config.raw_config.get("simulation", {}).get("random_seed", 42)
        rng = random.Random(rng_seed)

        for f_name, f_data in factions_config.items():
            if not self.engine.get_faction(f_name):
                from src.models.faction import Faction
                self.engine.add_faction(Faction(f_name))
                
            f_obj = self.engine.get_faction(f_name)
            # Config resources
            if "starting_resources" in f_data:
                for r, v in f_data["starting_resources"].items():
                     if hasattr(self.engine.economy_manager, "add_resource"):
                         self.engine.economy_manager.add_resource(f_name, r, v)
                     
            # Config Tech
            if "starting_tech" in f_data and hasattr(self.engine, 'tech_manager') and f_obj:
                for t in f_data["starting_tech"]:
                    f_obj.unlock_tech(t, turn=0, tech_manager=self.engine.tech_manager)
                    
            # 3. Planet Assignment
            homeworld = None
            assigned_planets = []
            
            if "starting_planets" in f_data:
                targets = f_data["starting_planets"]
                for p_name in targets:
                    target_p = next((p for p in self.engine.all_planets if p.name == p_name), None)
                    if target_p:
                        self.engine.update_planet_ownership(target_p, f_name)
                        target_p.colonized = True
                        assigned_planets.append(target_p)
                
            if assigned_planets:
                homeworld = assigned_planets[0]
            else:
                # Fallback Assignment
                candidates = [p for p in self.engine.all_planets if p.owner == "Neutral"]
                if candidates:
                    homeworld = rng.choice(candidates)
                    self.engine.update_planet_ownership(homeworld, f_name)
                    homeworld.colonized = True
            
            if homeworld:
                 f_obj = self.engine.get_faction(f_name)
                 if f_obj:
                     f_obj.home_planet_name = homeworld.name
                 
            # 4. Unit Spawning
            if "starting_units" in f_data and homeworld:
                fleet = self.engine.create_fleet(f_name, homeworld, [], fid=f"{f_name} Starting Fleet")
                for u_entry in f_data["starting_units"]:
                    u_type = u_entry.get("type", "Ship")
                    count = u_entry.get("count", 1)
                    
                    bp = next((b for b in self.engine.navy_blueprints.get(f_name, []) if b.name == u_type), None)
                    if not bp:
                        bp = next((b for b in self.engine.army_blueprints.get(f_name, []) if b.name == u_type), None)
                        
                    if bp:
                        for _ in range(count):
                             import copy
                             new_u = copy.deepcopy(bp)
                             if hasattr(new_u, 'finalize'): new_u.finalize() 
                             fleet.add_unit(new_u)
                    else:
                        for _ in range(count):
                            fleet.add_unit(Unit(u_type, "Ship"))
                            
                self.logger.campaign(f"[SPAWN] Spawned starting fleet for {f_name} at {homeworld.name}")

        self.engine.rebuild_planet_indices()

    def _link_seeded_systems(self, systems, rng):
        """Helper to link systems if custom seeded."""
        if not systems: return
        
        connected = {systems[0]}
        unconnected = set(systems[1:])
        
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

        for s1 in systems:
            others = sorted(systems, key=lambda s2: ((s1.x-s2.x)**2 + (s1.y-s2.y)**2) if s1!=s2 else 999999)
            for s2 in others[:3]:
                if s2 not in s1.connections:
                    s1.connections.append(s2)
                    s2.connections.append(s1)
        
        # Internal topologies
        for s in systems:
            s.generate_topology()
            for p in s.planets:
                p.generate_provinces()

import os
import json
import pickle
from typing import Any, Dict, List
from src.core.config import SAVES_DIR
from src.core.service_locator import ServiceLocator

class PersistenceManager:
    """
    Handles saving and loading the campaign state.
    Supports Legacy (Pickle) and Version 2 (JSON).
    """
    def __init__(self, engine: Any):
        self.engine = engine
        self.logger = engine.logger

    def save_campaign(self, filename: str = "autosave", version: int = 2) -> bool:
        """Saves current campaign state to a file."""
        save_dir = SAVES_DIR
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        extension = ".save" if version == 1 else ".json"
        filepath = os.path.join(save_dir, f"{filename}{extension}")
        
        try:
            if version == 1:
                state = {
                    "systems": self.engine.systems,
                    "fleets": self.engine.fleets,
                    "turn_counter": self.engine.turn_counter,
                    "factions": {f.name: f for f in self.engine.get_all_factions()}
                }
                with open(filepath, 'wb') as f:
                    pickle.dump(state, f)
            else:
                # Save Version 2 (JSON)
                state = {
                    "save_version": 2,
                    "turn_counter": self.engine.turn_counter,
                    "factions": [f.to_dict() for f in ServiceLocator.get("FactionRepository").get_all()],
                    "systems": [s.to_dict() for s in ServiceLocator.get("SystemRepository").get_all()],
                    "fleets": [f.to_dict() for f in ServiceLocator.get("FleetRepository").get_all() if not f.is_destroyed]
                }
                with open(filepath, 'w') as f:
                    json.dump(state, f, indent=4)
                    
            self.logger.info(f"Campaign saved to {filepath} (V{version})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save campaign: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

    def load_campaign(self, filename: str = "autosave") -> bool:
        """Loads campaign state from a file. Auto-detects version."""
        # Try JSON first
        json_path = os.path.join(SAVES_DIR, f"{filename}.json")
        pickle_path = os.path.join(SAVES_DIR, f"{filename}.save")
        
        if os.path.exists(json_path):
            return self._load_v2(json_path)
        elif os.path.exists(pickle_path):
            return self._load_v1(pickle_path)
        else:
            self.logger.error(f"Error: No save file found for {filename}")
            return False

    def _load_v1(self, filepath: str) -> bool:
        """Legacy Pickle Loader."""
        try:
            with open(filepath, 'rb') as f:
                state = pickle.load(f)
            
            self.engine.systems = state["systems"]
            self.engine.fleets = state["fleets"]
            self.engine.all_planets = []
            for s in self.engine.systems:
                self.engine.all_planets.extend(s.planets)
                
            self.engine.turn_counter = state["turn_counter"]
            self.engine.factions = state["factions"]
            
            self.logger.info(f"Campaign loaded (Legacy) from {filepath} (Turn {self.engine.turn_counter})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load legacy save: {e}")
            return False

    def _load_v2(self, filepath: str) -> bool:
        """Modern JSON Loader (Save Version 2)."""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            if state.get("save_version") != 2:
                self.logger.error(f"Invalid save version in {filepath}")
                return False
                
            self.engine.turn_counter = state["turn_counter"]
            
            # 1. Hydrate Factions
            from src.models.faction import Faction
            faction_repo = ServiceLocator.get("FactionRepository")
            for f_data in state.get("factions", []):
                faction = Faction.from_dict(f_data)
                faction_repo.save(faction)
            
            # 2. Hydrate Systems & Planets
            from src.models.star_system import StarSystem
            system_repo = ServiceLocator.get("SystemRepository")
            self.engine.systems = []
            self.engine.all_planets = []
            
            planet_lookup = {} # {name: planet_obj}
            
            for s_data in state.get("systems", []):
                system = StarSystem.from_dict(s_data)
                system_repo.save(system)
                self.engine.systems.append(system)
                for p in system.planets:
                    self.engine.all_planets.append(p)
                    planet_lookup[p.name] = p
            
            # 3. Hydrate Fleets
            from src.models.fleet import Fleet
            fleet_repo = ServiceLocator.get("FleetRepository")
            self.engine.fleets = []
            
            for fl_data in state.get("fleets", []):
                loc_name = fl_data.get("location_name")
                loc_obj = planet_lookup.get(loc_name)
                
                if not loc_obj:
                    # Fallback to first planet in first system if location lost
                    if self.engine.all_planets:
                        loc_obj = self.engine.all_planets[0]
                
                fleet = Fleet.from_dict(fl_data, loc_obj)
                
                # Link Destination
                dest_name = fl_data.get("destination_name")
                if dest_name:
                    fleet.destination = planet_lookup.get(dest_name)
                
                fleet_repo.save(fleet)
                self.engine.fleets.append(fleet)
                
            # 4. Resolve Cross-References (Armies, etc.)
            # Army hydration on planets
            from src.models.army import ArmyGroup
            for s_dict in state.get("systems", []):
                for p_dict in s_dict.get("planets", []):
                    planet = planet_lookup.get(p_dict["name"])
                    if not planet: continue
                    
                    planet.armies = []
                    for a_data in p_dict.get("armies", []):
                        loc_id = a_data.get("location_id")
                        loc_node = planet
                        if loc_id and planet.provinces:
                            loc_node = next((n for n in planet.provinces if n.id == loc_id), planet)
                        
                        army = ArmyGroup.from_dict(a_data, loc_node)
                        planet.armies.append(army)
                    
            # Army hydration in fleets
            for fl_dict in state.get("fleets", []):
                fleet = next((f for f in self.engine.fleets if f.id == fl_dict["id"]), None)
                if not fleet: continue
                
                fleet.cargo_armies = []
                for a_data in fl_dict.get("cargo_armies", []):
                    # Use fleet location as node reference
                    loc_node = fleet.location
                    if hasattr(fleet.location, "node_reference"):
                        loc_node = fleet.location.node_reference
                        
                    army = ArmyGroup.from_dict(a_data, loc_node)
                    army.transport_fleet = fleet
                    fleet.cargo_armies.append(army)

            # 5. Link System Connections
            for s_dict in state.get("systems", []):
                system = next((s for s in self.engine.systems if s.name == s_dict["name"]), None)
                if not system: continue
                
                system.connections = []
                for conn_name in s_dict.get("connections", []):
                    conn_sys = next((s for s in self.engine.systems if s.name == conn_name), None)
                    if conn_sys:
                        system.connections.append(conn_sys)
            
            # 6. Sync Engine Factions
            self.engine.factions = {f.name: f for f in faction_repo.get_all()}

            self.logger.info(f"Campaign loaded (V2) from {filepath} (Turn {self.engine.turn_counter})")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load V2 save: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False

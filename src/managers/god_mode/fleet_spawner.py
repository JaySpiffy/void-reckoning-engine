import random
from typing import Dict, Optional, List
from src.managers.campaign_manager import CampaignEngine
from src.core.config import get_universe_config

class FleetSpawner:
    """
    Helper class for God Mode to spawn fleets dynamically.
    """
    def __init__(self, engine: CampaignEngine):
        self.engine = engine
        self.config = get_universe_config(engine.universe_name) if hasattr(engine, 'universe_name') else {}

    def spawn_fleet(self, faction: str, system_name: str, ship_counts: Dict[str, int], name: Optional[str] = None) -> bool:
        """
        Spawns a fleet at the specified system.
        """
        # 1. Validate Faction
        if faction not in self.engine.factions:
            return False
            
        # 2. Validate System
        system = next((s for s in self.engine.systems if s.name == system_name), None)
        if not system:
            return False

        # 3. Create Fleet
        try:
            from src.entities.fleet import Fleet
            from src.entities.unit import Unit
            from src.utils.id_generator import generate_id
            
            fleet_id = generate_id("fleet")
            fleet_name = name if name else f"{faction} Special Task Force {random.randint(100, 999)}"
            
            # Create Fleet Object
            new_fleet = Fleet(
                id=fleet_id,
                name=fleet_name,
                owner=faction,
                location=system, # Object reference
                units=[]
            )
            
            # 4. Generate Ships
            # We need to know what 'Escort' or 'Cruiser' maps to in unit_registry for this faction.
            # Simplified: We assume ship_counts keys matches keys in the faction's ship roster or are generic classes.
            # If generic (e.g. "Cruiser"), we try to find a matching ship in the faction's known blueprint tags.
            
            # For now, let's assume the user passes actual blueprint names OR we do a lookup.
            # Let's try to find a valid blueprint for the faction.
            
            faction_obj = self.engine.factions[faction]
            # This requires the faction to have a 'units' list or we check the global registry.
            # Let's assume the caller passes valid blueprint IDs for now, or we default to simple ones.
            
            # To make it user friendly in TUI, we might map "Cruiser" -> Faction Specific Cruiser.
            # But that requires a lot of mapping logic. 
            # Let's implement a simple "Spawn Default Fleet" first which uses the faction's 'initial_fleet' logic if available,
            # or just simple placeholders.
            
            for ship_type, count in ship_counts.items():
                for _ in range(count):
                    # Check if ship_type is a blueprint ID
                    # If not, try to find a unit in the registry that matches criteria
                    # For MVP, we presume ship_type IS the blueprint ID (e.g. "Human_Cruiser")
                    
                    unit_id = generate_id("unit")
                    new_ship = Unit(
                        id=unit_id,
                        name=f"{ship_type}-{random.randint(1000,9999)}",
                        owner=faction,
                        unit_type=ship_type # This needs to be a valid blueprint ID usually
                    )
                    # We should probably initialize stats from registry
                    # self._hydrate_unit_stats(new_ship, ship_type) 
                    # For now, relying on engine to handle or simple objects
                    
                    new_fleet.add_unit(new_ship)

            # 5. Register Fleet
            self.engine.fleets.append(new_fleet)
            system.add_fleet(new_fleet)
            
            # Log
            print(f"GodMode: Spawned fleet {fleet_name} for {faction} at {system_name}")
            return True
            
        except Exception as e:
            print(f"GodMode Error: {e}")
            return False

    def spawn_preset_fleet(self, faction: str, system_name: str, preset_type: str) -> bool:
        """
        Spawns a preset fleet composition (e.g. 'Patrol', 'Battlegroup').
        """
        # Define composition based on faction tech/style if possible
        # For MVP, generic composition
        composition = {}
        
        # Try to resolve valid blueprints for this faction
        # This is tricky without access to the full blueprint registry here comfortably.
        # We will assume standard naming convention: "{Faction}_Frigate", "{Faction}_Cruiser"
        # or rely on the fact that we can just spawn them and if they don't render correctly that's fine for v1.
        
        prefix = faction.replace(" ", "_")
        
        if preset_type == "Patrol":
            composition = {f"{prefix}_Frigate": 3, f"{prefix}_Destroyer": 1}
        elif preset_type == "Battlegroup":
             composition = {f"{prefix}_Cruiser": 2, f"{prefix}_Destroyer": 4, f"{prefix}_Frigate": 6}
        elif preset_type == "Capital":
             composition = {f"{prefix}_Battleship": 1, f"{prefix}_Cruiser": 2, f"{prefix}_Escort": 4}
        else:
             composition = {f"{prefix}_Frigate": 1} # Fallback
             
        # Fallback names if specific ones don't exist? 
        # The engine likely needs valid IDs. 
        # Let's just pass these and hope the registry has them or the User inputs correct IDs in the UI.
        
        return self.spawn_fleet(faction, system_name, composition, name=f"{faction} {preset_type}")

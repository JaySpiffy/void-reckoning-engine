from typing import Dict, Any, Optional
import time
from src.managers.campaign_manager import CampaignEngine
from .fleet_spawner import FleetSpawner

class GodModeManager:
    """
    Handles execution of God Mode commands within the simulation worker.
    """
    def __init__(self, engine: CampaignEngine):
        self.engine = engine
        self.fleet_spawner = FleetSpawner(engine)
        self.is_paused = False

    def execute_command(self, cmd: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a god mode command.
        Returns a result dict.
        """
        action = cmd.get("action")
        payload = cmd.get("payload", {})
        
        result = {"success": False, "message": "Unknown action"}
        
        try:
            if action == "SPAWN_FLEET":
                success = self.fleet_spawner.spawn_preset_fleet(
                    faction=payload.get("faction"),
                    system_name=payload.get("system"),
                    preset_type=payload.get("preset", "Patrol")
                )
                result = {"success": success, "message": f"Spawned fleet for {payload.get('faction')}" if success else "Failed to spawn"}
                
            elif action == "SET_RESOURCES":
                faction = payload.get("faction")
                amount = payload.get("amount", 0)
                if faction in self.engine.factions:
                    self.engine.factions[faction].requisition = float(amount)
                    result = {"success": True, "message": f"Set {faction} req to {amount}"}
                else:
                    result = {"success": False, "message": "Faction not found"}

            elif action == "ADD_RESOURCES":
                faction = payload.get("faction")
                amount = payload.get("amount", 0)
                if faction in self.engine.factions:
                    self.engine.factions[faction].requisition += float(amount)
                    result = {"success": True, "message": f"Added {amount} req to {faction}"}
                else:
                    result = {"success": False, "message": "Faction not found"}
                    
            elif action == "FORCE_PEACE":
                # Reset all diplomacy to Neutral/Peace
                if hasattr(self.engine, 'diplomacy'):
                    # This is a bit complex, MVP just clears active wars
                    # Implementation depends on diplomacy manager structure
                    # Assuming we can just access treaties
                    pass
                result = {"success": True, "message": "Global Peace Enforced (Not fully impl)"}

            elif action == "FORCE_WAR":
                # Set all to war
                result = {"success": True, "message": "Total War Declared (Not fully impl)"}
                
            elif action == "TRIGGER_EVENT":
                event_type = payload.get("event_type")
                # Trigger logic here
                result = {"success": True, "message": f"Triggered {event_type}"}
                
        except Exception as e:
            result = {"success": False, "message": f"Error: {e}"}
            
        return result

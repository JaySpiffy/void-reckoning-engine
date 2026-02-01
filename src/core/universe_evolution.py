import os
import json
import time
from typing import Dict, List, Any
from pathlib import Path

class UniverseEvolution:
    """
    Manages the persistent storage and evolution of factions across campaigns.
    Implements the Additive Registry pattern.
    """
    
    def __init__(self, evolution_path: str = "universes/procedural_sandbox/evolution"):
        self.evolution_path = evolution_path
        self.evolution_log_path = os.path.join(evolution_path, "evolution_log.json")
        self.faction_history: Dict[str, List[Dict[str, Any]]] = {}
        self.ensure_directories()
        self.load_evolution_history()
    
    def ensure_directories(self):
        """Creates the evolution storage directory if it doesn't exist."""
        if not os.path.exists(self.evolution_path):
            os.makedirs(self.evolution_path)
    
    def load_evolution_history(self):
        """Loads the evolution history from disk."""
        if os.path.exists(self.evolution_log_path):
            with open(self.evolution_log_path, 'r') as f:
                data = json.load(f)
                self.faction_history = data.get("faction_history", {})
    
    def save_evolution_history(self):
        """Saves the evolution history to disk."""
        data = {
            "faction_history": self.faction_history,
            "last_updated": time.time()
        }
        with open(self.evolution_log_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_faction_birth(self, faction_data: Dict[str, Any], campaign_id: str = "unknown"):
        """
        Records the birth of a new faction.
        
        Args:
            faction_data: The faction's data dictionary
            campaign_id: The campaign where this faction was created
        """
        faction_uid = faction_data.get("uid", faction_data.get("id", "unknown"))
        
        if faction_uid not in self.faction_history:
            self.faction_history[faction_uid] = []
        
        birth_record = {
            "event": "birth",
            "timestamp": time.time(),
            "campaign_id": campaign_id,
            "faction_data": {
                "uid": faction_uid,
                "id": faction_data.get("id"),
                "name": faction_data.get("name"),
                "archetype": faction_data.get("archetype"),
                "dna": faction_data.get("dna", {}),
                "color": faction_data.get("color")
            }
        }
        
        self.faction_history[faction_uid].append(birth_record)
        self.save_evolution_history()
    
    def record_faction_evolution(self, faction_uid: str, dna_changes: Dict[str, float], 
                                 campaign_id: str = "unknown", reason: str = "evolution"):
        """
        Records an evolution event for a faction.
        
        Args:
            faction_uid: The faction's unique identifier
            dna_changes: Dictionary of DNA changes
            campaign_id: The campaign where evolution occurred
            reason: Reason for the evolution
        """
        if faction_uid not in self.faction_history:
            self.faction_history[faction_uid] = []
        
        evolution_record = {
            "event": "evolution",
            "timestamp": time.time(),
            "campaign_id": campaign_id,
            "reason": reason,
            "dna_changes": dna_changes
        }
        
        self.faction_history[faction_uid].append(evolution_record)
        self.save_evolution_history()
    
    def record_faction_death(self, faction_uid: str, campaign_id: str = "unknown", 
                           killer: str = "unknown"):
        """
        Records the death of a faction.
        
        Args:
            faction_uid: The faction's unique identifier
            campaign_id: The campaign where faction died
            killer: What caused the faction's death
        """
        if faction_uid not in self.faction_history:
            self.faction_history[faction_uid] = []
        
        death_record = {
            "event": "death",
            "timestamp": time.time(),
            "campaign_id": campaign_id,
            "killer": killer
        }
        
        self.faction_history[faction_uid].append(death_record)
        self.save_evolution_history()
    
    def get_faction_history(self, faction_uid: str) -> List[Dict[str, Any]]:
        """
        Retrieves the complete history of a faction.
        
        Args:
            faction_uid: The faction's unique identifier
        
        Returns:
            List of historical events for this faction
        """
        return self.faction_history.get(faction_uid, [])
    
    def get_all_faction_uids(self) -> List[str]:
        """Returns list of all faction UIDs in history."""
        return list(self.faction_history.keys())
    
    def get_active_factions(self) -> List[str]:
        """
        Returns list of faction UIDs that haven't died.
        """
        active_factions = []
        for faction_uid, history in self.faction_history.items():
            if not any(event.get("event") == "death" for event in history):
                active_factions.append(faction_uid)
        return active_factions
    
    def get_legacy_factions(self, min_campaigns: int = 5) -> List[str]:
        """
        Returns list of factions that have participated in multiple campaigns.
        These can be used as "Fallen Empires" or legendary threats.
        
        Args:
            min_campaigns: Minimum number of campaigns to be considered legacy
        
        Returns:
            List of faction UIDs
        """
        legacy_factions = []
        for faction_uid, history in self.faction_history.items():
            campaigns = set(event.get("campaign_id", "unknown") for event in history)
            if len(campaigns) >= min_campaigns:
                legacy_factions.append(faction_uid)
        return legacy_factions

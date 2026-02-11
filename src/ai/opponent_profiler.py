from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

@dataclass
class OpponentProfile:
    faction_name: str
    aggression: float = 0.5   # 0.0 (Pacifist) to 1.0 (Warmonger)
    reliability: float = 0.5  # 0.0 (Betrayer) to 1.0 (Honorable)
    expansionism: float = 0.5 # 0.0 (Tall) to 1.0 (Wide)
    tech_threat: float = 0.5  # Relative tech power (0-1+)
    
    last_interaction_turn: int = 0
    war_declarations: int = 0
    treaty_breaches: int = 0
    
    known_crimes: List[str] = field(default_factory=list)
    
    def update_aggression(self, magnitude: float):
        """Updates aggression score with decay towards current behavior."""
        # Simple weighted moving average? Or persistent accumulator?
        # Let's simply push it towards magnitude
        # learning rate = 0.2
        self.aggression = (self.aggression * 0.8) + (magnitude * 0.2)
        self.aggression = max(0.0, min(1.0, self.aggression))

    def update_reliability(self, magnitude: float):
        self.reliability = (self.reliability * 0.8) + (magnitude * 0.2)
        self.reliability = max(0.0, min(1.0, self.reliability))

class OpponentProfiler:
    """
    Tracks and profiles the behavior of other factions.
    Used by StrategicAI to adapt weights and diplomatic stances.
    """
    def __init__(self):
        self._profiles: Dict[str, OpponentProfile] = {}

    def get_profile(self, faction_name: str) -> OpponentProfile:
        if faction_name not in self._profiles:
            self._profiles[faction_name] = OpponentProfile(faction_name)
        return self._profiles[faction_name]

    def register_event(self, subject: str, event_type: str, turn: int, data: Dict[str, Any] = None):
        """
        Registers an observed action by 'subject'.
        Types: WAR_DECLARATION, BROKE_TREATY, EXPANDED, TECH_ADVANCE
        """
        profile = self.get_profile(subject)
        profile.last_interaction_turn = turn
        
        if event_type == "WAR_DECLARATION":
            profile.war_declarations += 1
            # Declaring war is aggressive (0.8 - 1.0 depending on context)
            # If they were provoked? Hard to tell. Assume aggressive.
            profile.update_aggression(0.9)
            
        elif event_type == "BROKE_TREATY":
            profile.treaty_breaches += 1
            # Huge hit to reliability (0.0)
            profile.update_reliability(0.0)
            profile.known_crimes.append(f"Broken Treaty (Turn {turn})")
            
        elif event_type == "PEACE_OFFER":
             # Peace is non-aggressive (0.2)
             profile.update_aggression(0.2)
             
        elif event_type == "EXPANSION":
             # Grabbing a planet
             # Push expansionism up
             profile.expansionism = (profile.expansionism * 0.9) + (1.0 * 0.1)
             
        elif event_type == "TECH_ADVANCE":
             # Tech threat logic handled separately mostly, but we can track 'tech_threat' 
             # if we have relative data passed in 'data'
             if data and 'relative_power' in data:
                  profile.tech_threat = data['relative_power']

    def analyze_threats(self, faction: str, theaters: list) -> List[dict]:
        """
        [AAA Upgrade] Predictive Profiling
        Analyzes enemy fleet movements relative to shared borders.
        Returns a list of threat events.
        """
        threats = []
        
        for theater in theaters:
            # Theater has knowledge of local enemy fleets?
            # We need to access the TheaterManager's analysis of enemy presence
            if not hasattr(theater, 'enemy_fleets'): continue
            
            total_enemy_power = 0
            enemy_counts = {}
            
            for f_name, fleets in theater.enemy_fleets.items():
                if f_name == "Neutral": continue
                f_power = sum(f.military_power_score for f in fleets)
                enemy_counts[f_name] = f_power
                total_enemy_power += f_power
                
            # Check for Massing
            # Heuristic: If > 50% of an enemy's KNOWN total power is in this theater
            # AND this theater is a border...
            
            for enemy, local_power in enemy_counts.items():
                # We need global context (total enemy power) to know if this is a "massing"
                # For now, we use a simpler heuristic: "Is local power threateningly high?"
                
                # Threshold: 20k power is a decent early game fleet
                if local_power > 25000:
                    profile = self.get_profile(enemy)
                    
                    # If high tension and not at war -> THREAT SPIKE
                    # (We assume caller checks war state, or we check it here if we had DiploManager ref)
                    
                    threats.append({
                        "type": "THREAT_SPIKE",
                        "source": enemy,
                        "theater": theater.id,
                        "value": local_power,
                        "reason": "Massive Fleet Concentration on Border"
                    })
                    
                    # Update profile
                    profile.update_aggression(0.6) # Posturing is aggressive
                    
        return threats

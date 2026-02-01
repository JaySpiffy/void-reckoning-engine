from typing import Dict, Any, Optional, List
from src.core.constants import VICTORY_PLANET_THRESHOLD, VICTORY_TURN_LIMIT
from src.reporting.telemetry import EventCategory
from src.events.event import EventType

class VictoryManager:
    """
    Handles victory condition checking and end-game scenarios.
    """
    def __init__(self, engine: Any):
        self.engine = engine
        self._victory_progress_history: Dict[str, List[Dict[str, Any]]] = {}
        
    def check_victory(self) -> Optional[str]:
        """Check if any faction has achieved victory."""
        winner = self._check_dominance_victory()
        if winner: return winner
        
        winner = self._check_elimination_victory()
        if winner: return winner
        
        winner = self._check_turn_limit_victory()
        if winner: return winner
        
        return None

    def _check_dominance_victory(self) -> Optional[str]:
        total_planets = len(self.engine.all_planets)
        if total_planets == 0: return None
        
        for faction_name in self.engine.factions:
            if faction_name == "Neutral": continue
            
            owned = len(self.engine.planets_by_faction.get(faction_name, []))
            ratio = owned / total_planets
            
            if ratio >= VICTORY_PLANET_THRESHOLD:
                return faction_name
        return None

    def _check_elimination_victory(self) -> Optional[str]:
        active_factions = [f for f in self.engine.factions if f != "Neutral"]
        alive_factions = []
        for f_name in active_factions:
             has_planets = len(self.engine.planets_by_faction.get(f_name, [])) > 0
             has_fleets = len(self.engine.fleets_by_faction.get(f_name, [])) > 0
             if has_planets or has_fleets:
                 alive_factions.append(f_name)
                 
        if len(alive_factions) == 1:
             return alive_factions[0]
        return None

    def _check_turn_limit_victory(self) -> Optional[str]:
        if self.engine.turn_counter >= VICTORY_TURN_LIMIT:
             alive_factions = [f for f in self.engine.factions if f != "Neutral"]
             best_faction = None
             max_planets = -1
             for f_name in alive_factions:
                 owned = len(self.engine.planets_by_faction.get(f_name, []))
                 if owned > max_planets:
                     max_planets = owned
                     best_faction = f_name
             return best_faction
        return None

    def log_victory_progress(self):
        """
        Logs victory condition progress for all factions.
        """
        if not self.engine.telemetry:
            return
        
        total_planets = len(self.engine.all_planets)
        threshold = int(total_planets * VICTORY_PLANET_THRESHOLD)
        
        # Calculate current progress
        tally: Dict[str, int] = {}
        for p in self.engine.all_planets:
            tally[p.owner] = tally.get(p.owner, 0) + 1
        
        progress_data = {}
        for faction, count in tally.items():
            if faction == "Neutral":
                continue
            
            progress_pct = (count / threshold) * 100 if threshold > 0 else 0
            progress_data[faction] = {
                'planets_controlled': count,
                'threshold': threshold,
                'progress_pct': min(progress_pct, 100.0),
                'remaining_planets': max(0, threshold - count)
            }
            
            # History
            if faction not in self._victory_progress_history:
                self._victory_progress_history[faction] = []
            
            self._victory_progress_history[faction].append({
                'turn': self.engine.turn_counter,
                'planets_controlled': count,
                'progress_pct': progress_pct
            })
            
            if len(self._victory_progress_history[faction]) > 100:
                self._victory_progress_history[faction] = self._victory_progress_history[faction][-100:]
            
            # Check for victory (redundant with check_victory but good for logging event context)
            if count >= threshold:
                if self.engine.logger:
                    self.engine.logger.campaign(f"[VICTORY] {faction} HAS WON THE CAMPAIGN! [VICTORY]")
                
                self.engine.orchestrator.event_bus.publish(
                    EventType.VICTORY_ACHIEVED,
                    {
                        'faction': faction,
                        'turn': self.engine.turn_counter,
                        'total_turns': self.engine.turn_counter
                    }
                )

        # Log progress
        self.engine.orchestrator.event_bus.publish(
            EventType.VICTORY_PROGRESS,
            {
                'turn': self.engine.turn_counter,
                'total_planets': total_planets,
                'threshold': threshold,
                'faction_progress': progress_data,
                'leading_faction': max(progress_data.items(), key=lambda x: x[1]['planets_controlled']) if progress_data else None
            }
        )

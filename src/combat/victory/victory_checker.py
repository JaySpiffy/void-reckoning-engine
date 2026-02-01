from typing import Dict, List, Any

class VictoryChecker:
    """Handles victory condition evaluation."""
    
    def __init__(self, defender_factions: set):
        self.defender_factions = defender_factions or set()
        
    def check_victory(self, armies: Dict[str, List[Any]], rounds_since_damage: int, force_result: bool = False) -> tuple:
        """
        Returns (winner, survivors, is_finished)
        """
        active_factions = [f for f, units in armies.items() 
                        if any(u.is_alive() for u in units)]
        
        # Stalemate conditions
        if rounds_since_damage >= 500 or force_result:
            return self._resolve_stalemate(active_factions, armies, force_result)
        
        if len(active_factions) == 0:
             return "Draw", 0, True
             
        if len(active_factions) == 1:
            winner = active_factions[0]
            survivors = sum(1 for u in armies.get(winner, []) if u.is_alive())
            return winner, survivors, True
        
        return "Draw", 0, False

    def _resolve_stalemate(self, active_factions, armies, force_result: bool):
        if not active_factions: 
            return "Draw", 0, True
            
        # If defenders are alive, they win by holding out
        defenders_alive = [f for f in active_factions if f in self.defender_factions]
        if defenders_alive:
            winner = defenders_alive[0]
            survivors = sum(1 for u in armies.get(winner, []) if u.is_alive())
            return winner, survivors, True
            
        # Otherwise, compare remaining strength
        # Simple count for now
        max_survivors = -1
        winner = "Draw"
        
        for f in active_factions:
            count = sum(1 for u in armies.get(f, []) if u.is_alive())
            if count > max_survivors:
                max_survivors = count
                winner = f
            elif count == max_survivors:
                winner = "Draw"
                
        return winner, max_survivors, True

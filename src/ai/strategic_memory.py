
import json
import os
import time
from typing import Dict, List, Any

class StrategicMemory:
    """
    Persists long-term strategic data across campaigns.
    Allows the AI to learn from victories and defeats in previous games.
    """
    def __init__(self, memory_file="data/ai_strategic_memory.json"):
        self.memory_file = memory_file
        self.data = {
            "campaigns": [],
            "patterns": {},
            "faction_stats": {},
            "failed_strategies": [] # [AAA Upgrade] List of {faction, goal, target, expires_turn}
        }
        self.load_memory()
        
    def load_memory(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    self.data = json.load(f)
            except Exception as e:
                print(f"Failed to load strategic memory: {e}")
                
    def save_memory(self):
        # Ensure dir exists
        os.makedirs(os.path.dirname(self.memory_file), exist_ok=True)
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Failed to save strategic memory: {e}")

    def record_campaign_result(self, faction: str, result: str, turns: int, score: int, strategy_summary: Dict):
        """
        Records the outcome of a game/campaign for a specific faction.
        """
        entry = {
            "timestamp": time.time(),
            "faction": faction,
            "result": result, # "VICTORY", "DEFEAT", "STALEMATE"
            "turns": turns,
            "score": score,
            "strategies_used": strategy_summary # e.g. {"posture": "TOTAL_WAR", "focus": "ECONOMY"}
        }
        self.data["campaigns"].append(entry)
        
        # Update Aggregate Stats
        if faction not in self.data["faction_stats"]:
            self.data["faction_stats"][faction] = {"wins": 0, "losses": 0, "games": 0, "avg_turns": 0}
            
        stats = self.data["faction_stats"][faction]
        stats["games"] += 1
        if result == "VICTORY": stats["wins"] += 1
        elif result == "DEFEAT": stats["losses"] += 1
        
        # Running average of turns
        stats["avg_turns"] = (stats["avg_turns"] * (stats["games"]-1) + turns) / stats["games"]
        
        self.save_memory()
        
    def analyze_patterns(self) -> Dict[str, Any]:
        """
        Analyzes history to find winning strategies.
        Returns: {faction: {best_posture: str, win_rate: float}}
        """
        insights = {}
        for faction in self.data["faction_stats"].keys():
            # filter games for this faction
            games = [g for g in self.data["campaigns"] if g["faction"] == faction]
            if not games: continue
            
            # Correlate strategy with win rate
            strategy_wins = {} # {posture: [wins, total]}
            
            for g in games:
                strat = g.get("strategies_used", {}).get("active_posture", "UNKNOWN")
                if strat not in strategy_wins: strategy_wins[strat] = [0, 0]
                
                strategy_wins[strat][1] += 1
                if g["result"] == "VICTORY":
                    strategy_wins[strat][0] += 1
                    
            # Find best
            best_strat = "UNKNOWN"
            best_rate = -1.0
            
            for strat, (wins, total) in strategy_wins.items():
                if total < 3: continue # Not enough sample
                rate = wins / total
                if rate > best_rate:
                    best_rate = rate
                    best_strat = strat
                    
            insights[faction] = {
                "best_posture": best_strat,
                "win_rate": best_rate
            }
            
        return insights

    def record_failure(self, faction: str, goal: str, target: str, turn: int, duration: int = 20):
        """
        Blacklists a specific strategy (Goal + Target) for a duration.
        """
        entry = {
            "faction": faction,
            "goal": goal,
            "target": target,
            "expires_turn": turn + duration
        }
        self.data["failed_strategies"].append(entry)
        self.save_memory()

    def is_strategy_blacklisted(self, faction: str, goal: str, target: str, current_turn: int) -> bool:
        """
        Checks if a strategy is currently blacklisted.
        """
        # 1. Cleanup expired
        self.data["failed_strategies"] = [
            f for f in self.data["failed_strategies"] 
            if f.get("expires_turn", 0) > current_turn
        ]
        
        # 2. Check match
        for f in self.data["failed_strategies"]:
            if f["faction"] == faction and f["goal"] == goal and f["target"] == target:
                return True
                
        return False

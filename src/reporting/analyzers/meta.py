import pandas as pd
from typing import Dict, Any

class ComparativeAnalyzer:
    """Compares metrics across factions and universes."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        
    def calculate_faction_balance_score(self, universe: str) -> float:
        """Returns a 0-100 score indicating how balanced the universe is."""
        stats_df = self.indexer.query_latest_faction_stats(universe)
        if stats_df.empty: return 50.0
        
        # Balance based on variance of planets controlled
        std_dev = stats_df['planets_controlled'].std()
        mean = stats_df['planets_controlled'].mean()
        
        if mean == 0: return 50.0
        cv = std_dev / mean # Coefficient of Variation
        
        # Mapping CV to score (Lower CV = Higher Balance)
        # CV 0.0 -> 100
        # CV 1.0 -> 0
        score = max(0, 100 - (cv * 100))
        return float(score)

class DifficultyAnalyzer:
    """Estimates universe difficulty rating."""
    def __init__(self, indexer):
        self.indexer = indexer
        
    def calculate_difficulty_rating(self, universe: str) -> str:
        """Returns difficulty classification based on attrition rates."""
        battles = self.indexer.query_battle_statistics(universe)
        if battles.empty: return "Unknown"
        
        avg_rounds = battles['rounds'].mean()
        avg_units_lost = battles['units_destroyed'].mean()
        
        score = (avg_rounds * 0.5) + (avg_units_lost * 0.1)
        if score > 50: return "Nightmare"
        elif score > 30: return "Hard"
        elif score > 15: return "Normal"
        return "Easy"

class ResourceExhaustionAnalyzer:
    """Predicts resource exhaustion events."""
    def __init__(self, indexer):
        self.indexer = indexer
        
    def check_exhaustion_risk(self, faction: str, universe: str) -> Dict[str, Any]:
        """Checks if a faction is burning resources too fast."""
        df = self.indexer.query_faction_time_series(faction, universe, ['requisition', 'promethium'])
        if df is None or df.empty or len(df) < 5: return {"risk": "low"}
        
        # Simple burn rate check
        req = df['requisition'].values
        burn_rate = req[-1] - req[-5] # Change over 5 turns
        
        if req[-1] < 1000 and burn_rate < -500:
            return {"risk": "critical", "turns_left": abs(req[-1] / burn_rate) * 5}
            
        return {"risk": "low"}

class PredictiveAnalytics:
    """Uses ML models to forecast outcomes."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.models = {} # Cache models
        
    def forecast_victory_probability(self, faction: str, universe: str, current_turn: int) -> float:
        """Predicts probability of victory based on logistic regression of historical data."""
        # Placeholder: Naive heuristic until training data available
        # In a real impl, we'd load a trained sklearn model
        
        stats = self.indexer.query_faction_snapshot(faction, universe, current_turn)
        if not stats: return 0.0
        
        # Simple heuristic model
        score = (stats.get('planets_controlled', 0) * 10) + \
                (stats.get('military_power', 0) * 0.5) + \
                (stats.get('tech_count', 0) * 5)
                
        # Normalize against total universe score? 
        return min(0.99, score / 1000.0)

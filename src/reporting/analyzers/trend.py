import numpy as np
import pandas as pd
from typing import Dict, Any
from sklearn.linear_model import LinearRegression

class TrendAnalyzer:
    """Analyzes historical trends for factions."""
    
    def __init__(self, indexer):
        self.indexer = indexer

    def analyze_win_rate_trajectory(self, faction: str, universe: str, window: int = 10) -> Dict[str, Any]:
        """Calculates win rate trends using linear regression over a moving window."""
        df = self.indexer.query_faction_time_series(faction, universe, ['battles_won', 'battles_fought'])
        if df.empty or len(df) < window:
            return {"trend": "stable", "slope": 0.0}
            
        # Calculate win rate
        df['win_rate'] = df['battles_won'] / df['battles_fought'].replace(0, 1)
        
        # Linear Regression on last 'window' turns
        recent = df.tail(window)
        X = np.arange(len(recent)).reshape(-1, 1)
        y = recent['win_rate'].values.reshape(-1, 1)
        
        reg = LinearRegression().fit(X, y)
        slope = reg.coef_[0][0]
        
        trend = "stable"
        if slope > 0.05: trend = "improving"
        elif slope < -0.05: trend = "declining"
        
        return {
            "trend": trend,
            "slope": float(slope),
            "current_rate": float(recent['win_rate'].iloc[-1]),
            "R2": float(reg.score(X, y))
        }

    def analyze_resource_efficiency(self, faction: str, universe: str) -> Dict[str, Any]:
        """Computes resource generation vs expenditure efficiency."""
        # Requires deeper query support, for now placeholder logic based on income
        df = self.indexer.query_faction_time_series(faction, universe, ['requisition', 'planets_controlled'])
        if df.empty: return {}
        
        # efficiency = req / planets
        df['efficiency'] = df['requisition'] / df['planets_controlled'].replace(0, 1)
        avg_eff = df['efficiency'].mean()
        
        return {
            "average_efficiency": float(avg_eff),
            "latest_efficiency": float(df['efficiency'].iloc[-1])
        }

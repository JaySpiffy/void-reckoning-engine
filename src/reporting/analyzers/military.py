import numpy as np
import pandas as pd
import json
from scipy import stats
from typing import Dict, Any
from sklearn.linear_model import LinearRegression

class MilitaryEfficiencyAnalyzer:
    """Analyzes combat performance and military efficiency."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.cache = {}

    def analyze_combat_effectiveness(self, faction: str, universe: str, window: int = 20, current_turn: int = None) -> Dict[str, Any]:
        if current_turn is not None and f"cer_{faction}" in self.cache:
            res, exp = self.cache[f"cer_{faction}"]
            if current_turn < exp: return res
            
        query = "SELECT combat_effectiveness_ratio FROM battle_performance WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT ?"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe, window))
        except:
            return {}
            
        if df.empty: return {"avg_cer": 0.0, "trend": "unknown", "relative_performance": 1.0}

        avg_cer = df['combat_effectiveness_ratio'].mean()
        
        # Trend
        X = np.arange(len(df)).reshape(-1, 1)
        y = df['combat_effectiveness_ratio'].iloc[::-1].values.reshape(-1, 1)
        
        reg = LinearRegression().fit(X, y)
        slope = reg.coef_[0][0]
        
        trend = "stable"
        if slope > 0.01: trend = "improving"
        elif slope < -0.01: trend = "declining"
        
        # Universe Average
        try:
            uni_df = pd.read_sql_query("SELECT AVG(combat_effectiveness_ratio) as avg_cer FROM battle_performance WHERE universe = ?", 
                                     self.indexer.conn, params=(universe,))
            uni_avg = uni_df['avg_cer'].iloc[0] if not uni_df.empty and uni_df['avg_cer'].iloc[0] else 1.0
        except:
            uni_avg = 1.0

        result = {
            "avg_cer": float(avg_cer),
            "trend": trend,
            "best_battle": float(df['combat_effectiveness_ratio'].max()),
            "worst_battle": float(df['combat_effectiveness_ratio'].min()),
            "relative_performance": float(avg_cer / uni_avg) if uni_avg else 1.0
        }
        
        if current_turn is not None:
             self.cache[f"cer_{faction}"] = (result, current_turn + 5)
             
        return result

    def calculate_force_composition_trends(self, faction: str, universe: str) -> Dict[str, Any]:
        query = "SELECT force_composition, turn FROM battle_performance WHERE faction = ? AND universe = ? ORDER BY turn ASC"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe))
        except:
            return {}
            
        if df.empty: return {}
        
        # Vectorized JSON parsing
        def safe_json(x):
            try: return json.loads(x) if x else {}
            except: return {}
            
        comps_list = df['force_composition'].apply(safe_json).tolist()
        comp_df = pd.DataFrame(comps_list).fillna(0)
        comp_df['turn'] = df['turn'].values
        
        means = comp_df.tail(10).mean(numeric_only=True)
        
        composition_type = "balanced"
        if means.get('Capital', 0) > 30: composition_type = "capital-heavy"
        elif means.get('Escort', 0) > 60: composition_type = "escort-heavy"
        elif means.get('Army', 0) > 60: composition_type = "ground-focused"

        return {
            "current_composition": means.to_dict(),
            "historical_trend": comp_df.to_dict(orient='list'),
            "composition_type": composition_type
        }

    def detect_attrition_patterns(self, faction: str, universe: str) -> Dict[str, Any]:
        query = "SELECT attrition_rate, battle_id, turn FROM battle_performance WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT 15"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe))
        except:
            return {}
            
        if df.empty: return {"avg_attrition_rate": 0.0, "is_bleeding_out": False, "risk_level": "low"}

        avg_attrition = df['attrition_rate'].mean()
        
        # Vectorized streak check
        attrition_vals = df['attrition_rate'].values
        high_attrition_mask = attrition_vals > 0.3
        streak = (np.cumsum(high_attrition_mask) == np.arange(1, len(high_attrition_mask) + 1)).sum()
                
        is_bleeding_out = streak >= 5
        
        # Anomalies
        if len(df) > 1:
            df['z'] = stats.zscore(df['attrition_rate'])
            anomalies = df[df['z'] > 2.0][['battle_id', 'turn', 'attrition_rate']].to_dict(orient='records')
        else:
            anomalies = []
        
        risk = "low"
        if avg_attrition > 0.2: risk = "medium"
        if avg_attrition > 0.4 or is_bleeding_out: risk = "high"

        return {
            "avg_attrition_rate": float(avg_attrition),
            "is_bleeding_out": is_bleeding_out,
            "anomalous_battles": anomalies,
            "risk_level": risk,
            "attrition_trend": "increasing" if streak > 2 else "stable",
            "attrition_streak": int(streak)
        }

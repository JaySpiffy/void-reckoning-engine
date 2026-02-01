import pandas as pd
from scipy import stats
from typing import Dict, List, Any

class AIAnalyzer:
    """Detects deviations in AI behavior patterns."""
    def __init__(self, indexer):
        self.indexer = indexer
        
    def detect_behavior_deviations(self, faction: str, universe: str) -> List[Dict]:
        """Flags statistical anomalies in action frequencies."""
        df = self.indexer.query_ai_action_patterns(faction, universe)
        if df is None or df.empty: return []
        
        deviations = []
        for action_type in df.columns:
            series = df[action_type]
            if len(series) < 5: continue
            
            z_scores = stats.zscore(series)
            # Check last few turns
            last_z = z_scores[-1]
            if abs(last_z) > 2.0:
                deviations.append({
                    "type": "behavior_deviation",
                    "action": action_type,
                    "z_score": float(last_z),
                    "current_rate": float(series.iloc[-1])
                })
        return deviations

class PortalAnalyzer:
    """Analyzes Star-Lattice/Portal network usage."""
    def __init__(self, indexer):
        self.indexer = indexer
        
    def analyze_usage_patterns(self, universe: str) -> Dict[str, Any]:
        """Returns top users and key transit hubs."""
        df = self.indexer.query_portal_usage(universe)
        if df is None or df.empty: return {}
        
        top_users = df['faction'].value_counts().head(3).to_dict()
        hubs = df['location'].value_counts().head(5).to_dict()
        
        return {
            "top_users": top_users,
            "key_hubs": hubs
        }

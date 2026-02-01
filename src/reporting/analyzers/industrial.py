import pandas as pd
from scipy import stats
from typing import Dict, Any

class IndustrialAnalyzer:
    """Analyzes industrial capacity and efficiency."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.cache = {}

    def calculate_industrial_density(self, faction: str, universe: str, current_turn: int = None) -> Dict[str, Any]:
        if current_turn is not None and f"den_{faction}" in self.cache:
            res, exp = self.cache[f"den_{faction}"]
            if current_turn < exp: return res

        query = """
            SELECT military_building_count, economy_building_count, research_building_count, planets_controlled
            FROM factions WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT 1
        """
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe))
        except:
            return {}
            
        if df.empty: return {}
        row = df.iloc[0]
        
        mil = row.get('military_building_count', 0)
        eco = row.get('economy_building_count', 0)
        res = row.get('research_building_count', 0)
        total = mil + eco + res
        
        percentages = {}
        if total > 0:
            percentages = {"Military": mil/total, "Economy": eco/total, "Research": res/total}
            
        stance = "balanced"
        if percentages.get("Military", 0) > 0.5: stance = "military_buildup"
        elif percentages.get("Economy", 0) > 0.5: stance = "economic_boom"
        elif percentages.get("Research", 0) > 0.4: stance = "research_focus"
        
        pc = row.get('planets_controlled', 1)
        density = total / pc if pc > 0 else 0
        
        result = {
            "building_counts": {"Military": int(mil), "Economy": int(eco), "Research": int(res)},
            "percentages": percentages,
            "stance": stance,
            "total_buildings": int(total),
            "density_score": float(density)
        }
        
        if current_turn is not None:
             self.cache[f"den_{faction}"] = (result, current_turn + 5)
             
        return result

    def analyze_queue_efficiency(self, faction: str, universe: str) -> Dict[str, Any]:
        query = "SELECT construction_efficiency, idle_construction_slots FROM factions WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT 20"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe))
        except:
            return {}
            
        if df.empty: return {} 
        
        avg_eff = df['construction_efficiency'].mean()
        avg_idle = df['idle_construction_slots'].mean()
        
        rating = "good"
        if avg_eff < 0.5: rating = "poor"
        if avg_eff > 0.9: rating = "excellent"
        
        bottlenecks = []
        if rating == "poor": bottlenecks.append("excess_capacity")
            
        return {
            "avg_idle_slots": float(avg_idle),
            "avg_queue_efficiency": float(avg_eff),
            "efficiency_rating": rating,
            "bottlenecks": bottlenecks,
            "inefficient_planets": [] # Placeholder requires deeper telemetry query
        }

    def detect_idle_time_anomalies(self, faction: str, universe: str) -> Dict[str, Any]:
         query = "SELECT idle_construction_slots, turn FROM factions WHERE faction = ? AND universe = ? ORDER BY turn ASC"
         try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe))
         except:
            return {}
            
         if df.empty or len(df) < 5: return {}
         
         df['z'] = stats.zscore(df['idle_construction_slots'])
         anoms = df[df['z'] > 2.0][['turn', 'idle_construction_slots']].to_dict(orient='records')
         
         return {
             "anomalies": anoms,
             "severity": "medium" if anoms else "low",
             "potential_causes": ["resource_shortage"] if anoms else []
         }

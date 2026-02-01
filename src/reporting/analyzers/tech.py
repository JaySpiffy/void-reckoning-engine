import pandas as pd
import json
from typing import Dict, Any

class TechAnalyzer:
    """Analyzes technology progression."""
    def __init__(self, indexer):
        self.indexer = indexer
        
    def calculate_tech_velocity(self, faction: str, universe: str) -> Dict[str, float]:
        """Calculates average turns per tech unlock."""
        df = self.indexer.query_tech_progression(faction, universe)
        if df is None or df.empty: 
            return {"velocity": 0.0, "total_unlocked": 0}
            
        last_turn = df['turn'].max()
        total_techs = df['cumulative_techs'].max()
        
        velocity = total_techs / last_turn if last_turn > 0 else 0
        return {
            "velocity": float(velocity),
            "total_unlocked": int(total_techs)
        }

class ResearchAnalyzer:
    """Analyzes technology progress and ROI."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.cache = {}

    def calculate_tech_tree_depth(self, faction: str, universe: str, current_turn: int = None) -> Dict[str, Any]:
        if current_turn is not None and f"depth_{faction}" in self.cache:
            res, exp = self.cache[f"depth_{faction}"]
            if current_turn < exp: return res

        query = "SELECT data_json, research_points FROM factions WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT 1"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe))
        except:
             return {}
        if df.empty: return {}
        
        try:
            data = json.loads(df['data_json'].iloc[0])
            tech_depth = data.get("tech_depth", {})
            tier_breakdown = tech_depth.get("tier_breakdown", {})
            avg_depth = tech_depth.get("avg_depth", 0)
            total = tech_depth.get("total_depth", 0)
        except:
            tier_breakdown = {}
            avg_depth = 0
            total = 0
            
        unlocked = df['research_points'].iloc[0]
        deepest = max([int(k) for k in tier_breakdown.keys()]) if tier_breakdown else 0
            
        result = {
            "total_techs_unlocked": int(unlocked),
            "techs_by_tier": tier_breakdown,
            "avg_depth": float(avg_depth),
            "deepest_tier_reached": deepest,
            "relative_position": "unknown"
        }
        
        if current_turn is not None:
             self.cache[f"depth_{faction}"] = (result, current_turn + 5)
             
        return result

    def measure_research_roi(self, faction: str, universe: str, tech_id: str = None, current_turn: int = None) -> Dict[str, Any]:
        """Measures impact of research on economy/growth."""
        if current_turn is not None and f"roi_{faction}_{tech_id}" in self.cache:
            res, exp = self.cache[f"roi_{faction}_{tech_id}"]
            if current_turn < exp: return res
            
        # Use research_delta_requisition from factions table to estimate economic impact
        query = "SELECT research_delta_requisition, turn FROM factions WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT 10"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe))
        except:
             return {}
             
        impact_val = 0
        if not df.empty:
             impact_val = df['research_delta_requisition'].mean()
             
        result = {
            "roi_score": float(impact_val / 1000.0) if impact_val else 0.0, # Approximate scaling
            "impact_category": "economic",
            "long_term_value_estimate": float(impact_val * 20),
            "unlocked_tech_id": tech_id
        }
        
        if current_turn is not None:
             self.cache[f"roi_{faction}_{tech_id}"] = (result, current_turn + 5)
             
        return result

    def compare_tech_progression(self, faction: str, universe: str, compare_faction: str = None, current_turn: int = None) -> Dict[str, Any]:
        """Compares tech progress against a rival."""
        if current_turn is not None and f"comp_{faction}_{compare_faction}" in self.cache:
            res, exp = self.cache[f"comp_{faction}_{compare_faction}"]
            if current_turn < exp: return res
            
        if not compare_faction:
             # Find rival: faction with similar planet count but different name
             q = "SELECT faction FROM factions WHERE universe = ? AND faction != ? ORDER BY planets_controlled DESC LIMIT 1"
             try:
                cdf = pd.read_sql_query(q, self.indexer.conn, params=(universe, faction))
                if not cdf.empty:
                    compare_faction = cdf['faction'].iloc[0]
             except:
                 pass
                 
        if not compare_faction:
            return {"faction_velocity": 0, "compare_velocity": 0, "overall_leader": "unknown"}

        # Get stats for both
        f1_stats = self.calculate_tech_tree_depth(faction, universe, current_turn)
        f2_stats = self.calculate_tech_tree_depth(compare_faction, universe, current_turn)
        
        v1 = f1_stats.get("total_techs_unlocked", 0)
        v2 = f2_stats.get("total_techs_unlocked", 0)
        
        leader = "even"
        if v1 > v2: leader = faction
        elif v2 > v1: leader = compare_faction
        
        result = {
            "faction_velocity": v1, # simple count for now
            "compare_velocity": v2,
            "overall_leader": leader,
            "rival_name": compare_faction,
            "tech_gap_count": abs(v1 - v2)
        }
        
        if current_turn is not None:
             self.cache[f"comp_{faction}_{compare_faction}"] = (result, current_turn + 5)

        return result

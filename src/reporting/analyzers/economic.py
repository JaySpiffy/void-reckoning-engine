import numpy as np
import pandas as pd
from typing import Dict, Any, Tuple
from sklearn.linear_model import LinearRegression

class EconomicHealthAnalyzer:
    """Analyzes economic stability and health."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        self.cache = {}

    def calculate_stockpile_velocity(self, faction: str, universe: str, window: int = 10, current_turn: int = None) -> Dict[str, Any]:
        """Calculates rate of resource change."""
        if current_turn is not None and f"vel_{faction}_{window}" in self.cache:
            res, exp = self.cache[f"vel_{faction}_{window}"]
            if current_turn < exp: return res

        df = self.indexer.query_faction_time_series(faction, universe, ['requisition'])
        if df.empty:
            return {"velocity": 0.0, "trend": "unknown", "current_stockpile": 0, "projected_depletion_turn": None}
            
        recent = df.tail(window)
        if len(recent) < 2:
             curr = float(recent['requisition'].iloc[-1]) if not recent.empty else 0
             return {"velocity": 0.0, "trend": "stable", "current_stockpile": curr, "projected_depletion_turn": None}

        X = np.arange(len(recent)).reshape(-1, 1)
        y = recent['requisition'].values.reshape(-1, 1)
        
        reg = LinearRegression().fit(X, y)
        velocity = float(reg.coef_[0][0])
        current = float(recent['requisition'].iloc[-1])
        
        trend = "stable"
        if velocity > 50: trend = "increasing"
        elif velocity < -50: trend = "decreasing"
        
        depletion = None
        if velocity < 0 and current > 0:
            turns_left = abs(current / velocity)
            last_turn = int(recent['turn'].iloc[-1]) if 'turn' in recent.columns else 0
            depletion = int(last_turn + turns_left)

        result = {
            "velocity": velocity,
            "trend": trend,
            "current_stockpile": current,
            "projected_depletion_turn": depletion
        }
        
        if current_turn is not None:
            self.cache[f"vel_{faction}_{window}"] = (result, current_turn + 5)
            
        return result

    def detect_economic_death_spiral(self, faction: str, universe: str, current_turn: int = None) -> Dict[str, Any]:
        """Detects if a faction is in an unrecoverable economic decline."""
        if current_turn is not None and f"spiral_{faction}" in self.cache:
            res, exp = self.cache[f"spiral_{faction}"]
            if current_turn < exp: return res
            
        df = self.indexer.query_faction_time_series(faction, universe, ['net_profit', 'requisition'])
        if df.empty or len(df) < 5:
             return {"in_death_spiral": False, "severity": "low", "turns_until_bankruptcy": None, "contributing_factors": []}
             
        recent = df.tail(10)
        
        # Vectorized check for consecutive negative profit
        profits = recent['net_profit'].values
        neg_mask = profits < -500
        # Calculate streak of negative profits at the end
        neg_profit_streak = (np.cumsum(neg_mask[::-1]) == np.arange(1, len(neg_mask) + 1)).sum()
                
        # Check stockpile depletion
        stockpile_velocity = self.calculate_stockpile_velocity(faction, universe, window=5, current_turn=current_turn)
        is_draining = stockpile_velocity['velocity'] < -100
        
        in_spiral = (neg_profit_streak >= 3) and is_draining
        
        severity = "low"
        if in_spiral:
            severity = "medium"
            req = recent['requisition'].iloc[-1]
            if req < 2000:
                severity = "critical"
            elif req < 5000:
                severity = "high"
                
        turns_until_bankrupt = stockpile_velocity.get("projected_depletion_turn")
        
        curr_t_data = int(recent['turn'].iloc[-1]) if 'turn' in recent.columns else 0
        if turns_until_bankrupt:
            turns_until_bankrupt -= curr_t_data
            
        result = {
            "in_death_spiral": in_spiral,
            "severity": severity,
            "turns_until_bankruptcy": turns_until_bankrupt,
            "contributing_factors": ["negative_profit", "rapid_depletion"] if in_spiral else [],
            "neg_profit_streak": int(neg_profit_streak)
        }
        
        if current_turn is not None:
             self.cache[f"spiral_{faction}"] = (result, current_turn + 5)
             
        return result

    def calculate_resource_roi(self, faction: str, universe: str, planet: str, current_turn: int = None) -> Dict[str, Any]:
        """Calculates ROI for a specific planet conquest."""
        if current_turn is not None and f"roi_{faction}_{planet}" in self.cache:
            res, exp = self.cache[f"roi_{faction}_{planet}"]
            if current_turn < exp: return res
            
        if planet is None:
            query = "SELECT turn, amount FROM resource_transactions WHERE faction = ? AND universe = ? AND source_planet IS NULL"
            params = (faction, universe)
        else:
            query = "SELECT turn, amount FROM resource_transactions WHERE faction = ? AND universe = ? AND source_planet = ?"
            params = (faction, universe, planet)

        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=params)
        except:
            return {}
            
        if df.empty: return {"conquest_cost": 0, "cumulative_income": 0, "payback_turns": 0, "roi_percentage": 0, "is_profitable": False}

        income = df[df['amount'] > 0]['amount'].sum()
        
        # Find conquest cost estimate
        battle_query = """
            SELECT bp.resources_lost 
            FROM battle_performance bp
            JOIN battles b ON bp.battle_id = b.id
            WHERE bp.faction = ? AND b.location = ? AND b.universe = ?
            ORDER BY b.turn ASC LIMIT 1
        """
        try:
            b_df = pd.read_sql_query(battle_query, self.indexer.conn, params=(faction, planet, universe))
            cost = b_df['resources_lost'].iloc[0] if not b_df.empty else 1000
        except:
            cost = 1000
        
        if cost == 0: cost = 1000
        
        roi_pct = ((income - cost) / cost) * 100
        payback = cost / (income / len(df)) if income > 0 else 999
        
        result = {
            "conquest_cost": cost,
            "cumulative_income": income,
            "payback_turns": payback,
            "roi_percentage": roi_pct,
            "is_profitable": income > cost
        }
        
        if current_turn is not None:
             self.cache[f"roi_{faction}_{planet}"] = (result, current_turn + 5)
             
        return result

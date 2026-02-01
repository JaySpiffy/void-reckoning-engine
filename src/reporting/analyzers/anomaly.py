import numpy as np
import pandas as pd
import json
from scipy import stats
from typing import Dict, List, Any
from src.reporting.analyzers.economic import EconomicHealthAnalyzer

class AnomalyDetector:
    """Detects statistical anomalies in simulation events."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        
    def detect_battle_anomalies(self, universe: str, threshold: float = 2.5) -> List[Dict]:
        """Flags battles with unusual duration or casualties."""
        battles = self.indexer.query_battle_statistics(universe)
        if battles.empty: return []
        
        # Z-score on rounds
        battles['round_z'] = stats.zscore(battles['rounds'])
        anomalies = battles[np.abs(battles['round_z']) > threshold]
        
        results = []
        for _, row in anomalies.iterrows():
            results.append({
                "type": "battle_duration",
                "planet": row['planet'],
                "rounds": row['rounds'],
                "z_score": float(row['round_z']),
                "turn": row['turn']
            })
        return results

    def detect_resource_spikes(self, faction: str, universe: str, window: int = 10) -> List[Dict]:
        """Identifies sudden changes in resources and economic death spirals."""
        df = self.indexer.query_faction_time_series(faction, universe, ['requisition'])
        if df.empty: return []
        
        df['change'] = df['requisition'].diff()
        
        results = []
        if len(df) > 1:
            df['z_score'] = stats.zscore(df['change'].fillna(0))
            spikes = df[np.abs(df['z_score']) > 3.0]
            results = [{
                "type": "resource_spike",
                "turn": int(idx),
                "change": float(val),
                "z_score": float(z)
            } for idx, val, z in zip(spikes.index, spikes['change'], spikes['z_score'])]

        # Economic death spiral detection (Comment 2)
        # Use stockpile velocity (per turn change) and check for consecutive values < -500 for 3+ turns
        if len(df) >= 3:
            # We need to compute velocity series if not available, or just use 'change' 
            # as a proxy for per-turn velocity if turn interval is 1.
            # Convert to series for easier sliding window if needed, but here we just check raw deltas.
            changes = df['change'].fillna(0).values
            neg_streak = 0
            for c in changes[::-1]:
                if c < -500:
                    neg_streak += 1
                else:
                    break
            
            if neg_streak >= 3:
                # Use EconomicHealthAnalyzer to get formal velocity/projection
                econ = EconomicHealthAnalyzer(self.indexer)
                velocity_data = econ.calculate_stockpile_velocity(faction, universe, window=window)
                results.append({
                    "type": "economic_death_spiral",
                    "severity": "critical",
                    "faction": faction,
                    "turns_in_spiral": neg_streak,
                    "velocity": float(velocity_data.get('velocity', 0)),
                    "projected_bankruptcy_turn": velocity_data.get('projected_depletion_turn')
                })
        return results

    def detect_military_inefficiency(self, faction: str, universe: str, battle_window: int = 5) -> Dict[str, Any]:
        """Detects consecutive battles where CER < 0.5 (Step 2)."""
        query = "SELECT battle_id, combat_effectiveness_ratio, turn FROM battle_performance WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT ?"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe, battle_window * 2))
        except:
            return {}
            
        if df.empty: return {}
            
        inefficient_battles = []
        streak = 0
        for _, row in df.iterrows():
            if row['combat_effectiveness_ratio'] < 0.5:
                streak += 1
                inefficient_battles.append(row['battle_id'])
            else:
                break
                
        if streak >= battle_window:
            avg_cer = df['combat_effectiveness_ratio'].head(streak).mean()
            return {
                "type": "military_inefficiency",
                "severity": "warning",
                "faction": faction,
                "consecutive_poor_battles": streak,
                "avg_cer": float(avg_cer),
                "trend": "declining",
                "battle_ids": inefficient_battles
            }
        return {}

    def detect_idle_infrastructure(self, faction: str, universe: str, turn_threshold: int = 10) -> Dict[str, Any]:
        """Detects if any planet has idle slots > 50% for 10+ consecutive turns (Comment 4)."""
        # Query last 10 turns of data_json from factions table to get detailed planet data
        query = "SELECT data_json, turn FROM factions WHERE faction = ? AND universe = ? ORDER BY turn DESC LIMIT ?"
        try:
            df = pd.read_sql_query(query, self.indexer.conn, params=(faction, universe, turn_threshold))
        except:
            return {}
            
        if df.empty or len(df) < turn_threshold:
            return {}
            
        # Phase 42: Vectorized planetary analysis
        records = []
        for _, row in df.iterrows():
            try:
                data = json.loads(row['data_json'])
                planets = data.get("territory", {}).get("planets", [])
                if isinstance(planets, dict): planets = planets.values()
                for p in planets:
                    total = p.get("total_slots", 0)
                    if total > 0:
                        records.append({
                            "planet": p.get("name"),
                            "turn": row['turn'],
                            "idle_pct": (p.get("idle_slots", 0) / total) * 100
                        })
            except: continue
            
        if not records: return {}
        
        pdf = pd.DataFrame(records)
        # Group by planet and check if ALL turns in the sample exceed 50%
        # (We only have turn_threshold turns due to LIMIT in query)
        stats = pdf.groupby("planet")["idle_pct"].agg(["count", "mean", "min"])
        flagged = stats[(stats["count"] >= turn_threshold) & (stats["min"] > 50)]
        
        flagged_planets = [
            {"planet": name, "avg_idle": float(row["mean"])}
            for name, row in flagged.iterrows()
        ]

        if flagged_planets:
            return {
                "type": "idle_infrastructure",
                "severity": "warning",
                "faction": faction,
                "flagged_planets": flagged_planets,
                "turns_idle": turn_threshold,
                "potential_causes": ["resource_shortage", "construction_stall"]
            }
        return {}

    def detect_research_stagnation(self, faction: str, universe: str, stagnation_threshold: int = 20) -> Dict[str, Any]:
        """Detects if no tech unlocks occurred for 20+ turns (Comment 3)."""
        # Tech progression returns turns where unlocks happened
        df = self.indexer.query_tech_progression(faction, universe)
        if df is None: return {}
        
        # Get latest turn from universe state
        try:
            q = "SELECT MAX(turn) FROM factions WHERE universe = ?"
            latest_turn_df = pd.read_sql_query(q, self.indexer.conn, params=(universe,))
            latest_turn = int(latest_turn_df.iloc[0, 0]) if not latest_turn_df.empty else 0
        except:
            latest_turn = 0

        # If no unlocks ever, check current turn
        if df.empty:
            if latest_turn >= stagnation_threshold:
                return {
                    "type": "research_stagnation",
                    "severity": "info",
                    "faction": faction,
                    "turns_without_progress": latest_turn,
                    "message": "No technologies unlocked since start of simulation."
                }
            return {}

        # Last unlock turn
        last_unlock_turn = df['turn'].max()
        turns_since = latest_turn - last_unlock_turn

        if turns_since >= stagnation_threshold:
            return {
                "type": "research_stagnation",
                "severity": "info",
                "faction": faction,
                "turns_without_progress": int(turns_since),
                "last_unlock_turn": int(last_unlock_turn)
            }
        return {}

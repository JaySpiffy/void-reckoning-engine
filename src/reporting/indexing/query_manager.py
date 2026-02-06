
import json
import sqlite3
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import pandas as pd
except ImportError:
    pd = None

class QueryManagerMixin:
    """Provides reporting and analytical query capabilities to the ReportIndexer."""
    
    def query_telemetry(self, run_id=None, category=None, event_type=None, faction=None, 
                        universe=None, limit=None, batch_id=None, turn_range=None, 
                        page=None, page_size=100) -> Any:
        conditions = []
        params = []
        
        if batch_id and batch_id != "unknown":
            conditions.append("batch_id = ?")
            params.append(batch_id)
        if run_id:
            conditions.append("run_id = ?")
            params.append(run_id)
        if category:
            conditions.append("category = ?")
            params.append(category)
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        if faction:
            if isinstance(faction, str) and "," in faction:
                f_list = [f.strip() for f in faction.split(",")]
                placeholders = ",".join("?" * len(f_list))
                conditions.append(f"faction IN ({placeholders})")
                params.extend(f_list)
            elif isinstance(faction, (list, tuple)):
                placeholders = ",".join("?" * len(faction))
                conditions.append(f"faction IN ({placeholders})")
                params.extend(faction)
            else:
                conditions.append("faction = ?")
                params.append(faction)
        if universe:
            conditions.append("universe = ?")
            params.append(universe)
        if turn_range:
            conditions.append("turn BETWEEN ? AND ?")
            params.extend(turn_range)
            
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
        limit_clause = ""
        if page is not None:
            with self._lock:
                total_count = self.get_query_count("events", where_clause, params)
            offset = (page - 1) * page_size
            limit_clause = f"LIMIT {page_size} OFFSET {offset}"
        elif limit:
            limit_clause = f"LIMIT {int(limit)}"
            
        query = f"SELECT turn, timestamp, category, event_type, faction, location, data_json FROM events {where_clause} ORDER BY turn ASC, timestamp ASC {limit_clause}"
        
        results = []
        try:
            with self._lock:
                cursor = self._execute_query(query, params)
                rows = cursor.fetchall()
            for row in rows:
                try: data = json.loads(row[6]) if row[6] else {}
                except: data = {}
                results.append({
                    "turn": row[0], "timestamp": row[1], "category": row[2],
                    "event_type": row[3], "faction": row[4], "location": row[5], "data": data
                })
        except Exception as e:
            logger.error(f"Error querying telemetry: {e}")
            
        if page is not None:
            return {
                "data": results, "page": page, "page_size": page_size,
                "total_count": total_count, "total_pages": (total_count + page_size - 1) // page_size
            }
        return results

    def query_resource_transactions(self, faction=None, universe=None, category=None, turn_range=None, page=None, page_size=100) -> Any:
        conditions = []
        params = []
        if faction: conditions.append("faction = ?"); params.append(faction)
        if universe: conditions.append("universe = ?"); params.append(universe)
        if category: conditions.append("category = ?"); params.append(category)
        if turn_range: conditions.append("turn BETWEEN ? AND ?"); params.extend(turn_range)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else "WHERE 1=1"
        query = f"SELECT * FROM resource_transactions {where_clause} ORDER BY turn"
        if page is not None:
            total_count = self.get_query_count("resource_transactions", where_clause, params)
            query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
            
        cursor = self._execute_query(query, params)
        columns = [desc[0] for desc in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]
        if page is not None:
            return {"data": data, "page": page, "page_size": page_size, "total_count": total_count, "total_pages": (total_count + page_size - 1) // page_size}
        return data

    def query_battle_performance(self, faction=None, universe=None, turn_range=None, page=None, page_size=100) -> Any:
        conditions = []
        params = []
        if faction: conditions.append("faction = ?"); params.append(faction)
        if universe: conditions.append("universe = ?"); params.append(universe)
        if turn_range: conditions.append("turn BETWEEN ? AND ?"); params.extend(turn_range)
        
        where_clause = "WHERE " + " AND ".join(conditions) if conditions else "WHERE 1=1"
        query = f"SELECT * FROM battle_performance {where_clause} ORDER BY turn"
        if page is not None:
            total_count = self.get_query_count("battle_performance", where_clause, params)
            query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
        
        cursor = self._execute_query(query, params)
        columns = [desc[0] for desc in cursor.description]
        results = []
        for row in cursor.fetchall():
            res = dict(zip(columns, row))
            if res.get("force_composition"): res["force_composition"] = json.loads(res["force_composition"])
            results.append(res)
        if page is not None:
            return {"data": results, "page": page, "page_size": page_size, "total_count": total_count, "total_pages": (total_count + page_size - 1) // page_size}
        return results

    def get_run_max_turn(self, universe: str, run_id: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT MAX(turn) FROM events WHERE universe = ? AND run_id = ?", (universe, run_id))
        row = cursor.fetchone()
        return row[0] if row and row[0] is not None else 0

    def query_galaxy_snapshot(self, universe: str, run_id: str, turn: int) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT f.faction, f.requisition, f.promethium, f.planets_controlled, f.fleets_count, f.data_json
            FROM factions f
            INNER JOIN (
                SELECT faction, MAX(turn) as max_turn FROM factions
                WHERE universe = ? AND run_id = ? AND turn <= ? GROUP BY faction
            ) latest ON f.faction = latest.faction AND f.turn = latest.max_turn
            WHERE f.universe = ? AND f.run_id = ?
        """, (universe, run_id, turn, universe, run_id))
        factions = {row[0]: {"requisition": row[1], "promethium": row[2], "planets_count": row[3], "fleets_count": row[4], "summary": json.loads(row[5]) if row[5] else {}} for row in cursor.fetchall()}
        
        cursor.execute("""
            SELECT data_json FROM events
            WHERE universe = ? AND run_id = ? AND event_type = 'planet_update' AND turn <= ?
            ORDER BY turn DESC, timestamp DESC LIMIT 1
        """, (universe, run_id, turn))
        row = cursor.fetchone()
        planets = {}
        if row:
            try:
                data = json.loads(row[0])
                for p in data.get("planets", []):
                    planets[p["name"]] = {"owner": p["owner"], "status": p.get("status", "Stable"), "is_sieged": p.get("is_sieged", False), "system": p.get("system")}
            except: pass
        return {"turn": turn, "factions": factions, "planets": planets}

    def query_faction_time_series(self, faction: str, universe: str, metrics: List[str], page=None, page_size=100) -> Any:
        cols = ", ".join(metrics)
        where_clause = "WHERE faction = ? AND universe = ?"
        params = [faction, universe]
        query = f"SELECT turn, {cols} FROM factions {where_clause} ORDER BY turn"
        if page is not None:
            total_count = self.get_query_count("factions", where_clause, params)
            query += f" LIMIT {page_size} OFFSET {(page - 1) * page_size}"
            df = pd.read_sql_query(query, self.conn, params=params) if pd else None
            return {"data": df.to_dict(orient='records') if df is not None else [], "page": page, "page_size": page_size, "total_count": total_count}
        return pd.read_sql_query(query, self.conn, params=params) if pd else None

    def query_battle_statistics(self, universe: str) -> Optional['pd.DataFrame']:
        query = "SELECT turn, location as planet, duration_rounds as rounds, total_damage, units_destroyed, winner FROM battles WHERE universe = ? ORDER BY turn"
        try: return pd.read_sql_query(query, self.conn, params=(universe,)) if pd else None
        except Exception as e: logger.error(f"Error querying battle stats: {e}"); return pd.DataFrame() if pd else None

    def query_latest_faction_stats(self, universe: str) -> Optional['pd.DataFrame']:
        query = "SELECT faction, planets_controlled, requisition, battles_won FROM factions WHERE universe = ? AND turn = (SELECT MAX(turn) FROM factions WHERE universe = ?)"
        try: return pd.read_sql_query(query, self.conn, params=(universe, universe)) if pd else None
        except: return pd.DataFrame() if pd else None
            
    def query_faction_snapshot(self, faction: str, universe: str, turn: int) -> Dict[str, Any]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT planets_controlled, requisition, fleets_count, battles_won FROM factions WHERE faction = ? AND universe = ? AND turn = ?", (faction, universe, turn))
        row = cursor.fetchone()
        if not row: return {}
        return {"planets_controlled": row[0], "requisition": row[1], "military_power": row[2] * 1000, "tech_count": 0}

    def query_tech_progression(self, faction: str, universe: str, run_id: str = None) -> Optional['pd.DataFrame']:
        params = [faction, universe]
        filter_clause = "AND run_id = ?" if run_id else ""
        if run_id: params.append(run_id)
        query = f"SELECT turn, COUNT(*) as tech_unlocks FROM events WHERE faction = ? AND universe = ? {filter_clause} AND event_type LIKE '%unlock%' GROUP BY turn ORDER BY turn"
        try:
            if pd is None: return None
            df = pd.read_sql_query(query, self.conn, params=tuple(params))
            if not df.empty: df['cumulative_techs'] = df['tech_unlocks'].cumsum()
            return df
        except: return pd.DataFrame() if pd else None

    def query_ai_action_patterns(self, faction: str, universe: str) -> Optional['pd.DataFrame']:
        query = "SELECT turn, event_type, COUNT(*) as count FROM events WHERE faction = ? AND universe = ? AND event_type IN ('construction_complete', 'unit_recruited', 'diplomacy_action', 'fleet_move') GROUP BY turn, event_type ORDER BY turn"
        try:
            if pd is None: return None
            df = pd.read_sql_query(query, self.conn, params=(faction, universe))
            if df.empty: return df
            return df.pivot(index='turn', columns='event_type', values='count').fillna(0)
        except: return pd.DataFrame() if pd else None

    def query_portal_usage(self, universe: str) -> Optional['pd.DataFrame']:
        query = "SELECT turn, faction, location, 1 as count FROM events WHERE universe = ? AND event_type = 'portal_transit'"
        try: return pd.read_sql_query(query, self.conn, params=(universe,)) if pd else None
        except: return pd.DataFrame() if pd else None

    def query_diplomacy_events(self, universe: str) -> List[tuple]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT faction, data_json FROM events WHERE universe = ? AND category = 'diplomacy'", (universe,))
        edges = []
        for row in cursor.fetchall():
            try:
                data = json.loads(row[1])
                tgt = data.get('target_faction') or data.get('other_faction')
                if row[0] and tgt: edges.append((row[0], tgt))
            except: pass
        return edges

    def query_faction_comparison(self, factions: List[str], universe: str, metrics: List[str]) -> Optional['pd.DataFrame']:
        if not factions or not metrics or not pd: return pd.DataFrame() if pd else None
        valid_metrics = {'requisition', 'promethium', 'planets_controlled', 'battles_won', 'units_recruited'}
        sel = [m for m in metrics if m in valid_metrics]
        placeholders = ",".join("?" * len(factions))
        query = f"SELECT turn, faction, {', '.join(sel)} FROM factions WHERE universe = ? AND faction IN ({placeholders}) ORDER BY turn, faction"
        try: return self._query_cached(query, tuple([universe] + factions))
        except: return pd.DataFrame() if pd else None

    def query_battle_heatmap(self, universe: str) -> Optional['pd.DataFrame']:
        query = "SELECT location, SUM(total_damage) as total_damage, SUM(battle_count) as battles FROM battle_intensity WHERE universe = ? GROUP BY location"
        try: return self._query_cached(query, (universe,))
        except: return pd.DataFrame() if pd else None

    def get_gold_standard_run(self, universe: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT run_id, batch_id, winner, turns_taken, finished_at FROM runs WHERE universe = ? AND is_gold_standard = 1 LIMIT 1", (universe,))
        row = cursor.fetchone()
        return {"run_id": row[0], "batch_id": row[1], "winner": row[2], "turns_taken": row[3], "timestamp": row[4]} if row else None

    def compare_runs(self, universe: str, current_run_id: str, current_batch_id: str, baseline_run_id: str, baseline_batch_id: str) -> Dict[str, Any]:
        if pd is None: return {"error": "Comparison features require pandas installed."}
        def fetch(r_id, b_id):
            try:
                df_f = pd.read_sql_query("SELECT * FROM factions WHERE universe = ? AND run_id = ? AND batch_id = ? ORDER BY turn", self.conn, params=(universe, r_id, b_id))
                df_r = pd.read_sql_query("SELECT amount, category, faction FROM resource_transactions WHERE universe = ? AND run_id = ? AND batch_id = ?", self.conn, params=(universe, r_id, b_id))
                cursor = self.conn.cursor()
                cursor.execute("SELECT turns_taken, winner FROM runs WHERE universe = ? AND run_id = ? AND batch_id = ?", (universe, r_id, b_id))
                m = cursor.fetchone()
                return {'factions': df_f, 'resources': df_r, 'metadata': {"turns_taken": m[0], "winner": m[1]} if m else {}}
            except Exception as e: return {'error': str(e)}

        curr, base = fetch(current_run_id, current_batch_id), fetch(baseline_run_id, baseline_batch_id)
        if 'error' in curr or 'error' in base: return {"error": "Failed to load run data"}
        def get_avg(df, col): return float(df[col].mean()) if df is not None and not df.empty and col in df.columns else 0.0
        deltas = {
            'victory': {"turns_delta": int((curr['metadata'].get('turns_taken') or 0) - (base['metadata'].get('turns_taken') or 0)), "winner_changed": curr['metadata'].get('winner') != base['metadata'].get('winner')},
            'economic': {"gross_income_delta": get_avg(curr['factions'], 'gross_income') - get_avg(base['factions'], 'gross_income'), "net_profit_delta": get_avg(curr['factions'], 'net_profit') - get_avg(base['factions'], 'net_profit')},
            'industrial': {"efficiency_delta": get_avg(curr['factions'], 'construction_efficiency') - get_avg(base['factions'], 'construction_efficiency'), "idle_slots_delta": get_avg(curr['factions'], 'idle_construction_slots') - get_avg(base['factions'], 'idle_construction_slots')},
            'research': {"research_points_delta": get_avg(curr['factions'], 'research_points') - get_avg(base['factions'], 'research_points')}
        }
        return {
            "current": {"run_id": current_run_id, "batch_id": current_batch_id, "metadata": curr['metadata'], "summary": {"avg_income": get_avg(curr['factions'], 'gross_income'), "avg_efficiency": get_avg(curr['factions'], 'construction_efficiency')}},
            "baseline": {"run_id": baseline_run_id, "batch_id": baseline_batch_id, "metadata": base['metadata'], "summary": {"avg_income": get_avg(base['factions'], 'gross_income'), "avg_efficiency": get_avg(base['factions'], 'construction_efficiency')}},
            "deltas": deltas
        }

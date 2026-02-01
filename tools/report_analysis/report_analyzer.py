import sqlite3
import os
import argparse
import json
import csv
import sys
from collections import defaultdict
from typing import List, Dict, Any

class ReportAnalyzer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found at {db_path}")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_faction_performance(self, batch_id: str = None) -> List[Dict[str, Any]]:
        """Aggregates win rates, damage, and losses for all factions."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        where_clause = ""
        params = []
        if batch_id:
            where_clause = "WHERE batch_id = ?"
            params.append(batch_id)
            
        query = f"""
            SELECT 
                faction,
                COUNT(*) as turn_snapshots,
                ROUND(AVG(requisition), 2) as avg_req,
                ROUND(AVG(promethium), 2) as avg_prom,
                MAX(planets_controlled) as peak_planets,
                SUM(battles_won) as total_wins,
                SUM(battles_fought) as total_battles,
                ROUND(SUM(damage_dealt), 2) as total_damage,
                SUM(units_lost) as total_losses
            FROM factions
            {where_clause}
            GROUP BY faction
            ORDER BY total_wins DESC
        """
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        
        # Calculate Win Rate
        for r in results:
            if r['total_battles'] > 0:
                r['win_rate'] = round((r['total_wins'] / r['total_battles']) * 100, 2)
            else:
                r['win_rate'] = 0.0
                
        conn.close()
        return results

    def get_battle_summary(self, batch_id: str = None) -> List[Dict[str, Any]]:
        """Analyzes battle outcomes by location and winner."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        where_clause = ""
        params = []
        if batch_id:
            where_clause = "WHERE batch_id = ?"
            params.append(batch_id)
            
        query = f"""
            SELECT 
                winner,
                COUNT(*) as win_count,
                ROUND(AVG(duration_rounds), 1) as avg_rounds,
                ROUND(AVG(total_damage), 1) as avg_damage,
                SUM(units_destroyed) as total_kills
            FROM battles
            {where_clause}
            GROUP BY winner
            ORDER BY win_count DESC
        """
        
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def get_economic_trends(self, batch_id: str, run_id: str) -> List[Dict[str, Any]]:
        """Returns turn-by-turn resource data for a specific run."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT turn, faction, requisition, promethium, planets_controlled
            FROM factions
            WHERE batch_id = ? AND run_id = ?
            ORDER BY turn ASC, faction ASC
        """
        
        cursor.execute(query, (batch_id, run_id))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def compare_runs(self, batch_id: str) -> List[Dict[str, Any]]:
        """Compares final state of all runs in a batch."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT run_id, winner, turns_taken, started_at, finished_at
            FROM runs
            WHERE batch_id = ?
            ORDER BY run_id ASC
        """
        
        cursor.execute(query, (batch_id,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

def print_table(data: List[Dict[str, Any]], title: str):
    if not data:
        print(f"\nNo data available for {title}")
        return
        
    print(f"\n=== {title} ===")
    headers = data[0].keys()
    header_row = " | ".join([str(h).upper().ljust(15) for h in headers])
    print(header_row)
    print("-" * len(header_row))
    
    for row in data:
        print(" | ".join([str(row.get(h, "")).ljust(15)[:15] for h in headers]))

def main():
    parser = argparse.ArgumentParser(description="Statistical analysis for simulation reports")
    parser.add_argument("--db-path", help="Path to SQLite index database")
    parser.add_argument("--batch", help="Batch ID to analyze")
    parser.add_argument("--run", help="Run ID for trend analysis")
    parser.add_argument("--faction-stats", action="store_true", help="Show faction performance")
    parser.add_argument("--battle-stats", action="store_true", help="Show battle outcomes")
    parser.add_argument("--trends", action="store_true", help="Show economic trends (needs --run)")
    parser.add_argument("--compare", action="store_true", help="Compare all runs in batch")
    parser.add_argument("--export-csv", help="Export result to CSV file")

    args = parser.parse_args()
    
    db_path = args.db_path or os.path.join("reports", "index.db")
    if not os.path.exists(db_path):
        db_path = os.path.join("reports", "reports", "index.db") # Try alternate
        
    try:
        analyzer = ReportAnalyzer(db_path)
    except Exception as e:
        print(f"Error: {e}")
        return

    result = None
    title = ""

    if args.faction_stats:
        result = analyzer.get_faction_performance(args.batch)
        title = "Faction Performance"
    elif args.battle_stats:
        result = analyzer.get_battle_summary(args.batch)
        title = "Battle Summary"
    elif args.trends:
        if not args.batch or not args.run:
            print("Error: --batch and --run are required for trends.")
            return
        result = analyzer.get_economic_trends(args.batch, args.run)
        title = f"Economic Trends: {args.run}"
    elif args.compare:
        if not args.batch:
            print("Error: --batch is required for comparison.")
            return
        result = analyzer.compare_runs(args.batch)
        title = f"Run Comparison: {args.batch}"
    else:
        parser.print_help()
        return

    if result:
        if args.export_csv:
            with open(args.export_csv, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=result[0].keys())
                writer.writeheader()
                writer.writerows(result)
            print(f"Exported to {args.export_csv}")
        else:
            print_table(result, title)

if __name__ == "__main__":
    main()

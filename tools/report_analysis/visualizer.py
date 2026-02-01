import sqlite3
import os
import argparse
import sys
from collections import defaultdict
from typing import List, Dict, Any

class ASCIIVisualizer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Database not found at {db_path}")

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def draw_resource_sparkline(self, data: List[float], width: int = 50) -> str:
        """Generates a simple ASCII sparkline-style bar chart."""
        if not data: return ""
        
        min_v = min(data)
        max_v = max(data)
        rng = max_v - min_v if max_v != min_v else 1.0
        
        chars = " ▂▃▄▅▆▇█"
        # Since some terminals don't support special chars well, we'll use blocks
        # or simplified bars if needed.
        
        result = []
        for val in data:
            pct = (val - min_v) / rng
            h = int(pct * 7)
            result.append(chars[h])
        return "".join(result)

    def draw_timeline(self, batch_id: str, run_id: str, step: Optional[int] = None):
        """Visualizes faction planet control over time."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT turn, faction, planets_controlled
            FROM factions
            WHERE batch_id = ? AND run_id = ?
            ORDER BY turn ASC, faction ASC
        """
        cursor.execute(query, (batch_id, run_id))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not rows:
            print("No data found for visualization.")
            return

        # Pivot data
        turns = sorted(list(set(r['turn'] for r in rows)))
        factions = sorted(list(set(r['faction'] for r in rows)))
        
        pivot = defaultdict(lambda: defaultdict(int))
        for r in rows:
            pivot[r['turn']][r['faction']] = r['planets_controlled']

        print(f"\n--- CAMPAIGN TIMELINE: {run_id} ---")
        print("Planet Control by Faction (ASCII Scale)")
        print("-" * 60)
        
        # Determine scaling
        max_planets = max(r['planets_controlled'] for r in rows)
        if max_planets == 0: max_planets = 1
        
        bar_max_len = 40
        
        # Calculate effective step (Comment 1)
        if step is None:
            eff_step = 10 if len(turns) > 20 else 1
        else:
            eff_step = step

        for i, t in enumerate(turns):
            if eff_step > 1:
                # Always show first and last, otherwise sample
                if i != 0 and i != len(turns) - 1 and t % eff_step != 0:
                    continue
            
            print(f"Turn {str(t).ljust(4)} | ", end="")
            for f in factions:
                count = pivot[t][f]
                bar_len = int((count / max_planets) * bar_max_len)
                # Map faction to a char
                sym = f[0].upper()
                print(sym * bar_len, end="")
            print(f" ({sum(pivot[t].values())} total)")

    def draw_resource_trends(self, batch_id: str, run_id: str):
        """Visualizes Requisition trends for each faction."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT turn, faction, requisition
            FROM factions
            WHERE batch_id = ? AND run_id = ?
            ORDER BY turn ASC, faction ASC
        """
        cursor.execute(query, (batch_id, run_id))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        if not rows: return

        f_data = defaultdict(list)
        for r in rows:
            f_data[r['faction']].append(float(r['requisition']))

        print(f"\n--- RESOURCE TRENDS (REQUISITION) ---")
        for faction, data in f_data.items():
            spark = self.draw_resource_sparkline(data)
            print(f"{faction.ljust(15)}: [{spark}] {int(data[-1])}")

def main():
    parser = argparse.ArgumentParser(description="ASCII visualization for campaign reports")
    parser.add_argument("--db-path", help="Path to index database")
    parser.add_argument("--batch", required=True, help="Batch ID")
    parser.add_argument("--run", required=True, help="Run ID")
    parser.add_argument("--timeline", action="store_true", help="Show planet control timeline")
    parser.add_argument("--resources", action="store_true", help="Show resource sparklines")
    parser.add_argument("--step", type=int, help="Turn sampling step for timeline (e.g., 5)")

    args = parser.parse_args()
    
    db_path = args.db_path or os.path.join("reports", "index.db")
    if not os.path.exists(db_path):
        db_path = os.path.join("reports", "reports", "index.db")
        
    try:
        viz = ASCIIVisualizer(db_path)
        if args.timeline:
            viz.draw_timeline(args.batch, args.run, step=args.step)
        if args.resources:
            viz.draw_resource_trends(args.batch, args.run)
        
        if not args.timeline and not args.resources:
            viz.draw_timeline(args.batch, args.run, step=args.step)
            viz.draw_resource_trends(args.batch, args.run)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

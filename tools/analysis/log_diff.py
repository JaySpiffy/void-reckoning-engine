import argparse
import sys
import os
import json
import difflib
from typing import List, Dict, Any
import glob

# Optional dependencies
try:
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    from scipy import stats
except ImportError:
    pd = None
    np = None
    plt = None

# Ensure src path available
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.reporting.indexer import ReportIndexer

class LogDiffer:
    """Advanced Log Comparison Tool."""
    
    def __init__(self, db_path: str = "reports/index.db"):
        self.indexer = ReportIndexer(db_path)

    def diff_text_logs(self, log_path_a: str, log_path_b: str, output_path: str = None):
        """Line-by-line diff of text logs."""
        print(f"Comparing text logs:\n A: {log_path_a}\n B: {log_path_b}")
        
        try:
            with open(log_path_a, 'r', encoding='utf-8') as f1, open(log_path_b, 'r', encoding='utf-8') as f2:
                lines_a = f1.readlines()
                lines_b = f2.readlines()
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return

        diff = difflib.unified_diff(
            lines_a, lines_b, 
            fromfile=log_path_a, tofile=log_path_b, 
            n=3
        )
        
        diff_lines = list(diff)
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as out:
                out.writelines(diff_lines)
            print(f"Text diff saved to {output_path}")
        else:
            for line in diff_lines[:50]: # Print first 50 lines only to avoid spam
                print(line, end='')
            if len(diff_lines) > 50:
                print(f"... ({len(diff_lines)-50} more lines) ...")

    def diff_events_json(self, run_a: str, run_b: str, universe: str):
        """Compare event sequences from DB."""
        if not pd: return
        
        print(f"Comparing Event Sequences: {run_a} vs {run_b}")
        
        # Fetch events
        query = "SELECT turn, event_type, faction, category FROM events WHERE universe = ? AND run_id = ? ORDER BY turn, id"
        df_a = pd.read_sql_query(query, self.indexer.conn, params=(universe, run_a))
        df_b = pd.read_sql_query(query, self.indexer.conn, params=(universe, run_b))
        
        # Normalize for comparison (ignore ID, timestamp)
        # Create a signature string for each event
        df_a['sig'] = df_a['turn'].astype(str) + "|" + df_a['event_type'] + "|" + df_a['faction'].fillna('')
        df_b['sig'] = df_b['turn'].astype(str) + "|" + df_b['event_type'] + "|" + df_b['faction'].fillna('')
        
        seq_a = df_a['sig'].tolist()
        seq_b = df_b['sig'].tolist()
        
        # Sequence Matcher
        matcher = difflib.SequenceMatcher(None, seq_a, seq_b)
        ratio = matcher.ratio()
        print(f"Sequence Similarity: {ratio:.2%}")
        
        # Divergence Point
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag != 'equal':
                print(f"Divergence at A:{i1} ({seq_a[i1] if i1<len(seq_a) else 'EOF'}) vs B:{j1} ({seq_b[j1] if j1<len(seq_b) else 'EOF'})")
                print(f"  Gap: A has {i2-i1} events, B has {j2-j1} events differing.")
                break # Show first divergence only

    def diff_stats(self, run_a: str, run_b: str, universe: str, output_path: str = None):
        """Compare aggregated stats."""
        if not pd: return
        
        print(f"Comparing Stats: {run_a} vs {run_b}")
        
        query = """
            SELECT faction, turn, planets_controlled, requisition, battles_won, run_id
            FROM factions
            WHERE universe = ? AND run_id IN (?, ?)
        """
        df = pd.read_sql_query(query, self.indexer.conn, params=(universe, run_a, run_b))
        
        # Pivot to align turns
        # We want to compare Faction X at Turn Y in Run A vs Run B
        groups = df.groupby(['faction', 'turn'])
        
        diffs = []
        for (faction, turn), group in groups:
            if len(group) == 2:
                # Both runs exist
                row_a = group[group['run_id'] == run_a].iloc[0]
                row_b = group[group['run_id'] == run_b].iloc[0]
                
                req_delta = row_b['requisition'] - row_a['requisition']
                planet_delta = row_b['planets_controlled'] - row_a['planets_controlled']
                
                if abs(req_delta) > 0 or abs(planet_delta) > 0:
                    diffs.append({
                        "faction": faction, "turn": turn,
                        "req_delta": req_delta, "planet_delta": planet_delta
                    })
        
        res_df = pd.DataFrame(diffs)
        if not res_df.empty:
            print(f"Found {len(res_df)} stat divergences.")
            print(res_df.head(10).to_string())
            if output_path:
                res_df.to_csv(output_path, index=False)
                print(f"Saved stats diff to {output_path}")
                
            # Visualization
            if plt:
                self._plot_diffs(res_df, run_a, run_b, output_path)
        else:
            print("No statistical divergences found.")

    def _plot_diffs(self, df, run_a, run_b, base_path):
        if not base_path: return
        try:
            # Scatter plot of divergences
            plt.figure(figsize=(10, 6))
            plt.scatter(df['turn'], df['req_delta'], alpha=0.6, label='Requisition Delta')
            plt.scatter(df['turn'], df['planet_delta'] * 100, alpha=0.6, label='Planet Delta (x100)')
            plt.title(f"Divergence: {run_a} vs {run_b}")
            plt.xlabel("Turn")
            plt.ylabel("Delta (Run B - Run A)")
            plt.legend()
            plt.grid(True)
            
            img_path = base_path.replace(".csv", ".png")
            plt.savefig(img_path)
            print(f"Saved plot to {img_path}")
            plt.close()
        except Exception as e:
            print(f"Plotting failed: {e}")

    def diff_battles(self, run_a: str, run_b: str, universe: str):
        """Compare battle outcomes."""
        if not pd: return
        
        query = """
            SELECT turn, location, factions_involved, winner, total_damage, run_id
            FROM battles
            WHERE universe = ? AND run_id IN (?, ?)
            ORDER BY turn, location
        """
        df = pd.read_sql_query(query, self.indexer.conn, params=(universe, run_a, run_b))
        
        # Match battles by Turn + Location
        # Identify Winner flips
        
        # Create unique key
        df['key'] = df['turn'].astype(str) + "_" + df['location']
        
        pivoted = df.pivot(index='key', columns='run_id', values='winner')
        
        # Drop rows where one run is missing the battle (structural divergence)
        # or where outcomes differ
        
        divergences = []
        structural = []
        
        for key, row in pivoted.iterrows():
            w_a = row.get(run_a)
            w_b = row.get(run_b)
            
            if pd.isna(w_a) or pd.isna(w_b):
                structural.append(key)
            elif w_a != w_b:
                divergences.append((key, w_a, w_b))
                
        print(f"Battle Comparison:")
        print(f"  Structural Differences (Battle present in one run only): {len(structural)}")
        print(f"  Outcome Flips (Same battle, different winner): {len(divergences)}")
        
        if divergences:
            print("  Top 5 Flips:")
            for d in divergences[:5]:
                print(f"    {d[0]}: {run_a}={d[1]} vs {run_b}={d[2]}")

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Log Diff Tool")
    parser.add_argument("run_a", help="Run ID A or Log Path A")
    parser.add_argument("run_b", help="Run ID B or Log Path B")
    parser.add_argument("--mode", choices=["text", "event", "stats", "battle"], default="text")
    parser.add_argument("--universe", help="Universe name (required for DB modes)")
    parser.add_argument("--db-path", default="reports/index.db")
    parser.add_argument("--output", help="Output path for report")
    
    args = parser.parse_args()
    
    differ = LogDiffer(args.db_path)
    
    if args.mode == "text":
        differ.diff_text_logs(args.run_a, args.run_b, args.output)
    elif args.mode == "event":
        if not args.universe:
            print("Error: --universe required for event diff")
            return
        differ.diff_events_json(args.run_a, args.run_b, args.universe)
    elif args.mode == "stats":
        if not args.universe:
            print("Error: --universe required for stats diff")
            return
        differ.diff_stats(args.run_a, args.run_b, args.universe, args.output)
    elif args.mode == "battle":
        if not args.universe:
            print("Error: --universe required for battle diff")
            return
        differ.diff_battles(args.run_a, args.run_b, args.universe)

if __name__ == "__main__":
    main()

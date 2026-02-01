import argparse
import sys
import os
import json
import sqlite3
import glob
from collections import defaultdict, Counter
from typing import List, Dict, Any, Tuple
from datetime import datetime

# Optional dependencies
try:
    import pandas as pd
    import numpy as np
    from scipy import stats
    import matplotlib.pyplot as plt
except ImportError:
    pd = None
    np = None
    plt = None

# Ensure src path available
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.reporting.indexer import ReportIndexer

class PatternMiner:
    """Mines frequent event sequences."""
    def __init__(self, db_path: str):
        self.indexer = ReportIndexer(db_path)

    def mine_patterns(self, universe: str, batch_id: str = None, min_support: float = 0.1, n_gram: int = 3):
        if not pd: 
            print("Error: Pandas required for pattern mining.")
            return

        print(f"Mining patterns (N={n_gram}) for universe {universe}...")
        
        # Fetch events sorted by run, turn, timestamp
        query = "SELECT run_id, turn, event_type FROM events WHERE universe = ?"
        params = [universe]
        if batch_id:
            query += " AND batch_id = ?"
            params.append(batch_id)
        
        query += " ORDER BY run_id, turn, timestamp"
        
        df = pd.read_sql_query(query, self.indexer.conn, params=params)
        if df.empty:
            print("No events found.")
            return

        sequences = df.groupby('run_id')['event_type'].apply(list)
        ngram_counts = Counter()
        total_runs = len(sequences)
        
        for seq in sequences:
            run_ngrams = set()
            for i in range(len(seq) - n_gram + 1):
                gram = tuple(seq[i:i+n_gram])
                run_ngrams.add(gram)
            ngram_counts.update(run_ngrams)

        results = []
        for gram, count in ngram_counts.items():
            support = count / total_runs
            if support >= min_support:
                results.append({
                    "pattern": " -> ".join(gram),
                    "support": support,
                    "count": count
                })
        
        results.sort(key=lambda x: x['support'], reverse=True)
        return results

class ErrorAnalyzer:
    """Analyzes ERROR/CRITICAL logs with chain detection."""
    def __init__(self, logs_dir: str):
        self.logs_dir = logs_dir

    def analyze_errors(self, run_id: str = None):
        error_counts = Counter()
        chains = Counter()
        
        search_pattern = os.path.join(self.logs_dir, "**", "*.json")
        files = glob.glob(search_pattern, recursive=True)
        
        print(f"Scanning {len(files)} log files...")
        
        for fpath in files:
            if run_id and run_id not in fpath: continue
            
            last_event = None
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    for line in f:
                        if not line.strip(): continue
                        try:
                            record = json.loads(line)
                        except: continue
                        
                        event = record.get("event_type") or record.get("message")
                        
                        if record.get("level") in ["ERROR", "CRITICAL"]:
                            msg = record.get("message", "Unknown")
                            ctx = record.get("context", {})
                            key = f"{msg} | {ctx.get('component','unknown')}"
                            error_counts[key] += 1
                            
                            # Simple chain: What happened immediately before?
                            if last_event:
                                chain_key = f"{last_event} -> {key}"
                                chains[chain_key] += 1
                                
                        last_event = event
            except: pass
                
        return error_counts.most_common(20), chains.most_common(10)

class PerformanceProfiler:
    """Profiles operation performance and memory usage."""
    def __init__(self, logs_dir: str):
        self.logs_dir = logs_dir

    def profile_performance(self, run_id: str = None, threshold_ms: int = 100):
        if not pd: return None
        
        records = []
        search_pattern = os.path.join(self.logs_dir, "**", "*.json")
        for fpath in glob.glob(search_pattern, recursive=True):
            if run_id and run_id not in fpath: continue
            
            try:
                with open(fpath, 'r') as f:
                    for line in f:
                        try:
                            data = json.loads(line)
                            perf = data.get("performance", {})
                            
                            op = data.get("event_type") or data.get("message")
                            turn = data.get("turn", 0)
                            
                            # Duration extraction
                            dur = 0
                            if isinstance(perf, dict) and "duration_ms" in perf:
                                dur = perf.get("duration_ms", 0)
                            elif "duration_ms" in data:
                                dur = data["duration_ms"]
                                
                            # Memory extraction
                            mem = 0
                            if isinstance(perf, dict) and "memory_mb" in perf:
                                mem = perf.get("memory_mb", 0)
                            elif "memory_mb" in data:
                                mem = data["memory_mb"]
                                
                            if dur > 0 or mem > 0:
                                records.append({"op": op, "duration": dur, "memory": mem, "turn": turn})
                                
                        except: continue
            except: pass
            
        if not records:
            print("No performance records found.")
            return None
            
        df = pd.DataFrame(records)
        
        # Stats
        stats = df.groupby('op')[['duration', 'memory']].describe(percentiles=[0.5, 0.95, 0.99])
        
        # Hotspots
        hotspots = df[df['duration'] > threshold_ms].groupby('op').size().sort_values(ascending=False)
        
        # High Memory Ops
        mem_hogs = df.sort_values('memory', ascending=False).head(10)[['op', 'memory', 'turn']]
        
        return stats, hotspots, mem_hogs

class CorrelationAnalyzer:
    """Correlates events with outcomes and crashes."""
    def __init__(self, db_path: str):
        self.indexer = ReportIndexer(db_path)

    def analyze_correlations(self, universe: str, target_metric: str = "battles_won"):
        if not pd or not np: return
        
        # 1. Standard Correlation
        query = """
            SELECT faction, turn, units_recruited, battles_won, damage_dealt, 
                   requisition, planets_controlled
            FROM factions
            WHERE universe = ?
        """
        df = pd.read_sql_query(query, self.indexer.conn, params=(universe,))
        if not df.empty:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            corr_matrix = df[numeric_cols].corr()
            print(f"\nMetric Correlations (Target: {target_metric}):")
            if target_metric in corr_matrix.columns:
                print(corr_matrix[target_metric].sort_values(ascending=False))
            else:
                print(corr_matrix)
        
    def analyze_crash_precursors(self, universe: str, window: int = 5):
        """Find events occurring frequently before crashes."""
        # This requires logs to be indexed as EVENTS with error info, or scanning raw logs
        # Assuming we scan events table where we might have ingested log errors or implied crashes
        # If we rely on logs, we need logic similar to ErrorAnalyzer but cross-ref with DB.
        # For this tool, we'll scan the events table for 'CRITICAL' or custom 'crash_detected' events
        # then look at N events prior in same run.
        
        # Fetch all events (optimized)
        query = "SELECT run_id, turn, event_type, id FROM events WHERE universe = ? ORDER BY run_id, id"
        df = pd.read_sql_query(query, self.indexer.conn, params=(universe,))
        
        if df.empty: return
        
        # Find 'crash' events - simplistic look for error types or specific known crash types
        # Note: If errors aren't indexed as events, this won't work well without log ingestion.
        # Assuming 'text_log' events with 'ERROR' keywords or specific event types.
        crash_indices = df[df['event_type'].str.contains('ERROR|CRITICAL|crash', case=False, na=False)].index
        
        if len(crash_indices) == 0:
            print("No crash/error events found in index to analyze precursors.")
            return

        precursors = Counter()
        for idx in crash_indices:
            # Get window before
            start = max(0, idx - window)
            subset = df.iloc[start:idx]
            # Ensure same run
            run_id = df.loc[idx, 'run_id']
            valid_precursors = subset[subset['run_id'] == run_id]['event_type']
            precursors.update(valid_precursors)
            
        print(f"\nTop {window} Events Preceding Errors/Crashes:")
        for ev, count in precursors.most_common(15):
            print(f"{count:4d} | {ev}")

# --- CLI ---

def main():
    parser = argparse.ArgumentParser(description="Log Analysis Tool")
    subparsers = parser.add_subparsers(dest="mode", help="Analysis mode")
    
    # Pattern Mining
    p_pat = subparsers.add_parser("pattern", help="Mine frequent event patterns")
    p_pat.add_argument("--db-path", default="reports/index.db")
    p_pat.add_argument("--universe", required=True)
    p_pat.add_argument("--batch-id")
    p_pat.add_argument("--n-gram", type=int, default=3)
    p_pat.add_argument("--min-support", type=float, default=0.1)
    
    # Error Analysis
    p_err = subparsers.add_parser("errors", help="Analyze error logs")
    p_err.add_argument("--logs-dir", default="logs")
    p_err.add_argument("--run-id")
    
    # Performance
    p_perf = subparsers.add_parser("performance", help="Profile performance")
    p_perf.add_argument("--logs-dir", default="logs")
    p_perf.add_argument("--run-id")
    p_perf.add_argument("--threshold", type=int, default=100)
    
    # Correlation
    p_corr = subparsers.add_parser("correlation", help="Analyze metrics correlation")
    p_corr.add_argument("--db-path", default="reports/index.db")
    p_corr.add_argument("--universe", required=True)
    p_corr.add_argument("--target", default="battles_won")
    p_corr.add_argument("--crash-window", type=int, default=0, help="Analyze events before crashes (set > 0)")
    
    args = parser.parse_args()
    
    if args.mode == "pattern":
        miner = PatternMiner(args.db_path)
        results = miner.mine_patterns(args.universe, args.batch_id, args.min_support, args.n_gram)
        if results:
            print("\nFrequent Patterns:")
            print(pd.DataFrame(results).to_markdown(index=False))
            
    elif args.mode == "errors":
        analyzer = ErrorAnalyzer(args.logs_dir)
        errors, chains = analyzer.analyze_errors(args.run_id)
        print("\nTop Errors:")
        for e, c in errors:
            print(f"{c:4d} | {e}")
        print("\nCommon Error Chains:")
        for ch, c in chains:
            print(f"{c:4d} | {ch}")
            
    elif args.mode == "performance":
        profiler = PerformanceProfiler(args.logs_dir)
        res = profiler.profile_performance(args.run_id, args.threshold)
        if res:
            stats, hotspots, mem_hogs = res
            print("\nPerformance Stats:")
            print(stats)
            print("\nHotspots (Ops > Threshold):")
            print(hotspots)
            print("\nTop Memory Spikes:")
            print(mem_hogs)
            
    elif args.mode == "correlation":
        analyzer = CorrelationAnalyzer(args.db_path)
        analyzer.analyze_correlations(args.universe, args.target)
        if args.crash_window > 0:
            analyzer.analyze_crash_precursors(args.universe, args.crash_window)

if __name__ == "__main__":
    main()

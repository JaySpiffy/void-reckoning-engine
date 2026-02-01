
import sys
import os
import time
import datetime
import json
import traceback
import multiprocessing
from multiprocessing import Manager
from collections import defaultdict

# Extracted Components
from src.engine.runner.simulation_worker import SimulationWorker, worker_init
from src.engine.runner.progress_dashboard import ProgressDashboard
from src.engine.runner.results_aggregator import ResultsAggregator

from src.reporting.indexer import ReportIndexer

def load_config_from_file(path=None):
    if not path:
        path = "config/void_reckoning_config.json"
    
    if not os.path.exists(path):
        print(f"Config file not found at {path}. Using defaults.")
        # Minimal Fallback
        return {
            "simulation": {"num_runs": 10},
            "campaign": {"turns": 100}
        }
        
    with open(path, "r") as f:
        return json.load(f)

def run_batch_simulation(config_data, output_dir=None):
    multiprocessing.freeze_support()
    
    # helper to flatten or fallback
    def get_conf(key, default, section=None):
        if section and section in config_data and key in config_data[section]:
            return config_data[section][key]
        return config_data.get(key, default)

    # Load Config (Support Flat or Nested)
    num_runs = get_conf("num_runs", 100, "simulation")
    workers_conf = get_conf("max_workers", 14, "simulation")
    turns_per_run = get_conf("turns", 5000, "campaign")

    num_systems = get_conf("num_systems", 20, "campaign")
    min_p = get_conf("min_planets", 1, "campaign")
    max_p = get_conf("max_planets", 5, "campaign")
    
    combat_rounds = get_conf("combat_rounds", 500, "campaign")
    max_fleet = get_conf("max_fleet_size", 50, "units")
    max_land = get_conf("max_land_army_size", 20, "units")
    base_req = get_conf("base_income_req", 1000, "economy")

    # Hardware Check
    cores = multiprocessing.cpu_count()
    workers = min(workers_conf, cores - 1)
    if workers < 1: workers = 1
    
    print(f"Initializing {workers} workers based on config...")
    
    # Shared Queue
    m = Manager()
    q = m.Queue()
    
    # Setup Batch Directory
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if not output_dir:
        output_dir = get_conf("output_dir", None, "simulation")
        
    base_reports_dir = output_dir if output_dir else os.path.join(os.path.dirname(os.path.dirname(__file__)), "reports")
    batch_dir = os.path.join(base_reports_dir, f"batch_{timestamp}")
    
    try:
        os.makedirs(batch_dir, exist_ok=True)
    except Exception as e:
        print(f"Error creating batch directory: {e}")
        return

    # Ensure Indexer Schema
    base_reports_dir = os.path.dirname(batch_dir)
    db_path = os.path.join(base_reports_dir, "index.db")
    try:
        print(f"  > [INIT] Verifying indexer schema at {db_path}...")
        idx = ReportIndexer(db_path)
        idx.close()
    except Exception as e:
        print(f"  > [WARNING] Failed to pre-initialize indexer: {e}")

    # Worker Pool
    pool = multiprocessing.Pool(processes=workers, initializer=worker_init, initargs=(q,))
    
    game_config = {
        "mechanics": get_conf("mechanics", {}, "mechanics"), 
        "seed": get_conf("random_seed", None, "simulation"),
        "reporting": get_conf("reporting", {}, "reporting"),
        "debug": get_conf("debug_mode", False, "simulation")
    }

    # Pass config args AND batch_dir to workers
    # Signature: run_id, turns_per_run, num_systems, batch_dir, min_p, max_p, combat_rounds, max_fleet, max_land, base_req, game_config
    tasks = [(i+1, turns_per_run, num_systems, batch_dir, min_p, max_p, combat_rounds, max_fleet, max_land, base_req, game_config) for i in range(num_runs)]
    
    # Start Workers
    # Point to SimulationWorker wrapper via import or static method reference wrapped in global func
    # We imported `run_single_campaign_wrapped` from simulation_worker, which calls SimulationWorker
    from src.engine.runner.simulation_worker import run_single_campaign_wrapped
    result_async = pool.map_async(run_single_campaign_wrapped, tasks, chunksize=1)
    
    print(f"Starting Simulation Batch: {timestamp}")
    print(f"Output Directory: {batch_dir}")
    
    # Orchestration Loop
    progress_map = {} 
    map_str = f"{num_systems} Systems (~{num_systems * ((min_p+max_p)//2)} Worlds)"
    dashboard = ProgressDashboard()
    
    try:
        while not result_async.ready():
            while not q.empty():
                try:
                    data = q.get_nowait()
                    rid = data[0]
                    progress_map[rid] = data[1:]
                except:
                    break
            
            finished_count = sum(1 for v in progress_map.values() if "Done" in v[1] or "Error" in v[1])
            dashboard.draw(progress_map, num_runs, workers, finished_count, turns_per_run, output_path=batch_dir, map_config=map_str)
            time.sleep(1.0) 
            
        results = result_async.get()
        
        # Final Drain
        while not q.empty():
            try:
                data = q.get_nowait()
                rid = data[0]
                progress_map[rid] = data[1:]
            except: break
            
        finished_count = sum(1 for v in progress_map.values() if "Done" in v[1] or "Error" in v[1])
        
        # Result Aggregation
        aggregator = ResultsAggregator(batch_dir, num_runs)
        final_wins = defaultdict(int) 
        # Calculate wins here or delegate to Aggregator? 
        # Dashboard wants wins dict immediately for display.
        for r in results:
            if r and r.get('Winner') and r['Winner'] != 'Draw':
                final_wins[r['Winner']] += 1
                
        dashboard.draw(progress_map, num_runs, workers, finished_count, turns_per_run, output_path=batch_dir, map_config=map_str, is_done=True, wins=final_wins)
        
        # Save Consolidated CSV
        # Ideally Aggregator handles this, but we have `results` in memory here from map_async.
        # We can implement a simplified save here or update Aggregator to accept list.
        # For now, inline save to maintain behavior, but maybe move to Aggregator later.
        log_filename = os.path.join(batch_dir, f"campaign_batch_stats.csv")
        try:
             import csv
             with open(log_filename, mode='w', newline='', encoding='utf-8') as f:
                all_keys = set()
                valid_results = [r for r in results if r]
                for r in valid_results: all_keys.update(r.keys())
                fieldnames = sorted(list(all_keys))
                if 'RunID' in fieldnames: fieldnames.insert(0, fieldnames.pop(fieldnames.index('RunID')))
                if 'Winner' in fieldnames: fieldnames.insert(1, fieldnames.pop(fieldnames.index('Winner')))
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for r in valid_results: writer.writerow(r)
             print(f"Results saved to {log_filename}")
        except Exception as e:
             print(f"Error saving results: {e}")

    except KeyboardInterrupt:
        print("\nStopping...")
        pool.terminate()
        pool.join()

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Warhammer 40k Campaign Simulation Runner")
    parser.add_argument("--config", type=str, default="config/void_reckoning_config.json", help="Path to config file")
    parser.add_argument("--universe", type=str, help="Target universe name (e.g. void_reckoning)")
    parser.add_argument("--runs", type=int, help="Number of parallel runs")
    parser.add_argument("--turns", type=int, help="Number of turns per run")
    parser.add_argument("--output", type=str, help="Custom output directory")
    parser.add_argument("--headless", action="store_true", help="Run without dashboard visualization")

    args = parser.parse_args()

    config = load_config_from_file(args.config)
    
    # CLI Overrides
    if args.universe:
        config["universe"] = args.universe
    
    if args.runs:
        if "simulation" not in config: config["simulation"] = {}
        config["simulation"]["num_runs"] = args.runs
        
    if args.turns:
        if "campaign" not in config: config["campaign"] = {}
        config["campaign"]["turns"] = args.turns
        
    if args.output:
        if "simulation" not in config: config["simulation"] = {}
        config["simulation"]["output_dir"] = args.output
        
    if args.headless:
        # We might need to pass this down or handle it. 
        # Currently dashboard is attached if import works. 
        # We can implement a global flag or config override.
        if "reporting" not in config: config["reporting"] = {}
        config["reporting"]["enable_dashboard"] = False

    run_batch_simulation(config)

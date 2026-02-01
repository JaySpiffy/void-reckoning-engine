import argparse
import os
import sys
import logging

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reporting.indexer import ReportIndexer
from src.reporting.analytics_engine import AnalyticsEngine
from src.reporting import visualizations as viz

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    setup_logging()
    parser = argparse.ArgumentParser(description="Export Campaign Visualizations")
    parser.add_argument("--batch", type=str, required=True, help="Batch ID to process")
    parser.add_argument("--run", type=str, help="Specific Run ID (optional)")
    parser.add_argument("--universe", type=str, default="eternal_crusade", help="Universe name")
    parser.add_argument("--output-dir", type=str, default="reports/visualizations", help="Output directory")
    parser.add_argument("--format", type=str, default="png", choices=["png", "pdf", "svg"], help="Output format")
    
    args = parser.parse_args()
    
    # 1. Initialize Indexer
    # Assume standard DB path for now or typical location
    db_path = f"reports/{args.universe}/{args.batch}/index.db"
    
    if not os.path.exists(db_path):
        # Fallback to shared indexer if exists
        db_path = "reports/index.db"
        
    logging.info(f"Connecting to Indexer at {db_path}...")
    indexer = ReportIndexer(db_path)
    # Ensure indices/views
    indexer.create_analytics_views()
    
    engine = AnalyticsEngine(indexer)
    
    # 2. Determine Scope
    target_runs = []
    if args.run:
        target_runs.append(args.run)
    else:
        # TODO: Query all runs in batch?
        # For now, require run or process 'latest' logic if we had it.
        # Let's just warn if no run specified, or try to find one.
        pass

    if not args.run:
        logging.warning("No specific --run provided. Batch processing not fully implemented in this script version.")
        return

    # 3. Generate Visualizations for Run
    run_id = args.run
    universe = args.universe
    out_dir = os.path.join(args.output_dir, args.batch, run_id)
    os.makedirs(out_dir, exist_ok=True)
    
    logging.info(f"Generating visualizations for Run {run_id} in {out_dir}...")
    
    # A. Resource Trends (Per Faction)
    # Get active factions first?
    # Simple hardcoded check or query
    known_factions = ["Imperium", "Chaos", "Orks", "Eldar", "Tau", "Necrons", "Tyranids"]
    
    for faction in known_factions:
        logging.info(f"  > Processing {faction}...")
        df = indexer.query_faction_time_series(faction, universe, ['requisition', 'promethium', 'planets_controlled', 'battles_won'])
        
        if not df.empty:
            # Resources
            viz.plot_resource_trends(df, os.path.join(out_dir, f"{faction}_resources.{args.format}"))
            
            # Military Power
            if 'military_power' in df.columns: # Assuming indexer query returns this proxied or actual
                 viz.plot_military_power_evolution(df, os.path.join(out_dir, f"{faction}_mil_strength.{args.format}"))
            elif 'battles_won' in df.columns:
                 # Fallback if mil power not explicit in time series query yet
                 pass
            
    # B. Battle Heatmap
    logging.info("  > Generating Battle Heatmap...")
    battles = indexer.query_battle_statistics(universe)
    if not battles.empty:
        viz.plot_battle_intensity_heatmap(battles, os.path.join(out_dir, f"battle_heatmap.{args.format}"))
        
    logging.info("Done.")

if __name__ == "__main__":
    main()

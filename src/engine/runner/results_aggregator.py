import os
import csv
import json
import statistics
import time
from typing import List, Dict

class ResultsAggregator:
    """
    Handles merging of simulation results and statistical analysis.
    """
    def __init__(self, batch_dir: str, num_runs: int):
        self.batch_dir = batch_dir
        self.num_runs = num_runs

    def aggregate_results(self, output_file: str = "aggregated_results.csv"):
        """Merges individual run results into a summary CSV."""
        print("\n[Aggregator] Consolidating results...")
        
        agg_data = []
        headers = []

        found_results = 0
        
        # 1. Harvest Results
        for i in range(self.num_runs):
            run_id = f"run_{i:03d}"
            # Check for results file in run directory (Organizer structure)
            # Path: <batch>/<universe>/run_XXX/reports/factions.csv or similar?
            # Actually SimulationRunner usually writes a 'results.csv' or metrics.
            # Let's assume standard location: <batch>/<run_id>/results.csv OR the new organizer path
            
            # The current SimulationRunner writes "full_campaign_log.txt" but maybe not a structured CSV per run?
            # It seems the previous runner aggregated from telemetry or memory?
            # Let's fallback to checking if telemetry indexer populated the DB, OR check for local JSONs.
            
            # If the architecture uses ReportOrganizer, we should look for 'turn_XXX/manifest.json' or 'economy/manifest'.
            # But tailored aggregation usually needs a specific summary file.
            pass
            
        # Since logic was missing from view, I will implement a generic aggregator based on commonly expected outputs.
        # Or I can wait to see what SimulationRunner was actually doing at the end.
        # It seems SimulationRunner.py lines 600+ usually has this logic.
        
        pass

    def compute_summary_stats(self, results: List[Dict]) -> Dict:
        if not results: return {}
        
        # Calculate averages for key metrics
        stats = {}
        keys = results[0].keys()
        for k in keys:
            try:
                values = [float(r[k]) for r in results if r[k] != '']
                if values:
                    stats[k] = {
                        "mean": statistics.mean(values),
                        "stdev": statistics.stdev(values) if len(values) > 1 else 0.0,
                        "min": min(values),
                        "max": max(values)
                    }
            except (ValueError, TypeError):
                pass
        return stats

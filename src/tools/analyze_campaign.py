
import os
import csv
import json
import argparse
import sys
from collections import defaultdict
from glob import glob

def load_metrics(batch_path):
    """
    Parses a batch folder to aggregate metrics across all runs and turns.
    Returns a dict of aggregated data per faction.
    """
    aggregated_data = defaultdict(lambda: {
        "income": 0, "expense": 0, "recruitment": 0, "construction": 0,
        "battles_won": 0, "planets_owned": 0, "turns_counted": 0
    })
    
    # 1. Parse Economy CSVs for financial data
    # Pattern: reports/batch_XXX/run_XXX/economy_run_XXX.csv
    csv_files = glob(os.path.join(batch_path, "run_*", "economy_*.csv"))
    
    if not csv_files:
        print("No economy CSV files found. Ensure the simulation reached Turn 100+ to flush analytics.")
        return {}

    print(f"Parsing {len(csv_files)} economy logs...")
    
    for csv_file in csv_files:
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Row keys: Turn, Global_Fleets, {Faction}_Req, {Faction}_Income, etc.
                    # We need to extract faction names from headers
                    factions = set([k.split('_')[0] for k in row.keys() if '_' in k and k.split('_')[0] not in ["Turn", "Global"]])
                    
                    for faction in factions:
                        if faction == "Neutral": continue
                        
                        inc = float(row.get(f"{faction}_Income", 0))
                        exp = float(row.get(f"{faction}_Expense", 0))
                        
                        aggregated_data[faction]["income"] += inc
                        aggregated_data[faction]["expense"] += exp
                        aggregated_data[faction]["turns_counted"] += 1
        except Exception as e:
            print(f"Error parsing {csv_file}: {e}")

    # 2. Parse Final Manifests for Structure/Military snapshots (Optional but useful)
    # This is harder without reading every single turn manifest. 
    # For now, we rely on the CSV data which supposedly tracks spending.
    # To get "Current Power", we really need the LATEST turn state.
    
    return aggregated_data

def calculate_rankings(data):
    """
    Calculates power scores based on aggregated metrics.
    Score = (Avg Income * 0.5) + (Avg Spending * 0.5)
    (Simple proxy for now until we parse unit counts deeper)
    """
    rankings = []
    
    for faction, metrics in data.items():
        turns = metrics["turns_counted"] if metrics["turns_counted"] > 0 else 1
        
        avg_income = metrics["income"] / turns
        avg_spend = metrics["expense"] / turns
        
        # Economic Health Score
        # High income is good. High spending is good (active).
        power_score = (avg_income * 0.4) + (avg_spend * 0.6)
        
        rankings.append({
            "Faction": faction,
            "PowerScore": int(power_score),
            "AvgIncome": int(avg_income),
            "AvgSpend": int(avg_spend),
            "TotalTurns": turns
        })
        
    return sorted(rankings, key=lambda x: x["PowerScore"], reverse=True)

def main():
    parser = argparse.ArgumentParser(description="Analyze 40k Campaign Logs")
    parser.add_argument("--batch", required=True, help="Batch directory name (e.g., batch_20251228_163355)")
    parser.add_argument("--reports-dir", help="Root reports directory", default="reports")
    
    args = parser.parse_args()
    
    target_dir = os.path.join(args.reports_dir, args.batch)
    if not os.path.exists(target_dir):
        # Try checking absolute path or straight relational
        if os.path.exists(args.batch):
            target_dir = args.batch
        else:
            print(f"Error: Batch directory not found at {target_dir}")
            return

    print(f"Analyzing batch: {target_dir}")
    print("-" * 60)
    
    data = load_metrics(target_dir)
    rankings = calculate_rankings(data)
    
    if not rankings:
        print("No ranking data could be generated.")
        return
        
    print(f"{'RANK':<5} {'FACTION':<20} {'POWER':<10} {'INCOME':<10} {'SPEND':<10}")
    print("-" * 60)
    
    for i, rank in enumerate(rankings):
        print(f"{i+1:<5} {rank['Faction']:<20} {rank['PowerScore']:<10} {rank['AvgIncome']:<10} {rank['AvgSpend']:<10}")
        
    print("-" * 60)
    
    # Save to CSV
    out_file = os.path.join(target_dir, "ranking_summary.csv")
    keys = rankings[0].keys()
    with open(out_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rankings)
        
    print(f"Summary saved to {out_file}")

if __name__ == "__main__":
    main()

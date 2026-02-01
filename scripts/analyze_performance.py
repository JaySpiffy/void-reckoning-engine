
import json
import os
import glob
from collections import defaultdict
import statistics

TRACK_METRICS = [
    "process_faction_turn",
    "update_faction_visibility",
    "economy_phase_total",
    "process_turn"
]

def analyze_telemetry(report_dir="reports/telemetry"):
    print(f"Analyzing Performance Telemetry in {report_dir}...")
    
    files = glob.glob(os.path.join(report_dir, "*.json"))
    if not files:
        print("No telemetry files found.")
        return

    data_store = defaultdict(list)

    for file_path in files:
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    try:
                        event = json.loads(line)
                        if event.get("event_type") == "performance_summary":
                            data = event.get("data", {})
                            for metric_name, metric_data in data.items():
                                if metric_name in TRACK_METRICS or True: # Capture all
                                    if isinstance(metric_data, dict) and "avg_ms" in metric_data:
                                        data_store[metric_name].append(metric_data["avg_ms"])
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    print("\n=== PERFORMANCE SUMMARY REPORT ===")
    print(f"{'Metric':<30} | {'Count':<5} | {'Avg (ms)':<10} | {'Max (ms)':<10} | {'P95 (ms)':<10}")
    print("-" * 80)
    
    for metric in sorted(data_store.keys()):
        values = sorted(data_store[metric])
        if not values: continue
        
        count = len(values)
        avg = statistics.mean(values)
        max_val = max(values)
        p95 = values[int(count * 0.95)] if count > 0 else 0
        
        print(f"{metric:<30} | {count:<5} | {avg:<10.2f} | {max_val:<10.2f} | {p95:<10.2f}")

    print("\nanalysis complete.")

if __name__ == "__main__":
    analyze_telemetry()

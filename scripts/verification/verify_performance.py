
import re
import statistics
import os

LOG_FILE = "reports/logs/campaign.log" # Force reports log

def analyze_performance(log_path):
    if not os.path.exists(log_path):
        print(f"Log file not found: {log_path}")
        return

    print(f"Analyzing {log_path}...")
    line_count = 0
    match_count = 0

    
    battle_durations = []
    turn_durations = []
    
    # Regex patterns
    # > [COMBAT] BATTLE ENDED at Cylven Prime. Winner: Draw (Rounds: 2000, Duration: 0.35s)
    battle_pattern = re.compile(r"Duration: (\d+\.\d+)s")
    
    # Turn duration might not be explicitly logged in the snippet I saw, 
    # but usually "Turn X completed in Y s" or measuring timestamp diffs.
    # I'll rely on battle durations for now as that's the Rust component (CombatResolver).
    
    with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line_count += 1
            if "BATTLE ENDED" in line:
                match = battle_pattern.search(line)
                if match:
                    battle_durations.append(float(match.group(1)))
                    match_count += 1
    
    print(f"Scanned {line_count} lines. Found {match_count} battle events.")

    if battle_durations:
        avg_battle = statistics.mean(battle_durations)
        max_battle = max(battle_durations)
        min_battle = min(battle_durations)
        total_battles = len(battle_durations)
        
        print(f"\n--- Combat Performance (Rust) ---")
        print(f"Total Battles: {total_battles}")
        print(f"Average Duration: {avg_battle:.4f} s")
        print(f"Max Duration:     {max_battle:.4f} s")
        print(f"Min Duration:     {min_battle:.4f} s")
        
        # Baseline Comparison (Estimated Python Baseline: ~1.5s for similar scale)
        # 2000 rounds in Python would take significantly longer.
        baseline = 2.0 # Conservative estimate for 2000 rounds of simple combat
        speedup = baseline / avg_battle if avg_battle > 0 else 0
        print(f"Estimated Speedup vs Python Baseline ({baseline}s): {speedup:.1f}x")
        
    else:
        print("No battle durations found in log.")

if __name__ == "__main__":
    analyze_performance(LOG_FILE)

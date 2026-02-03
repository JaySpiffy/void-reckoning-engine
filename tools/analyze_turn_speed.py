import re
from datetime import datetime

log_file = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260203_084745\void_reckoning\runs\run_001\campaign.log"

def analyze_turn_speed():
    turn_times = {}
    
    # regex to match [TIME] [LEVEL] [SYSTEM] === TURN X GLOBAL PHASE ===
    start_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}) \[INFO\] \[SYSTEM\] === TURN (\d+) GLOBAL PHASE ===")
    end_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}) \[INFO\] \[SYSTEM\] === END OF TURN (\d+) ===")
    
    with open(log_file, 'r') as f:
        for line in f:
            start_match = start_pattern.search(line)
            if start_match:
                time_str, turn_str = start_match.groups()
                turn_num = int(turn_str)
                time_val = datetime.strptime(time_str, "%H:%M:%S")
                turn_times[turn_num] = {'start': time_val}
                
            end_match = end_pattern.search(line)
            if end_match:
                time_str, turn_str = end_match.groups()
                turn_num = int(turn_str)
                time_val = datetime.strptime(time_str, "%H:%M:%S")
                if turn_num in turn_times:
                    turn_times[turn_num]['end'] = time_val
                    duration = (time_val - turn_times[turn_num]['start']).total_seconds()
                    turn_times[turn_num]['duration'] = duration

    print(f"{'Turn':<6} | {'Start':<10} | {'End':<10} | {'Duration (s)':<12}")
    print("-" * 45)
    
    durations = []
    for turn in sorted(turn_times.keys()):
        data = turn_times[turn]
        if 'duration' in data:
            print(f"{turn:<6} | {data['start'].strftime('%H:%M:%S'):<10} | {data['end'].strftime('%H:%M:%S'):<10} | {data['duration']:<12.2f}")
            durations.append(data['duration'])
            
    if durations:
        avg_speed = sum(durations) / len(durations)
        print("-" * 45)
        print(f"Average Turn Speed: {avg_speed:.2f} seconds")
        print(f"Max Turn Speed: {max(durations):.2f} seconds (Turn {durations.index(max(durations))+1})")
        print(f"Min Turn Speed: {min(durations):.2f} seconds")

if __name__ == "__main__":
    analyze_turn_speed()

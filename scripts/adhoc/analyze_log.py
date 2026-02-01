
import os

log_path = r"C:\Users\whitt\OneDrive\Desktop\New folder (4)\reports\multi_universe_20260120_130912\eternal_crusade\eternal_crusade\batch_20260120_130913\run_001\full_campaign_log.txt"

print(f"Reading log: {log_path}")

try:
    with open(log_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    gpu_lines = [l.strip() for l in lines if "Logic backend initialized" in l or "Legacy CPU" in l]
    error_lines = [l.strip() for l in lines if "ERROR" in l or "WARNING" in l]
    
    print("\n--- GPU CONFIRMATION ---")
    if gpu_lines:
        for l in gpu_lines:
            print(l)
    else:
        print("No GPU backend log found.")

    print("\n--- STARTUP ERRORS/WARNINGS (First 20) ---")
    for l in error_lines[:20]:
        print(l)

except Exception as e:
    print(f"Error reading log: {e}")

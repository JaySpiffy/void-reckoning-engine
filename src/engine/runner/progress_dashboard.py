import os
from src.core import gpu_utils

class ProgressDashboard:
    """
    Handles terminal visualization of simulation progress.
    """
    def __init__(self):
        pass

    def draw(self, progress_map, num_runs, active_workers, total_finished, turns_per_run, output_path="", map_config="", is_done=False, wins=None):
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Check for dynamic planet count override
        dynamic_map_str = map_config
        try:
            if progress_map:
                first_key = next(iter(progress_map))
                first_data = progress_map[first_key]
                if len(first_data) >= 3 and isinstance(first_data[2], dict):
                     stats = first_data[2]
                     if 'GLOBAL_PLANETS' in stats:
                         base_sys = map_config.split('(')[0].strip() if '(' in map_config else "Galaxy"
                         dynamic_map_str = f"{base_sys} (Exact: {stats['GLOBAL_PLANETS']} Worlds)"
        except: 
            pass

        dashboard_title = "--- SIMULATION COMPLETE ---" if is_done else "--- SIMULATION DASHBOARD (Config-Driven) ---"
        print(dashboard_title)
        print(f"Active Workers: {active_workers} | Completed: {total_finished}/{num_runs}")
        if dynamic_map_str:
            print(f"Map Config: {dynamic_map_str}")
        if output_path:
            # Build hardware info line
            hw_line = f"Output Path: {output_path}"
            selected_gpu = gpu_utils.get_selected_gpu()
            if selected_gpu:
                hw_line += f" | GPU: {selected_gpu.model.value} (Dev {selected_gpu.device_id})"
            else:
                hw_gpus = gpu_utils.get_hardware_gpu_info()
                if hw_gpus:
                    hw_line += f" | GPU: {hw_gpus[0]['name']} (HW Only)"
                else:
                    hw_line += f" | GPU: CPU-Only Fallback"
            print(hw_line)
        print("-" * 80)
        
        sorted_ids = sorted(progress_map.keys())
        shown_count = 0
        
        for rid in sorted_ids:
            data = progress_map[rid]
            turn = data[0]
            status = data[1]
            stats = data[2] if len(data) > 2 else {}
            
            # Format Bar
            pct = min(1.0, turn / float(turns_per_run)) if turns_per_run > 0 else 0
            bar_len = 20
            filled = int(bar_len * pct)
            bar = "=" * filled + "-" * (bar_len - filled)
            
            if "Done" in status:
                color_status = status 
            elif "Error" in status:
                color_status = "!ERROR!"
            else:
                color_status = f"{turn}/{turns_per_run}"

            print(f"Run {rid:03d}: [{bar}] {color_status}")
            
            # Render Detailed Stats Below
            if stats:
                print("   --- FACTION STATISTICS ---")
                sorted_factions = sorted(stats.items(), key=lambda x: x[1]['Score'] if isinstance(x[1], dict) and 'Score' in x[1] else 0, reverse=True)
                display_factions = [(k,v) for k,v in sorted_factions if not k.startswith('GLOBAL_')]
                
                abbr_map = {
                    "Templars_of_the_Flux": "TPL",
                    "Transcendent_Order": "TRA",
                    "SteelBound_Syndicate": "STE",
                    "BioTide_Collective": "BIO",
                    "Algorithmic_Hierarchy": "ALG",
                    "Nebula_Drifters": "NEB",
                    "Aurelian_Hegemony": "AUR",
                    "VoidSpawn_Entities": "VOI",
                    "ScrapLord_Marauders": "SCR",
                    "Primeval_Sentinels": "PRM"
                }
                
                for i, (faction, s) in enumerate(display_factions, 1):
                    if not isinstance(s, dict): continue
                    # [DASHBOARD-FIX] Parse Instance ID (e.g. "Templars_of_the_Flux 2" -> "2TPL")
                    parts = faction.rsplit(' ', 1)
                    base_name = parts[0]
                    instance_suffix = ""
                    
                    if len(parts) > 1 and parts[1].isdigit():
                        instance_suffix = parts[1]
                        
                    # Lookup abbr generally on base name
                    abbr = abbr_map.get(base_name, base_name[:3].upper())
                    
                    # Construct Code
                    code = f"{instance_suffix}{abbr}" 
                    if len(code) > 4: code = code[:4] # Clip to 4 chars
                    score = s.get('Score', 0)
                    wl_ratio = f"{s.get('BW',0)}/{s.get('BF',0)}"
                    posture = s.get('Post', 'BALANCED')[:4]
                    
                    entry = f"   #{i:<2} {code:<3}: Score: {score:>7} | Sys: {s.get('S',0):>2} | P: {s['P']:>2} | B: {s.get('B',0):>3} | SB: {s.get('SB',0):>2} | F: {s['F']:>3} | A: {s.get('A',0):>3} | Req: {s.get('R',0):>8} | Tech: {s.get('T',0):>2} | L: {s.get('L',0):>3} | W/L: {wl_ratio:>7} | {posture}"
                    print(entry)
                
                print("") 
            
            shown_count += 1
            if shown_count >= 25:
                print(f"... and {len(sorted_ids) - 25} more ...")
                break
                
        # Global Footer Summary
        if progress_map:
            first_key = next(iter(progress_map))
            first_stats = progress_map[first_key][2] if len(progress_map[first_key]) > 2 else {}
            if 'GLOBAL_NEUTRAL' in first_stats:
                print(f"GLOBAL SUMMARY: Neutral Worlds: {first_stats.get('GLOBAL_NEUTRAL', 0)} | Flux Storm: {first_stats.get('GLOBAL_STORMS', 0)} | Active Battles: {first_stats.get('GLOBAL_BATTLES', 0)}")
        
        print("-" * 80)
        if is_done and wins:
            print("FINAL WIN COUNT SUMMARY:")
            sorted_wins = sorted(wins.items(), key=lambda x: x[1], reverse=True)
            for faction, count in sorted_wins:
                print(f"  {faction:<15}: {count}")
            print("-" * 80)
        
        if not is_done:
            print("Press Ctrl+C to stop.")

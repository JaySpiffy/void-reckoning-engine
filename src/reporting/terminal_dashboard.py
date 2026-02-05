import os
import sys
import time
from typing import Dict, Any, List
from src.core.constants import FACTION_ABBREVIATIONS
from src.core import gpu_utils

# ANSI Colors
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
WHITE = "\033[97m"
MAGENTA = "\033[95m"
BLACK = "\033[30m"
ON_YELLOW = "\033[43m"


class TerminalDashboard:
    """
    Handles terminal-based visualization of multi-universe simulation progress.
    Now with interactivity and keyboard shortcuts!
    """
    def __init__(self):
        self.is_paused = False
        self.faction_filter = ""
        self.faction_detail_mode = "SUMMARY" # HIDDEN, SUMMARY, EVERYTHING
        self.show_galactic_summary = True
        self.show_diplomacy = "SUMMARY" # OFF, SUMMARY, EVERYTHING, NO_WAR
        self.show_help = False
        self.show_theaters = False
        self.show_victory = False
        self.show_alerts = False
        self.show_map = False
        self.show_map = False
        self.global_stats_mode = "FULL" # FULL, COMPACT
        
        self.quit_requested = False
        self.filter_buffer = ""
        self.is_filtering = False
        self.last_progress_data = {}
        self.last_universe_configs = []
        self.trend_data = {} # Faction trends
        self.global_trend_data = {} # Global trends
        self.last_export_status = ""
        self.last_export_status = ""
        self.last_export_time = 0
        self.session_start_time = time.time()


    def handle_input(self, key: str | None):
        """Processes keyboard input to update dashboard state."""
        if not key:
            return

        if self.is_filtering:
            if key == '\r' or key == '\n':
                self.faction_filter = self.filter_buffer.upper()
                self.filter_buffer = ""
                self.is_filtering = False
            elif key == '\x08' or key == '\x7f': # Backspace
                self.filter_buffer = self.filter_buffer[:-1]
            elif key == '\x1b': # Esc
                self.filter_buffer = ""
                self.is_filtering = False
            else:
                self.filter_buffer += key
            return

        if key == 'q':
            self.quit_requested = True
        elif key == 'p':
            self.is_paused = not self.is_paused
        elif key == 'd':
            # Cycle diplomacy view
            modes = ["OFF", "SUMMARY", "EVERYTHING", "NO_WAR"]
            curr_idx = modes.index(self.show_diplomacy) if self.show_diplomacy in modes else 0
            self.show_diplomacy = modes[(curr_idx + 1) % len(modes)]
        elif key == 'y':
            # Cycle faction details
            modes = ["HIDDEN", "SUMMARY", "EVERYTHING"]
            curr_idx = modes.index(self.faction_detail_mode)
            self.faction_detail_mode = modes[(curr_idx + 1) % len(modes)]
        elif key == '?':
            self.show_help = not self.show_help
        elif key == 'f':
            self.is_filtering = True
            self.filter_buffer = ""
        elif key == 't':
            self.show_theaters = not self.show_theaters
        elif key == 'v':
            self.show_victory = not self.show_victory
        elif key == 'a':
            self.show_alerts = not self.show_alerts
        elif key == 'h' or key == '?':
            self.show_help = not self.show_help
        elif key == 'm':
            self.show_map = not self.show_map
        elif key == 'e' or key == 'c':
            self._export_session_data() # Export / Capture
        elif key == 's':
            self.global_stats_mode = "COMPACT" if self.global_stats_mode == "FULL" else "FULL"
        elif key == 'r':
            pass
        elif key.isdigit():
            self.faction_filter = f"INDEX_{key}"


    def render(self, output_dir: str, progress_data: Dict[str, Any], universe_configs: List[Dict[str, Any]]):
        """
        Renders the full dashboard to the terminal using double-buffering for performance.
        """
        # Cache data if not paused
        if not self.is_paused:
            self.last_progress_data = progress_data
            self.last_universe_configs = universe_configs

        # Use cached data if paused
        data_to_render = self.last_progress_data if self.is_paused else progress_data
        configs_to_render = self.last_universe_configs if self.is_paused else universe_configs

        buffer = []
        if os.name == 'nt':
            os.system('cls')
        else:
            buffer.append("\033[2J\033[H")

        # Core Header: Title & Metadata
        buffer.append(f"{CYAN}{'━' * 80}{RESET}")
        title = "MULTI-UNIVERSE SIMULATION DASHBOARD"
        buffer.append(f" {BOLD}{WHITE}{title.center(78)}{RESET}")
        
        gpu_info = gpu_utils.get_selected_gpu()
        gpu_str = f"{gpu_info.model.value} (Device {gpu_info.device_id})" if gpu_info else "N/A"
        buffer.append(f" {DIM}Output: {output_dir} | {GREEN}GPU: {gpu_str}{RESET}")
        buffer.append(f"{CYAN}{'━' * 80}{RESET}")
        
        # Data derivation
        current_turn = 0
        total_turns = 100
        if configs_to_render and "game_config" in configs_to_render[0]:
            total_turns = configs_to_render[0]["game_config"].get("campaign", {}).get("turns", 100)
        
        current_stats = {}
        if data_to_render and configs_to_render:
            first_universe_name = configs_to_render[0]["universe_name"]
            runs = data_to_render.get(first_universe_name, {}).get("runs", {})
            
            # Robust lookup: Try "001", then integer 1, then any run
            run_data = runs.get("001") or runs.get(1)
            if not run_data and runs:
                first_id = next(iter(runs))
                run_data = runs[first_id]
                
            if run_data:
                current_stats = run_data.get("stats", {})
                current_turn = run_data.get('turn', 0)

        # Controls Footer (Now Header for visibility in mockup)
        ctrl_line = f" {BOLD}Controls:{RESET} {DIM}(q)uit (p)ause (d)iplomacy (y)details (s)ummary (f)ilter (h)elp (a)lerts (v)ictory (m)ap{RESET}"
        if self.is_paused:
            ctrl_line += f" | {BOLD}{BLACK}{ON_YELLOW} PAUSED {RESET}"
        if self.faction_filter:
            ctrl_line += f" | {BOLD}{YELLOW}Filter: {self.faction_filter}{RESET}"
        buffer.append(ctrl_line)

        # Performance & ETA Line
        elapsed_total = int(time.time() - self.session_start_time)
        el_m, el_s = divmod(elapsed_total, 60)
        
        perf_time = current_stats.get('GLOBAL_PERF_TURN_TIME', 0)
        perf_tps = current_stats.get('GLOBAL_PERF_TPS', 0)
        mem = current_stats.get('GLOBAL_PERF_MEMORY', 0)
        mem_trend = self._get_trend_icon('GLOBAL_PERF_MEMORY')
        
        turns_left = max(0, total_turns - current_turn)
        eta_seconds = int(turns_left * perf_time)
        eta_m, eta_s = divmod(eta_seconds, 60)

        perf_time_str = f"{perf_time:.2f}s/turn" if perf_time > 0 else "CALCULATING..."
        perf_tps_str = f"{perf_tps:.2f} tps" if perf_tps > 0 else "CALCULATING..."
        mem_str = f"{int(mem)}MB" if mem > 0 else "0MB"
        eta_str = f"{eta_m}m {eta_s}s" if eta_seconds > 0 else "---"

        info_line = f" {BOLD}Elapsed:{RESET} {el_m}m {el_s}s | {DIM}⏱ {perf_time_str}{RESET} | {BOLD}🚀 {perf_tps_str}{RESET} | {MAGENTA}🧠 {mem_str} {mem_trend}{RESET} | {YELLOW}ETA: {eta_str}{RESET}"
        buffer.append(info_line)
        buffer.append(f"{CYAN}{'─' * 80}{RESET}")

        if self.show_help:
            self._render_help_overlay(buffer)
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return

        if self.show_alerts:
            self._render_alerts_overlay(current_stats, buffer)
            
        if self.show_victory:
            self._render_victory_overlay(current_stats, buffer)
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return

        if self.show_map:
            self._render_map_overlay(current_stats, buffer)
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return

        if self.is_filtering:
            buffer.append(f"\n   {BOLD}{YELLOW}ENTER FACTION TAG TO FILTER:{RESET} {WHITE}{self.filter_buffer}{RESET}_")
            buffer.append(f"   {DIM}(Press Enter to confirm, Esc to cancel){RESET}")

        
        for config in configs_to_render:
            name = config["universe_name"]
            data = data_to_render.get(name, {})
            completed = data.get("completed", 0)
            total = config["num_runs"]
            affinity = config.get("processor_affinity", "Auto")
            
            # Universe Section
            header_color = GREEN if completed == total else YELLOW
            buffer.append(f"\n{BOLD}{header_color}[{name.upper()}] {RESET}- Cores: {affinity}")
            buffer.append(f"  {BOLD}Progress:{RESET} {completed}/{total} Runs Completed")
            
            # Show top 5 active/recent runs
            runs = data.get("runs", {})
            sorted_runs = sorted(runs.items(), key=lambda x: x[0])
            
            # Filter for running first, then done
            active = [r for r in sorted_runs if "Done" not in r[1]["status"]]
            done = [r for r in sorted_runs if "Done" in r[1]["status"]]
            
            # Show active runs with progress bars
            for rid, rdata in active[:5]:
                turn_num = rdata.get("turn", 0)
                max_turns = config["game_config"]["campaign"].get("turns", 100)
                bar = self._make_bar(turn_num, max_turns)
                status = rdata['status']
                status_color = RED if "Error" in status else (YELLOW if "Waiting" in status else GREEN)
                
                rid_display = f"{int(rid):03d}" if str(rid).isdigit() else str(rid)[:3]
                buffer.append(f"  Run {rid_display}: {bar} {DIM}Turn{RESET} {turn_num:>3} | {status_color}{status}{RESET}")

                self._render_faction_summary(rdata.get("stats", {}), buffer, is_final=False)

            if len(active) > 5:
                buffer.append(f"  {DIM}... {len(active)-5} more active ...{RESET}")
                
            # Show latest done (if no active)
            if done and not active:
                last_rid, last_rdata = done[-1]
                last_rid_display = f"{int(last_rid):03d}" if str(last_rid).isdigit() else str(last_rid)[:3]
                buffer.append(f"  Run {last_rid_display}: {BOLD}{GREEN}[DONE]{RESET} {last_rdata['status']}")
                self._render_faction_summary(last_rdata.get("stats", {}), buffer, is_final=True)
                
        # Flush Buffer Once
        sys.stdout.write("\n".join(buffer) + "\n")
        
        # [IMPROVEMENT] Print Traceback ONLY if there's an error and we just finished
        # Iterate again to find errors
        # Note: We can't clear screen easily if we print traceback, so it will append to bottom.
        for config in universe_configs:
            name = config["universe_name"]
            data = progress_data.get(name, {})
            runs = data.get("runs", {})
            for rid, rdata in runs.items():
                if "Error" in rdata.get("status", "") and "error_trace" in rdata.get("stats", {}):
                    # We found a trace. Print it nicely.
                    err_trace = rdata["stats"]["error_trace"]
                    print(f"\n{RED}!!! RUN {rid} CRITICAL FAILURE !!!{RESET}")
                    print(f"{DIM}{err_trace}{RESET}")
                    # Clear it so we don't spam print every frame? 
                    # Actually dashboard is a loop. If we print this, it will be wiped next frame?
                    # The 'render' overwrites.
                    # If we print to stdout, it might get overwritten by next render frame's 'cls' or overwrite.
                    # But the User asked for it.
                    # Best approach: If we detect error, we stop clearing screen? Or append it to buffer?
                    # Appending to buffer makes it part of the frame.
                    pass

        sys.stdout.flush()

    def _render_help_overlay(self, buffer: list):
        buffer.append(f"\n   {BOLD}{WHITE}╔════ INTERACTIVE SHORTCUTS ════╗{RESET}")
        buffer.append(f"   ║ {YELLOW}q{RESET} : Quit Dashboard / Stop Sim ║")
        buffer.append(f"   ║ {YELLOW}p{RESET} : Pause/Resume Display      ║")
        buffer.append(f"   ║ {YELLOW}d{RESET} : Cycle Diplomacy Views    ║")
        buffer.append(f"   ║ {YELLOW}y{RESET} : Cycle Faction Details    ║")
        buffer.append(f"   ║ {YELLOW}s{RESET} : Cycle Galactic Summary   ║")
        buffer.append(f"   ║ {YELLOW}f{RESET} : Filter by Faction Tag     ║")
        buffer.append(f"   ║ {YELLOW}t{RESET} : Toggle Military Theaters  ║")
        buffer.append(f"   ║ {YELLOW}v{RESET} : Toggle Victory Progress   ║")
        buffer.append(f"   ║ {YELLOW}a{RESET} : Toggle Alert History      ║")
        buffer.append(f"   ║ {YELLOW}m{RESET} : Toggle Galaxy map         ║")
        buffer.append(f"   ║ {YELLOW}e{RESET} : Export / Save Screenshot  ║")
        buffer.append(f"   ║ {YELLOW}h{RESET} : Toggle Help Overlay       ║")
        buffer.append(f"   ║ {YELLOW}1-9{RESET} : Quick Filter Index      ║")
        buffer.append(f"   {BOLD}{WHITE}╚═══════════════════════════════╝{RESET}")


    def _update_trends(self, stats: dict):
        """Calculates global trends by comparing current stats with previous turn."""
        if not stats: return
        
        for k, v in stats.items():
            if k.startswith("GLOBAL_") and isinstance(v, (int, float)):
                if k in self.global_trend_data:
                    prev = self.global_trend_data[k]["value"]
                    if v > prev: self.global_trend_data[k]["trend"] = "UP"
                    elif v < prev: self.global_trend_data[k]["trend"] = "DOWN"
                    else: self.global_trend_data[k]["trend"] = "STABLE"
                    self.global_trend_data[k]["prev"] = prev
                else:
                    self.global_trend_data[k] = {"trend": "STABLE", "prev": v}
                self.global_trend_data[k]["value"] = v

    def _get_trend_icon(self, key: str) -> str:
        """Returns ↑, ↓, or → based on trend."""
        trend = self.global_trend_data.get(key, {}).get("trend", "STABLE")
        if trend == "UP": return f"{GREEN}↑{RESET}"
        if trend == "DOWN": return f"{RED}↓{RESET}"
        return f"{DIM}→{RESET}"

    def _render_faction_summary(self, stats: dict, buffer: list, is_final: bool = False):
        """Helper for rendering faction summary in dashboard. Appends to buffer."""
        if not stats:
            return
            
        self._update_trends(stats)
        
        if self.show_galactic_summary:
            if self.global_stats_mode == "FULL":
                self._render_boxed_summary(stats, buffer)
            else:
                # Compact Line (Quick Stats)
                p = stats.get('GLOBAL_PLANETS', 0)
                n = stats.get('GLOBAL_NEUTRAL', 0)
                b = stats.get('GLOBAL_BATTLES', 0)
                c = stats.get('GLOBAL_CASUALTIES_SHIP', 0) + stats.get('GLOBAL_CASUALTIES_GROUND', 0)
                r = format_large_num(stats.get('GLOBAL_REQUISITION', 0))
                t = stats.get('GLOBAL_PERF_TURN_TIME', 0)
                buffer.append(f"     {BOLD}[Q] Quick:{RESET} P:{p} N:{n} B:{b} C:{c} R:{r} T:{t:.2f}s")



        
        # Phase 5: Theater Overview (Top Faction)
        # The dashboard receives pre-processed stats, so we need to extract theater info from there.
        # Assuming 'stats' might contain a 'GLOBAL_THEATERS' key or similar, or we derive it.
        # For now, we'll simulate based on the strongest faction from the stats.
        
        # Find strongest faction by score to show their theater breakdown
        # Display Diplomacy (Alliances & Trade)
        diplomacy = stats.get('GLOBAL_DIPLOMACY', [])
        if diplomacy and self.show_diplomacy != "OFF":
            wars = sum(1 for d in diplomacy if d['type'] == 'War')
            allies = sum(1 for d in diplomacy if d['type'] == 'Alliance')
            trades = sum(1 for d in diplomacy if d['type'] == 'Trade')
            
            buffer.append(f"     {MAGENTA}[GALACTIC DIPLOMACY] ({self.show_diplomacy}){RESET}")
            if self.show_diplomacy == "SUMMARY":
                buffer.append(f"     {RED}⚔ {wars}{RESET} wars | {CYAN}🤝 {allies}{RESET} alliances | {GREEN}📦 {trades}{RESET} trades")
            
            # 1. Identify Alliance Groups
            alliance_groups = self._identify_alliance_groups(diplomacy)
            
            # Map faction -> group_index for coloring
            faction_to_group = {}
            for idx, group in enumerate(alliance_groups):
                for member in group:
                    faction_to_group[member] = idx

            # Only show icons if not in SUMMARY mode
            if self.show_diplomacy in ["EVERYTHING", "NO_WAR"]:
                # Priorities: War > Alliance > Vassal > Trade
                def get_dip_prio(d):
                    t = d['type']
                    if t == 'War': return 0
                    if t == 'Alliance': return 1
                    if t == 'Vassal': return 2
                    return 3
                
                # Filter if NO_WAR
                dip_to_show = diplomacy
                if self.show_diplomacy == "NO_WAR":
                    dip_to_show = [d for d in diplomacy if d['type'] != 'War']
                
                dip_to_show.sort(key=get_dip_prio)
                
                formatted_entries = []
                for entry in dip_to_show:
                    pair = entry['members']
                    n1, n2 = pair[0], pair[1]
                    
                    def get_tag_with_instance(name):
                        parts = name.rsplit(' ', 1)
                        base = parts[0]
                        instance = parts[1] if len(parts) > 1 and parts[1].isdigit() else ""
                        abbr = FACTION_ABBREVIATIONS.get(base, base[:3].upper())
                        return f"{instance}{abbr}"[:4]

                    n1_s = get_tag_with_instance(n1)
                    n2_s = get_tag_with_instance(n2)
                    
                    t_type = entry['type']
                    if t_type == 'War':
                        type_color = RED
                        icon = "⚔"
                    elif t_type == 'Alliance':
                        g_idx = faction_to_group.get(n1)
                        if g_idx is not None and g_idx == faction_to_group.get(n2):
                             type_color = self._get_group_color(g_idx)
                        else:
                             type_color = GREEN
                        icon = "🤝"
                    elif t_type == 'Vassal':
                        type_color = CYAN
                        icon = "👑"
                    else:
                        type_color = BLUE
                        icon = "💰"
                    
                    formatted_entries.append(f"{type_color}{icon} {n1_s}-{n2_s}{RESET}")

                # Render in columns (4 per line)
                cols = 4
                for i in range(0, len(formatted_entries), cols):
                    row = formatted_entries[i:i+cols]
                    buffer.append("     " + "   ".join(row))
            
            # Render Explicit Alliance Blocs if any exist
            if alliance_groups:
                 buffer.append(f"     {DIM}--- ALLIANCE BLOCS ---{RESET}")
                 for idx, group in enumerate(alliance_groups):
                      if len(group) < 2: continue
                      
                      color = self._get_group_color(idx)
                      names = [f"{n[:3].upper()}" for n in group]
                      names_str = ", ".join(names)
                      buffer.append(f"     {color}Bloc {idx+1}: [{names_str}]{RESET}")

        elif self.show_diplomacy != "OFF":
             buffer.append(f"     {DIM}[DIPLOMACY] {self.show_diplomacy} - Waiting for data...{RESET}")
        else:
             buffer.append(f"     {DIM}[DIPLOMACY] No active treaties.{RESET}")

        header_text = "FINAL FACTION STATISTICS" if is_final else "TOP FACTION STATISTICS"
        header_color = MAGENTA if is_final else BLUE
        
        if self.faction_detail_mode != "HIDDEN":
            limit = 10 if self.faction_detail_mode == "SUMMARY" else None
            buffer.append(f"     {header_color}{'-'*3} {header_text} ({self.faction_detail_mode}) {'-'*3}{RESET}")
            self._print_faction_stats(stats, buffer, limit=limit)
            if not is_final:
                buffer.append("") # Spacer
        elif not is_final:
            buffer.append(f"     {DIM}(FACTION DETAILS HIDDEN - press 'y' to cycle modes){RESET}")

    def _print_faction_stats(self, stats: dict, buffer: list, limit: int | None = None):
        """Helper to render faction statistics table to buffer."""
        # Sort by Score desc
        sorted_factions = sorted(stats.items(), key=lambda x: x[1]['Score'] if isinstance(x[1], dict) and 'Score' in x[1] else 0, reverse=True)
        
        # Filter for display
        to_display = []
        for f, s in sorted_factions:
            if not isinstance(s, dict) or f.startswith("GLOBAL_"):
                continue
            
            # Apply Filter
            if self.faction_filter:
                parts = f.rsplit(' ', 1)
                base = parts[0]
                instance = parts[1] if len(parts) > 1 and parts[1].isdigit() else ""
                abbr = FACTION_ABBREVIATIONS.get(base, base[:3].upper())
                tag = f"{instance}{abbr}".upper()
                if self.faction_filter not in tag and self.faction_filter not in f.upper():
                    continue

            to_display.append((f, s))
        
        if limit:
            to_display = to_display[:limit]
            
        # Headers
        buffer.append(f"     {DIM}{'#':<3} {'TAG':<4} {'SCORE':>7}  {'SYS':>3} {'OWN(A)':>7} {'CON(A)':>7} {'CTY':>3} {'B(AVG)':>9} {'SB':>3} {'F(AVG)':>7} {'A(AVG)':>7} {'REQ':>8} {'T':>3} {'WRS':>3} {'W/L/D':>8} {'L(S)':>4} {'L(G)':>4} {'POST':>4}{RESET}")

        for i, (faction, s) in enumerate(to_display, 1):

             if not isinstance(s, dict): continue
             
             parts = faction.rsplit(' ', 1)
             base_name = parts[0]
             instance_suffix = ""
             if len(parts) > 1 and parts[1].isdigit():
                 instance_suffix = parts[1]
             
             if base_name in FACTION_ABBREVIATIONS:
                 abbr = FACTION_ABBREVIATIONS[base_name]
             else:
                 abbr = base_name[:3].upper()
                 
             code = f"{instance_suffix}{abbr}" 
             if len(code) > 4: code = code[:4] 
                 
             score = format_large_num(s.get('Score', 0))
             wins = s.get('BW', 0)
             draws = s.get('BD', 0)
             fought = s.get('BF', 0)
             losses = fought - wins - draws
             
             wl_ratio = f"{wins}/{losses}/{draws}"
             posture = s.get('Post', 'BAL')[:3].upper()
             casuals = s.get('L', 0)
             l_ship = s.get('L_Ship', 0)
             l_ground = s.get('L_Ground', 0)
             req = format_large_num(s.get('R', 0))
             
             # Colorize Score
             score_color = GREEN if i <= 3 else WHITE
             
             avg_s = s.get('AvgS', 0)
             avg_g = s.get('AvgG', 0)
             flt_display = f"{s.get('F',0):>2}({int(avg_s)})"
             arm_display = f"{s.get('A',0):>2}({int(avg_g)})"
             
             cty_count = s.get('CTY', 0)
             b_total = s.get('B', 0)
             b_avg = b_total / cty_count if cty_count > 0 else 0
             bld_display = f"{b_total:>3}({b_avg:.1f})"
             
             own_count = s.get('OWN', 0)
             con_count = s.get('CON', 0)
             own_cty = s.get('OWN_CTY', 0)
             con_cty = s.get('CON_CTY', 0)
             
             own_avg = own_cty / own_count if own_count > 0 else 0
             con_avg = con_cty / con_count if con_count > 0 else 0
             
             own_display = f"{own_count:>2}({own_avg:.1f})"
             con_display = f"{con_count:>2}({con_avg:.1f})"
             
             wrs = s.get('WRS', 0)
             wrs_color = RED if wrs > 0 else DIM
             
             entry = f"     {i:<3} {BOLD}{code:<4}{RESET} {score_color}{score:>7}{RESET}  {s.get('S',0):>3} {own_display:>7} {con_display:>7} {cty_count:>3} {bld_display:>9} {s.get('SB',0):>3} {flt_display:>7} {arm_display:>7} {req:>8} {s.get('T',0):>3} {wrs_color}{wrs:>3}{RESET} {wl_ratio:>8} {RED}{l_ship:>4} {l_ground:>4}{RESET} {posture:>4}"
             buffer.append(entry)

    def _render_boxed_summary(self, stats: dict, buffer: list):
        """Renders a detailed boxed galactic summary."""
        turn = stats.get('turn', 0)
        uncol = stats.get('GLOBAL_NEUTRAL', 0)
        planets = stats.get('GLOBAL_PLANETS', 1)
        contested = stats.get('GLOBAL_CONTESTED_PLANETS', 0)
        col_pct = (1 - (uncol / planets)) * 100 if planets > 0 else 0
        
        battles = stats.get('GLOBAL_BATTLES', 0)
        s_battles = stats.get('GLOBAL_SPACE_BATTLES', 0)
        g_battles = stats.get('GLOBAL_GROUND_BATTLES', 0)
        
        casualties_s = stats.get('GLOBAL_CASUALTIES_SHIP', 0)
        casualties_g = stats.get('GLOBAL_CASUALTIES_GROUND', 0)
        casualties_total = casualties_s + casualties_g
        
        total_casualties_s = stats.get('GLOBAL_TOTAL_CASUALTIES_SHIP', 0)
        total_casualties_g = stats.get('GLOBAL_TOTAL_CASUALTIES_GROUND', 0)
        total_casualties_all = total_casualties_s + total_casualties_g
        
        req = stats.get('GLOBAL_REQUISITION', 0)
        # Assuming flow is change in requisition? For now we'll just show total
        tech_avg = stats.get('GLOBAL_TECH_AVG', 0)
        breakthroughs = stats.get('GLOBAL_TECH_BREAKTHROUGHS', 0)
        
        perf_time = stats.get('GLOBAL_PERF_TURN_TIME', 0)
        perf_tps = stats.get('GLOBAL_PERF_TPS', 0)
        alerts = stats.get('GLOBAL_ALERT_COUNTS', {"CRITICAL": 0, "WARNING": 0, "INFO": 0})
        
        width = 76
        title_raw = " GLOBAL GALACTIC SUMMARY "
        side_border = (width - len(title_raw)) // 2
        
        buffer.append(f"     ╔{'═' * side_border}{BOLD} GLOBAL GALACTIC SUMMARY {RESET}{'═' * (width - side_border - len(title_raw))}╗")
        
        # Line 1: Planets
        # Planets: 300 total | 0 ntl (0%) | 16 cont (5%) | 284 held (95%)
        ntl_pct = (uncol / planets) * 100 if planets > 0 else 0
        cont_pct = (contested / planets) * 100 if planets > 0 else 0
        held_count = max(0, planets - uncol - contested)
        held_pct = (held_count / planets) * 100 if planets > 0 else 0
        
        line1 = f"  {BOLD}Planets:{RESET} {WHITE}{planets}{RESET} total | {CYAN}{uncol}{RESET} ntl ({int(ntl_pct)}%) | {YELLOW}{contested}{RESET} cont ({int(cont_pct)}%) | {GREEN}{held_count}{RESET} held ({int(held_pct)}%)"
        buffer.append(f"     ║ {line1}{' ' * (width - self._visual_width(line1) - 1)}║")
        
        # Line 2: Battles
        line2 = f"  {BOLD}Battles:{RESET} {RED}⚔ {battles}{RESET} active | {BLUE}🚀 {s_battles}{RESET} space | {GREEN}🪖 {g_battles}{RESET} ground"
        buffer.append(f"     ║ {line2}{' ' * (width - self._visual_width(line2) - 1)}║")
        
        # Line 3: Losses (Turn vs Total)
        line3 = f"  {BOLD}Turn Losses:{RESET} {RED}💀 {format_large_num(casualties_total)}{RESET} | {BLUE}🚀 {casualties_s}{RESET} ships | {GREEN}🪖 {casualties_g}{RESET} ground"
        buffer.append(f"     ║ {line3}{' ' * (width - self._visual_width(line3) - 1)}║")
        
        line3b = f"  {BOLD}Total Deaths:{RESET} {RED}💀 {format_large_num(total_casualties_all)}{RESET} | {BLUE}🚀 {total_casualties_s}{RESET} ships | {GREEN}🪖 {total_casualties_g}{RESET} ground"
        buffer.append(f"     ║ {line3b}{' ' * (width - self._visual_width(line3b) - 1)}║")

        # Line 3c: Diplomacy
        dip_data = stats.get('GLOBAL_DIPLOMACY', [])
        wars = sum(1 for d in dip_data if d['type'] == 'War')
        allies = sum(1 for d in dip_data if d['type'] == 'Alliance')
        trades = sum(1 for d in dip_data if d['type'] == 'Trade')
        line3c = f"  {BOLD}Diplomacy:{RESET} {RED}� {wars}{RESET} wars | {CYAN}🤝 {allies}{RESET} allies | {GREEN}📦 {trades}{RESET} trade"
        buffer.append(f"     ║ {line3c}{' ' * (width - self._visual_width(line3c) - 1)}║")
        
        # Line 4: Economy / Tech / Flux
        velocity = stats.get('GLOBAL_ECON_VELOCITY', 100.0)
        econ_status = f"{GREEN}Flowing{RESET}" if velocity > 50 else (f"{YELLOW}Stable{RESET}" if velocity > 0 else f"{RED}Stagnant{RESET}")
        tech_pts = int(tech_avg)
        storms = stats.get('GLOBAL_STORMS_BLOCKING', 0)
        line4 = f"  {BOLD}Economy:{RESET} 💰 {econ_status} | {BOLD}Tech:{RESET} 🔬 {CYAN}{tech_pts}{RESET} pts | {BOLD}Flux:{RESET} ⚡ {YELLOW}{storms}{RESET} blocking"
        buffer.append(f"     ║ {line4}{' ' * (width - self._visual_width(line4) - 1)}║")
        
        # Line 5: Latest Critical Alert
        latest_crit = "SYSTEMS NOMINAL"
        raw_alerts = stats.get('GLOBAL_ALERTS', [])
        for a in reversed(raw_alerts):
            if a.get('severity') == 'critical':
                latest_crit = a.get('message', 'UNKNOWN CRITICAL ERROR')
                break
        
        line5 = f"  {RED}![CRIT]{RESET} {DIM}{latest_crit[:width-12]}{RESET}"
        buffer.append(f"     ║ {line5}{' ' * (width - self._visual_width(line5) - 1)}║")
        
        buffer.append(f"     ╚{'═' * width}╝")

    def _render_theater_overlay(self, stats: dict, buffer: list):
        """Displays localized military theater information."""
        buffer.append(f"\n     {BOLD}{CYAN}╔════════ MILITARY THEATER OVERVIEW ════════╗{RESET}")
        
        # Derive theaters from faction data
        theaters_found = False
        for f, s in stats.items():
            if isinstance(s, dict) and "Theaters" in s:
                theaters = s["Theaters"]
                if theaters:
                    theaters_found = True
                    buffer.append(f"     ║ {BOLD}{f:<40}{RESET} ║")
                    for t in theaters:
                        name = t.get("name", "Unknown")
                        goal = t.get("goal", "IDLE")
                        goal_color = YELLOW if "EXPAND" in goal else (RED if "OFFENSIVE" in goal else GREEN)
                        buffer.append(f"     ║   > {name:<20} | {goal_color}{goal:<13}{RESET} ║")
        
        if not theaters_found:
             buffer.append(f"     ║ {DIM}No active theater data available.{RESET}          ║")
             
        buffer.append(f"     {BOLD}{CYAN}╚═══════════════════════════════════════════╝{RESET}")

    def _render_victory_overlay(self, stats: dict, buffer: list):
        """Displays progress towards victory conditions with premium styling."""
        turn = stats.get('turn', 0)
        victory = stats.get('GLOBAL_VICTORY', {})
        
        width = 74
        title = f" GALACTIC VICTORY PROGRESS - Turn {turn} "
        side_border = (width - len(title)) // 2
        
        buffer.append(f"\n     {YELLOW}╔{'═' * side_border}{BOLD}{title}{RESET}{YELLOW}{'═' * (width - side_border - len(title))}╗{RESET}")
        
        if not victory:
            buffer.append(f"     ║ {DIM}Calculating progress...{RESET}{' ' * (width - 24)}║")
        else:
            # Sort by progress desc
            sorted_vic = sorted(victory.items(), key=lambda x: x[1], reverse=True)
            
            for f_name, pct in sorted_vic:
                # Clean Tag Logic: Use Abbreviation [Instance]
                parts = f_name.rsplit(' ', 1)
                base = parts[0]
                instance = parts[1] if len(parts) > 1 and parts[1].isdigit() else ""
                abbr = FACTION_ABBREVIATIONS.get(base, base[:18]).strip()
                tag = f"{abbr} [{instance}]" if instance else abbr
                
                # Bar color: Green if high, Yellow if mid, Dim if low
                if pct > 60: bar_color = GREEN
                elif pct > 30: bar_color = YELLOW
                else: bar_color = DIM
                
                # Dynamic Bar Length
                bar_len = 35
                bar = self._make_bar(pct, 100, length=bar_len)
                
                # Construct Line with proper spacing
                tag_display = f"{WHITE}{tag:<25}{RESET}"
                pct_display = f"{BOLD}{pct:>5.1f}%{RESET}"
                
                content = f" {tag_display} ║ {bar_color}{bar}{RESET} ║ {pct_display} "
                raw_len = len(self._strip_ansi(content))
                padding = width - raw_len
                
                buffer.append(f"     ║{content}{' ' * padding}║")
                
        buffer.append(f"     {YELLOW}╚{'═' * width}╝{RESET}")
        buffer.append(f"     {DIM} Target: Control 75% of Galaxy Systems{RESET}")
        buffer.append(f"     {DIM} (Press 'v' to close, 'q' to quit){RESET}")

    def _render_alerts_overlay(self, stats: dict, buffer: list):
        """Displays recent critical and warning alerts."""
        alerts = stats.get('GLOBAL_ALERTS', [])
        buffer.append(f"\n     {BOLD}{RED}╔════════════ CRITICAL ALERT HISTORY ════════════╗{RESET}")
        
        if not alerts:
             buffer.append(f"     ║ {DIM}No alerts detected in current log window.{RESET}       ║")
        else:
            # Show last 10 alerts
            for a in alerts[-10:]:
                sev = a.get('severity', 'info').upper()
                sev_color = RED if sev == "CRITICAL" else (YELLOW if sev == "WARNING" else WHITE)
                msg = a.get('message', 'No message')
                # Truncate message
                msg = (msg[:45] + '..') if len(msg) > 45 else msg
                buffer.append(f"     ║ {sev_color}{sev:<8}{RESET} | {msg:<45} ║")
                
        buffer.append(f"     {BOLD}{RED}╚════════════════════════════════════════════════╝{RESET}")

    def _render_map_overlay(self, stats: dict, buffer: list):
        """Displays a premium Tactical HUD Galaxy Map."""
        map_data = stats.get('GLOBAL_MAP_DATA', [])
        width = 72
        title = " GALAXY TACTICAL SCANNER "
        side_border = (width - len(title)) // 2
        
        buffer.append(f"\n     {BLUE}╔═══════════════════════[ {BOLD}{WHITE}SDR-9 SCANNER{RESET}{BLUE} ]═══════════════════════╗{RESET}")
        buffer.append(f"     {BLUE}║{RESET}  {DIM}Y-AXIS{RESET}{' ' * (width-10)}{BLUE}║{RESET}")
        
        if not map_data:
             buffer.append(f"     {BLUE}║{RESET}      {RED}ERR: NO SIGNAL IN SECTOR{RESET}{' ' * (width-30)}{BLUE}║{RESET}")
        else:
            # grid settings - more compact for better density
            grid_w, grid_h = 56, 14
            grid = [[f"{DIM}·{RESET}" for _ in range(grid_w)] for _ in range(grid_h)]
            
            # Normalize coordinates
            xs = [s['x'] for s in map_data]
            ys = [s['y'] for s in map_data]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            
            range_x = max(1, max_x - min_x)
            range_y = max(1, max_y - min_y)
            
            for s in map_data:
                nx = int(((s['x'] - min_x) / range_x) * (grid_w - 1))
                ny = int(((s['y'] - min_y) / range_y) * (grid_h - 1))
                
                owner = s.get('owner', 'Neutral')
                if owner == 'Neutral':
                    grid[ny][nx] = f"{WHITE}●{RESET}"
                else:
                    # Get color index for owner
                    raw_faction = owner.rsplit(' ', 1)[0]
                    f_idx = list(FACTION_ABBREVIATIONS.keys()).index(raw_faction) if raw_faction in FACTION_ABBREVIATIONS else (hash(raw_faction) % 6)
                    color = self._get_group_color(f_idx % 6)
                    char = owner[0].upper()
                    grid[ny][nx] = f"{color}{BOLD}{char}{RESET}"
                
            # Render grid with frame
            for i, row in enumerate(grid):
                y_lbl = f"{DIM}{14-i:2}{RESET}" if i % 4 == 0 else "  "
                content = "".join(row)
                buffer.append(f"     {BLUE}║{RESET} {y_lbl} │ {content} │    {BLUE}║{RESET}")
                
            # X-Axis
            x_ax = "─" * grid_w
            buffer.append(f"     {BLUE}║{RESET}    └──{x_ax}──    {BLUE}║{RESET}")
            buffer.append(f"     {BLUE}║{RESET}        {DIM}00   10   20   30   40   54  X-AXIS{RESET}      {BLUE}║{RESET}")

        buffer.append(f"     {BLUE}╚═[ {BOLD}{CYAN}LIVE FEED OK{RESET}{BLUE} ]══════════════════════════════[ {BOLD}{WHITE}m:CLOSE{RESET}{BLUE} ]═╝{RESET}")
        
        # Legend section
        legend = f"{WHITE}●{RESET} Neutral | {BOLD}{GREEN}H{RESET}eld | {BOLD}{YELLOW}C{RESET}apital | {DIM}·{RESET} Deep Space"
        buffer.append(f"     {DIM}SENSORS:{RESET} {legend}")



    def _export_session_data(self):
        """Exports current statistics to a JSON/CSV file."""
        import json
        import os
        from datetime import datetime
        
        if not self.last_progress_data: return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = "reports/dashboard_exports"
        if not os.path.exists(export_dir): os.makedirs(export_dir)
        
        filepath = os.path.join(export_dir, f"stats_export_{timestamp}.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(self.last_progress_data, f, indent=4)
            self.last_export_status = f"Exported to {os.path.basename(filepath)}"
            self.last_export_time = time.time()
        except Exception as e:
            self.last_export_status = f"Export failed: {e}"

    def _strip_ansi(self, text: str) -> str:
        """Removes ANSI escape sequences for length calculation."""
        import re
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def _visual_width(self, text: str) -> int:
        """Calculates visual column width, accounting for double-width characters."""
        stripped = self._strip_ansi(text)
        width = 0
        for char in stripped:
            # Simple heuristic for double-width emojis/icons
            if ord(char) > 0xFFFF or char in "💀🚀🪖💰🔬⚡⚔●HCP":
                width += 2
            else:
                width += 1
        return width

    def _make_bar(self, value, total, length=20):
        if total == 0: total = 1
        pct = min(1.0, value / total)
        filled_len = int(length * pct)
        
        # Gradient colors for bar? Maybe too complex for now, stick to simple green/white
        bar_color = GREEN
        empty_color = DIM + WHITE
        
        # Block characters
        bar_str = "█" * filled_len
        empty_str = "░" * (length - filled_len)
        
        return f"{bar_color}{bar_str}{empty_str}{RESET}"

    def _identify_alliance_groups(self, diplomacy_list: List[Dict]) -> List[List[str]]:
        """
        Identifies connected components of allied factions.
        """
        adj = {}
        all_factions = set()
        
        # Build graph
        for entry in diplomacy_list:
            if entry['type'] == 'Alliance':
                pair = entry['members']
                u, v = pair[0], pair[1]
                adj.setdefault(u, []).append(v)
                adj.setdefault(v, []).append(u)
                all_factions.add(u)
                all_factions.add(v)
        
        visited = set()
        groups = []
        
        for faction in all_factions:
            if faction not in visited:
                # BFS
                component = []
                queue = [faction]
                visited.add(faction)
                while queue:
                    curr = queue.pop(0)
                    component.append(curr)
                    for neighbor in adj.get(curr, []):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)
                groups.append(sorted(component))
                
        # Sort groups by size (desc) then name to be deterministic
        groups.sort(key=lambda x: (-len(x), x[0]))
        return groups

    def _get_group_color(self, index: int) -> str:
        """Returns a distinct color for an alliance group index."""
        colors = [CYAN, YELLOW, MAGENTA, BLUE, WHITE]
        return colors[index % len(colors)]

def format_large_num(n):
    """Formats large numbers with K/M/B suffixes."""
    try:
        n = float(n)
        if n >= 1_000_000_000: return f"{n/1_000_000_000:.1f}B"
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000: return f"{n/1_000:.1f}K"
        return str(int(n))
    except (ValueError, TypeError):
        return str(n)

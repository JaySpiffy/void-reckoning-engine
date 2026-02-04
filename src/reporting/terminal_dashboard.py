
import os
import sys
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
        self.show_detailed = True
        self.show_galactic_summary = True
        self.show_diplomacy = True
        self.show_help = False
        self.quit_requested = False
        self.filter_buffer = ""
        self.is_filtering = False
        self.last_progress_data = {}
        self.last_universe_configs = []


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
            self.show_detailed = not self.show_detailed
        elif key == 's':
            self.show_galactic_summary = not self.show_galactic_summary
        elif key == 'h':
            self.show_help = not self.show_help
        elif key == 'f':
            self.is_filtering = True
            self.filter_buffer = ""
        elif key == 'y':
            self.show_diplomacy = not self.show_diplomacy
        elif key == 'r':
            # Force refresh is conceptually simple - we just don't skip the next render
            pass
        elif key.isdigit():
            # Quick filter by index (simplified: just sets a filter for testing)
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
        
        # Fancy Header
        buffer.append(f"{BOLD}{CYAN}╔{'═'*78}╗{RESET}")
        buffer.append(f"{BOLD}{CYAN}║ {WHITE}MULTI-UNIVERSE SIMULATION DASHBOARD{' '*43}{CYAN}║{RESET}")
        buffer.append(f"{BOLD}{CYAN}╚{'═'*78}╝{RESET}")
        
        # Hardware Info Line
        hw_info = f"{DIM}Output: {output_dir}{RESET}"
        selected_gpu = gpu_utils.get_selected_gpu()
        if selected_gpu:
            hw_info += f" | {BOLD}{GREEN}GPU: {selected_gpu.model.value} (Device {selected_gpu.device_id}){RESET}"
        else:
            hw_gpus = gpu_utils.get_hardware_gpu_info()
            if hw_gpus:
                hw_info += f" | {BOLD}{YELLOW}GPU: {hw_gpus[0]['name']} (Hardware Only){RESET}"
            else:
                hw_info += f" | {DIM}GPU: CPU OnlyFallback{RESET}"
        
        buffer.append(hw_info)
        buffer.append(f"{CYAN}{'─' * 80}{RESET}")
        
        # Shortcuts Line
        status_line = f" {BOLD}Controls:{RESET} {DIM}(q)uit (p)ause (d)etailed (s)ummary (y)diplomacy (f)ilter (h)elp{RESET}"
        if self.is_paused:
            status_line += f" | {BOLD}{BLACK}{ON_YELLOW} PAUSED {RESET}"
        if self.faction_filter:
            status_line += f" | {BOLD}{YELLOW}Filter: {self.faction_filter}{RESET}"
        buffer.append(status_line)
        buffer.append(f"{CYAN}{'─' * 80}{RESET}")

        if self.show_help:
            self._render_help_overlay(buffer)
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
                
                buffer.append(f"  Run {rid:03d}: {bar} {DIM}Turn{RESET} {turn_num:>3} | {status_color}{status}{RESET}")

                self._render_faction_summary(rdata.get("stats", {}), buffer, is_final=False)

            if len(active) > 5:
                buffer.append(f"  {DIM}... {len(active)-5} more active ...{RESET}")
                
            # Show latest done (if no active)
            if done and not active:
                last_rid, last_rdata = done[-1]
                buffer.append(f"  Run {last_rid:03d}: {BOLD}{GREEN}[DONE]{RESET} {last_rdata['status']}")
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
        buffer.append(f"   ║ {YELLOW}d{RESET} : Toggle Detailed Faction   ║")
        buffer.append(f"   ║ {YELLOW}s{RESET} : Toggle Global Summary     ║")
        buffer.append(f"   ║ {YELLOW}y{RESET} : Toggle Galactic Diplomacy ║")
        buffer.append(f"   ║ {YELLOW}f{RESET} : Filter by Faction Tag     ║")
        buffer.append(f"   ║ {YELLOW}r{RESET} : Force Full Refresh        ║")
        buffer.append(f"   ║ {YELLOW}h{RESET} : Toggle Help Overlay       ║")
        buffer.append(f"   ║ {YELLOW}1-9{RESET} : Quick Filter Index      ║")
        buffer.append(f"   {BOLD}{WHITE}╚═══════════════════════════════╝{RESET}")


    def _render_faction_summary(self, stats: dict, buffer: list, is_final: bool = False):
        """Helper for rendering faction summary in dashboard. Appends to buffer."""
        if not stats:
            return
            
        uncol = stats.get('GLOBAL_NEUTRAL', 0)
        battles = stats.get('GLOBAL_BATTLES', 0)
        storms = stats.get('GLOBAL_STORMS', 0)
        
        if self.show_galactic_summary:
            # Global Stats Line
            s_battles = stats.get('GLOBAL_SPACE_BATTLES', 0)
            g_battles = stats.get('GLOBAL_GROUND_BATTLES', 0)
            
            storm_display = f"{YELLOW}⚡ {storms}{RESET}" if storms > 0 else f"{DIM}0{RESET}"
            buffer.append(f"     {DIM}Global Stats:{RESET} Uncolonized: {WHITE}{uncol}{RESET} | Battles: {RED}⚔ {battles}{RESET} (🚀{s_battles} 🪖{g_battles}) | Flux Storms: {storm_display}")

        
        # Phase 5: Theater Overview (Top Faction)
        # The dashboard receives pre-processed stats, so we need to extract theater info from there.
        # Assuming 'stats' might contain a 'GLOBAL_THEATERS' key or similar, or we derive it.
        # For now, we'll simulate based on the strongest faction from the stats.
        
        # Find strongest faction by score to show their theater breakdown
        # Display Diplomacy (Alliances & Trade)
        diplomacy = stats.get('GLOBAL_DIPLOMACY', [])
        if diplomacy and self.show_diplomacy:
            buffer.append(f"     {MAGENTA}[GALACTIC DIPLOMACY]{RESET}")
            
            # 1. Identify Alliance Groups
            alliance_groups = self._identify_alliance_groups(diplomacy)
            
            # Map faction -> group_index for coloring
            faction_to_group = {}
            for idx, group in enumerate(alliance_groups):
                for member in group:
                    faction_to_group[member] = idx

            # Priorities: War > Alliance > Vassal > Trade
            def get_dip_prio(d):
                t = d['type']
                if t == 'War': return 0
                if t == 'Alliance': return 1
                if t == 'Vassal': return 2
                return 3
            diplomacy.sort(key=get_dip_prio)
            
            formatted_entries = []
            for entry in diplomacy:
                pair = entry['members']
                n1, n2 = pair[0], pair[1]
                
                # Use Standard Abbreviations with Instance support
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
                    # Use Group Color if available
                    g_idx = faction_to_group.get(n1)
                    # specific check: both must be in same group (they should be if logic holds)
                    if g_idx is not None and g_idx == faction_to_group.get(n2):
                         type_color = self._get_group_color(g_idx)
                    else:
                         type_color = GREEN
                    icon = "🤝"
                elif t_type == 'Vassal':
                    type_color = Cyan
                    icon = "👑"
                else:
                    type_color = BLUE
                    icon = "💰"
                
                # Compact Format: [ICON] ABC-XYZ
                formatted_entries.append(f"{type_color}{icon} {n1_s}-{n2_s}{RESET}")

            # Render in columns (4 per line to maximize density)
            cols = 4
            for i in range(0, len(formatted_entries), cols):
                row = formatted_entries[i:i+cols]
                buffer.append("     " + "   ".join(row))
                
            # Render Explicit Alliance Blocs if any exist
            if alliance_groups:
                 buffer.append(f"     {DIM}--- ALLIANCE BLOCS ---{RESET}")
                 for idx, group in enumerate(alliance_groups):
                      if len(group) < 2: continue # Should not happen for valid alliances
                      
                      color = self._get_group_color(idx)
                      # Format names
                      names = [f"{n[:3].upper()}" for n in group]
                      names_str = ", ".join(names)
                      buffer.append(f"     {color}Bloc {idx+1}: [{names_str}]{RESET}")

        else:
             buffer.append(f"     {DIM}[DIPLOMACY] No active treaties.{RESET}")

        header_text = "FINAL FACTION STATISTICS" if is_final else "TOP FACTION STATISTICS"
        header_color = MAGENTA if is_final else BLUE
        
        if self.show_detailed:
            buffer.append(f"     {header_color}{'-'*3} {header_text} {'-'*3}{RESET}")
            self._print_faction_stats(stats, buffer)
            if not is_final:
                buffer.append("") # Spacer
        elif not is_final:
             buffer.append(f"     {DIM}({header_text} HIDDEN - press 'd' to show){RESET}")

    def _print_faction_stats(self, stats: dict, buffer: list):
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
        
        # Headers
        buffer.append(f"     {DIM}{'#':<3} {'TAG':<4} {'SCORE':>7}  {'SYS':>3} {'OWN(A)':>7} {'CON(A)':>7} {'CTY':>3} {'B(AVG)':>9} {'SB':>3} {'F(AVG)':>7} {'A(AVG)':>7} {'REQ':>8} {'T':>3} {'W/L/D':>8} {'L(S)':>4} {'L(G)':>4} {'POST':>4}{RESET}")

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
             
             entry = f"     {i:<3} {BOLD}{code:<4}{RESET} {score_color}{score:>7}{RESET}  {s.get('S',0):>3} {own_display:>7} {con_display:>7} {cty_count:>3} {bld_display:>9} {s.get('SB',0):>3} {flt_display:>7} {arm_display:>7} {req:>8} {s.get('T',0):>3} {wl_ratio:>8} {RED}{l_ship:>4} {l_ground:>4}{RESET} {posture:>4}"
             buffer.append(entry)

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

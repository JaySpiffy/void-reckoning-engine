
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, List
from src.core.constants import FACTION_ABBREVIATIONS
from src.core import gpu_utils

from .constants import *
from .renderer import DashboardRenderer
from .input_handler import TUIInputHandler
from src.reporting.services.causal_tracing import CausalTracingService
from src.reporting.indexing import ReportIndexer

class TerminalDashboard:
    """
    Handles terminal-based visualization of multi-universe simulation progress.
    Refactored into a modular structure.
    """
    def __init__(self):
        self.is_paused = False
        self.faction_filter = ""
        self.faction_detail_mode = "SUMMARY" 
        self.show_galactic_summary = True
        self.show_diplomacy = "SUMMARY"
        self.show_help = False
        self.show_theaters = False
        self.show_victory = False
        self.show_alerts = False
        self.show_map = False
        self.show_inspector = False
        self.global_stats_mode = "FULL"
        
        self.indexer = None
        self.causal_service = None
        self.inspector_selection_idx = 0
        self.inspector_trace_chain = []
        self.last_key = "None"
        self.poll_count = 0
        self.key_count = 0
        
        self.quit_requested = False
        self.filter_buffer = ""
        self.is_filtering = False
        self.last_progress_data = {}
        self.last_universe_configs = []
        self.trend_data = {} 
        self.global_trend_data = {} 
        self.last_export_status = ""
        self.last_export_time = 0
        self.session_start_time = time.time()
        
        # God Mode State
        self.show_god_mode = False
        self.god_mode_selection = 0
        self.command_queues = {} # Stores reference to universe queues

    def set_command_queues(self, queues):
        self.command_queues = queues

    def trigger_simulation_pause(self):
        """Sends PAUSE/RESUME command to all universes."""
        # Simple toggle logic based on internal state tracking?
        # Since we don't know the exact worker state, we rely on the user knowing.
        # But wait, we can track if we sent a pause.
        self.sim_paused_state = getattr(self, 'sim_paused_state', False)
        self.sim_paused_state = not self.sim_paused_state
        
        cmd = "PAUSE" if self.sim_paused_state else "RESUME"
        self._broadcast_command({"action": cmd})

    def _broadcast_command(self, cmd_dict):
        """Helper to send command to all active universes."""
        if not self.command_queues: return
        for uname, qs in self.command_queues.items():
            if 'incoming' in qs:
                qs['incoming'].put(cmd_dict)

    def handle_input(self, key: str | None):
        """Delegates input handling to the modular handler."""
        self.poll_count += 1
        if key:
            self.last_key = key
            self.key_count += 1
        TUIInputHandler.handle_input(self, key)

    def render(self, output_dir: str, progress_data: Dict[str, Any], universe_configs: List[Dict[str, Any]]):
        """Orchestrates the rendering process."""
        # Initialize indexer and causal service if not already done
        if not self.indexer:
            db_path = os.path.join(output_dir, "index.db")
            if os.path.exists(db_path):
                self.indexer = ReportIndexer(db_path)
                self.causal_service = CausalTracingService(self.indexer)

        if not self.is_paused:
            self.last_progress_data = progress_data
            self.last_universe_configs = universe_configs

        data_to_render = self.last_progress_data if self.is_paused else progress_data
        configs_to_render = self.last_universe_configs if self.is_paused else universe_configs

        buffer = []
        # Use os.system for reliable clearing on Windows
        os.system('cls' if os.name == 'nt' else 'clear')
        # buffer.append("\033[2J\033[H") # Unreliable on some Windows terminals

        # Header
        gpu_info = gpu_utils.get_selected_gpu()
        gpu_str = f"{gpu_info.model.value} (Device {gpu_info.device_id})" if gpu_info else "N/A"
        DashboardRenderer.render_header(buffer, "MULTI-UNIVERSE SIMULATION DASHBOARD", output_dir, gpu_str)
        
        # Data derivation
        current_turn = 0
        total_turns = 100
        if configs_to_render and "game_config" in configs_to_render[0]:
            total_turns = configs_to_render[0]["game_config"].get("campaign", {}).get("turns", 100)
        
        current_stats = {}
        if data_to_render and configs_to_render:
            first_universe_name = configs_to_render[0]["universe_name"]
            runs = data_to_render.get(first_universe_name, {}).get("runs", {})
            run_data = runs.get("001") or runs.get(1)
            if not run_data and runs:
                first_id = next(iter(runs))
                run_data = runs[first_id]
            if run_data:
                current_stats = run_data.get("stats", {})
                current_turn = run_data.get('turn', 0)

        # --- Footer Section ---
        buffer.append(f"{CYAN}{'━' * 80}{RESET}")
        
        # 1. Performance & Status Row
        elapsed_total = int(time.time() - self.session_start_time)
        el_m, el_s = divmod(elapsed_total, 60)
        perf_tps = current_stats.get('GLOBAL_PERF_TPS', 0)
        perf_time = current_stats.get('GLOBAL_PERF_TURN_TIME', 0)
        mem = current_stats.get('GLOBAL_PERF_MEMORY', 0)
        mem_trend = self._get_trend_icon('GLOBAL_PERF_MEMORY')
        
        turns_left = max(0, total_turns - current_turn)
        eta_s_total = int(turns_left * perf_time)
        eta_m, eta_s = divmod(eta_s_total, 60)
        
        perf_line = f" {BOLD}ELAPSED:{RESET} {el_m}m {el_s}s | {BOLD}PACE:{RESET} {perf_time:.2f}s/T | {BOLD}TPS:{RESET} {CYAN}{perf_tps:.2f}{RESET} | {BOLD}MEM:{RESET} {MAGENTA}{int(mem)}MB {mem_trend}{RESET} | {YELLOW}ETA: {eta_m}m {eta_s}s{RESET}"
        
        if self.is_paused:
            perf_line += f" | {BOLD}{BLACK}{ON_YELLOW} PAUSED {RESET}"
        if self.faction_filter:
            perf_line += f" | {BOLD}{YELLOW}FILTER: {self.faction_filter}{RESET}"
        
        buffer.append(perf_line)
        
        # 2. Controls Row (Clean Box-style)
        ctrl_l1 = f" {BOLD}NAV:{RESET} {DIM}(q)uit (p)ause (h)elp (m)ap (i)nspect (e)xport (G)odMode (Shift+P)auseSim{RESET}"
        ctrl_l2 = f" {BOLD}VIEW:{RESET} {DIM}(d)iplomacy (y)details (s)ummary (f)ilter (v)ictory (a)lerts{RESET}"
        
        debug_info = f" {DIM}Polls:{self.poll_count} Keys:{self.key_count} Last:{CYAN}{self.last_key}{RESET}"
        
        buffer.append(ctrl_l1)
        buffer.append(ctrl_l2 + debug_info.rjust(80 - visual_width(ctrl_l2)))
        buffer.append(f"{CYAN}{'━' * 80}{RESET}")

        # View Overlays
        if self.show_help:
            DashboardRenderer.render_help_overlay(buffer)
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return

        if self.show_alerts:
            DashboardRenderer.render_alerts_overlay(current_stats, buffer)
        if self.show_victory:
            DashboardRenderer.render_victory_overlay(current_stats, buffer)
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return
        if self.show_map:
            DashboardRenderer.render_map_overlay(current_stats, buffer)
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return

        if self.show_inspector:
            self._update_inspector_state(current_stats, configs_to_render)
            DashboardRenderer.render_inspector_overlay(
                buffer, 
                current_stats.get('GLOBAL_ALERTS', []), 
                self.inspector_selection_idx, 
                self.inspector_trace_chain
            )
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return
            
        if self.show_god_mode:
            DashboardRenderer.render_god_mode_overlay(buffer, self.god_mode_selection)
            sys.stdout.write("\n".join(buffer) + "\n")
            sys.stdout.flush()
            return

        if self.is_filtering:
            buffer.append(f"\n   {BOLD}{YELLOW}ENTER FACTION TAG TO FILTER:{RESET} {WHITE}{self.filter_buffer}{RESET}_")
            buffer.append(f"   {DIM}(Press Enter to confirm, Esc to cancel){RESET}")

        # Main Content
        import shutil
        term_width, term_height = shutil.get_terminal_size((80, 24))
        max_rows = max(10, term_height - 10) # Reserve space for header/footer
        rows_used = 0
        
        for config in configs_to_render:
            if rows_used >= max_rows:
                 buffer.append(f"  {DIM}... (Output truncated for terminal height) ...{RESET}")
                 break
                 
            name = config["universe_name"]
            data = data_to_render.get(name, {})
            completed = data.get("completed", 0)
            total = config["num_runs"]
            affinity = config.get("processor_affinity", "Auto")
            
            header_color = GREEN if completed == total else YELLOW
            buffer.append(f"\n{BOLD}{header_color}[{name.upper()}] {RESET}- Cores: {affinity}")
            buffer.append(f"  {BOLD}Progress:{RESET} {completed}/{total} Runs Completed")
            
            runs = data.get("runs", {})
            sorted_runs = sorted(runs.items(), key=lambda x: x[0])
            active = [r for r in sorted_runs if "Done" not in r[1]["status"]]
            done = [r for r in sorted_runs if "Done" in r[1]["status"]]
            
            for rid, rdata in active[:5]:
                turn_num = rdata.get("turn", 0)
                max_turns = config["game_config"]["campaign"].get("turns", 100)
                bar = make_bar(turn_num, max_turns)
                status = rdata['status']
                status_color = RED if "Error" in status else (YELLOW if "Waiting" in status else GREEN)
                rid_display = f"{int(rid):03d}" if str(rid).isdigit() else str(rid)[:3]
                buffer.append(f"  Run {rid_display}: {bar} {DIM}Turn{RESET} {turn_num:>3} | {status_color}{status}{RESET}")
                self._render_faction_summary(rdata.get("stats", {}), buffer, is_final=False)
                rows_used += 1 + (12 if self.faction_detail_mode == "SUMMARY" else 2) # approx rows added

            if len(active) > 5:
                buffer.append(f"  {DIM}... {len(active)-5} more active ...{RESET}")
            if done and not active:
                last_rid, last_rdata = done[-1]
                last_rid_display = f"{int(last_rid):03d}" if str(last_rid).isdigit() else str(last_rid)[:3]
                buffer.append(f"  Run {last_rid_display}: {BOLD}{GREEN}[DONE]{RESET} {last_rdata['status']}")
                self._render_faction_summary(last_rdata.get("stats", {}), buffer, is_final=True)
                
        # Consolidate output string
        final_output = "\n".join(buffer) + "\n"
        
        # Write to stdout in one go to minimize flickering
        sys.stdout.write(final_output)
        
        # Critical Error Tracebacks
        for config in universe_configs:
            name = config["universe_name"]
            data = progress_data.get(name, {})
            runs = data.get("runs", {})
            for rid, rdata in runs.items():
                if "Error" in rdata.get("status", "") and "error_trace" in rdata.get("stats", {}):
                    err_trace = rdata["stats"]["error_trace"]
                    print(f"\n{RED}!!! RUN {rid} CRITICAL FAILURE !!!{RESET}")
                    print(f"{DIM}{err_trace}{RESET}")

        sys.stdout.flush()

    def draw(self, progress_map, num_runs, active_workers, total_finished, turns_per_run, output_path="", map_config="", is_done=False, wins=None):
        """Compatibility wrapper for ProgressDashboard.draw signature."""
        if not self.last_universe_configs:
            return
            
        # Reconstruct the expected multi-universe data structure
        # progress_map values are tuples: (turn, status, stats) or similar depending on worker output
        # Worker sends: (run_id, turn, status, stats) -> progress_map[rid] = (turn, status, stats)
        
        runs_dict = {}
        for rid, data_tuple in progress_map.items():
            if isinstance(data_tuple, (list, tuple)) and len(data_tuple) >= 3:
                # unpack
                turn = data_tuple[0]
                status = data_tuple[1]
                raw_payload = data_tuple[2] if len(data_tuple) > 2 else {}
                
                # Check if payload is actually stats dict (vs list from GALAXY_READY)
                stats = raw_payload if isinstance(raw_payload, dict) else {}
                
                runs_dict[rid] = {
                    "turn": turn,
                    "status": status,
                    "stats": stats
                }
            else:
                 # Fallback/Error state
                 runs_dict[rid] = {"turn": 0, "status": "Error (Invalid Data)", "stats": {}}

        universe_name = self.last_universe_configs[0]["universe_name"]
        wrapped_data = {
            universe_name: {
                "runs": runs_dict,
                "completed": total_finished
            }
        }
        self.render(output_path, wrapped_data, self.last_universe_configs)

    def _update_trends(self, stats: dict):
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
        trend = self.global_trend_data.get(key, {}).get("trend", "STABLE")
        if trend == "UP": return f"{GREEN}↑{RESET}"
        if trend == "DOWN": return f"{RED}↓{RESET}"
        return f"{DIM}→{RESET}"

    def _render_faction_summary(self, stats: dict, buffer: list, is_final: bool = False):
        if not stats: return
        self._update_trends(stats)
        
        if self.show_galactic_summary:
            if self.global_stats_mode == "FULL":
                DashboardRenderer.render_boxed_summary(stats, buffer)
            else:
                p = stats.get('GLOBAL_PLANETS', 0)
                n = stats.get('GLOBAL_NEUTRAL', 0)
                b = stats.get('GLOBAL_BATTLES', 0)
                c = stats.get('GLOBAL_CASUALTIES_SHIP', 0) + stats.get('GLOBAL_CASUALTIES_GROUND', 0)
                r = format_large_num(stats.get('GLOBAL_REQUISITION', 0))
                t = stats.get('GLOBAL_PERF_TURN_TIME', 0)
                buffer.append(f"     {BOLD}[Q] Quick:{RESET} P:{p} N:{n} B:{b} C:{c} R:{r} T:{t:.2f}s")

        diplomacy = stats.get('GLOBAL_DIPLOMACY', [])
        if diplomacy and self.show_diplomacy != "OFF":
            wars = sum(1 for d in diplomacy if d['type'] == 'War')
            allies = sum(1 for d in diplomacy if d['type'] == 'Alliance')
            trades = sum(1 for d in diplomacy if d['type'] == 'Trade')
            
            buffer.append(f"     {MAGENTA}[GALACTIC DIPLOMACY] ({self.show_diplomacy}){RESET}")
            if self.show_diplomacy == "SUMMARY":
                buffer.append(f"     {RED}⚔ {wars}{RESET} wars | {CYAN}🤝 {allies}{RESET} alliances | {GREEN}📦 {trades}{RESET} trades")
            
            alliance_groups = self._identify_alliance_groups(diplomacy)
            faction_to_group = {member: idx for idx, group in enumerate(alliance_groups) for member in group}

            if self.show_diplomacy in ["EVERYTHING", "NO_WAR"]:
                dip_to_show = diplomacy
                if self.show_diplomacy == "NO_WAR":
                    dip_to_show = [d for d in diplomacy if d['type'] != 'War']
                
                formatted_entries = []
                for entry in dip_to_show:
                    pair = entry['members']
                    n1, n1_s = pair[0], get_tag_with_instance(pair[0])
                    n2_s = get_tag_with_instance(pair[1])
                    t_type = entry['type']
                    if t_type == 'War': type_color = RED; icon = "⚔"
                    elif t_type == 'Alliance':
                        g_idx = faction_to_group.get(n1)
                        type_color = self._get_group_color(g_idx) if g_idx is not None else GREEN
                        icon = "🤝"
                    elif t_type == 'Vassal': type_color = CYAN; icon = "👑"
                    else: type_color = BLUE; icon = "💰"
                    formatted_entries.append(f"{type_color}{icon} {n1_s}-{n2_s}{RESET}")

                cols = 4
                for i in range(0, len(formatted_entries), cols):
                    buffer.append("     " + "   ".join(formatted_entries[i:i+cols]))
            
            if alliance_groups:
                 buffer.append(f"     {DIM}--- ALLIANCE BLOCS ---{RESET}")
                 for idx, group in enumerate(alliance_groups):
                      if len(group) < 2: continue
                      color = self._get_group_color(idx)
                      names = [f"{n[:3].upper()}" for n in group]
                      buffer.append(f"     {color}Bloc {idx+1}: [{', '.join(names)}]{RESET}")

        header_text = "FINAL FACTION STATISTICS" if is_final else "TOP FACTION STATISTICS"
        header_color = MAGENTA if is_final else BLUE
        
        if self.faction_detail_mode != "HIDDEN":
            limit = 10 if self.faction_detail_mode == "SUMMARY" else None
            buffer.append(f"     {header_color}{'-'*3} {header_text} ({self.faction_detail_mode}) {'-'*3}{RESET}")
            self._print_faction_stats(stats, buffer, limit=limit)
            if not is_final: buffer.append("") 
        elif not is_final:
            buffer.append(f"     {DIM}(FACTION DETAILS HIDDEN - press 'y' to cycle modes){RESET}")

    def _print_faction_stats(self, stats: dict, buffer: list, limit: int | None = None):
        sorted_factions = sorted(stats.items(), key=lambda x: x[1]['Score'] if isinstance(x[1], dict) and 'Score' in x[1] else 0, reverse=True)
        to_display = []
        for f, s in sorted_factions:
            if not isinstance(s, dict) or f.startswith("GLOBAL_"): continue
            if self.faction_filter:
                tag = get_tag_with_instance(f).upper()
                if self.faction_filter not in tag and self.faction_filter not in f.upper(): continue
            to_display.append((f, s))
        
        if limit: to_display = to_display[:limit]
        buffer.append(f"     {DIM}{'#':<3} {'TAG':<4} {'SCORE':>7}  {'SYS':>3} {'OWN(A)':>7} {'CON(A)':>7} {'CTY':>3} {'B(AVG)':>9} {'SB':>3} {'F(AVG)':>7} {'A(AVG)':>7} {'REQ':>8} {'T':>3} {'WRS':>3} {'W/L/D':>8} {'L(S)':>4} {'L(G)':>4} {'POST':>4}{RESET}")

        for i, (faction, s) in enumerate(to_display, 1):
             code = get_tag_with_instance(faction)
             score = format_large_num(s.get('Score', 0))
             wins, draws, fought = s.get('BW', 0), s.get('BD', 0), s.get('BF', 0)
             losses = fought - wins - draws
             wl_ratio = f"{wins}/{losses}/{draws}"
             posture = s.get('Post', 'BAL')[:3].upper()
             l_ship, l_ground = s.get('L_Ship', 0), s.get('L_Ground', 0)
             req = format_large_num(s.get('R', 0))
             score_color = GREEN if i <= 3 else WHITE
             
             flt_display = f"{s.get('F',0):>2}({int(s.get('AvgS', 0))})"
             arm_display = f"{s.get('A',0):>2}({int(s.get('AvgG', 0))})"
             
             cty_count = s.get('CTY', 0)
             b_total = s.get('B', 0)
             b_avg = b_total / cty_count if cty_count > 0 else 0
             bld_display = f"{b_total:>3}({b_avg:.1f})"
             
             own_count, con_count = s.get('OWN', 0), s.get('CON', 0)
             own_avg = s.get('OWN_CTY', 0) / own_count if own_count > 0 else 0
             con_avg = s.get('CON_CTY', 0) / con_count if con_count > 0 else 0
             
             own_display = f"{own_count:>2}({own_avg:.1f})"
             con_display = f"{con_count:>2}({con_avg:.1f})"
             
             wrs = s.get('WRS', 0)
             wrs_color = RED if wrs > 0 else DIM
             
             buffer.append(f"     {i:<3} {BOLD}{code:<4}{RESET} {score_color}{score:>7}{RESET}  {s.get('S',0):>3} {own_display:>7} {con_display:>7} {cty_count:>3} {bld_display:>9} {s.get('SB',0):>3} {flt_display:>7} {arm_display:>7} {req:>8} {s.get('T',0):>3} {wrs_color}{wrs:>3}{RESET} {wl_ratio:>8} {RED}{l_ship:>4} {l_ground:>4}{RESET} {posture:>4}")

    def _export_session_data(self):
        if not self.last_progress_data: return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_dir = "reports/dashboard_exports"
        if not os.path.exists(export_dir): os.makedirs(export_dir)
        filepath = os.path.join(export_dir, f"stats_export_{timestamp}.json")
        try:
            with open(filepath, 'w') as f: json.dump(self.last_progress_data, f, indent=4)
            self.last_export_status = f"Exported to {os.path.basename(filepath)}"
            self.last_export_time = time.time()
        except Exception as e: self.last_export_status = f"Export failed: {e}"

    def _update_inspector_state(self, stats: dict, configs: list):
        if not self.causal_service or not stats:
            return
            
        alerts = stats.get('GLOBAL_ALERTS', [])
        if not alerts:
            return
            
        # Ensure index is within range
        self.inspector_selection_idx = max(0, min(self.inspector_selection_idx, len(alerts) - 1))
        
        # If selection changed or trace not yet fetched, fetch it
        selected_alert = alerts[-(self.inspector_selection_idx + 1)] # Most recent first for selection
        trace_id = selected_alert.get('context', {}).get('span_id')
        
        if trace_id and (not self.inspector_trace_chain or self.inspector_trace_chain[-1].get('context', {}).get('span_id') != trace_id):
            universe = configs[0]["universe_name"]
            # We need to find the run_id. Assuming single run demo or latest run.
            run_id = "001" # Default for demo
            self.inspector_trace_chain = self.causal_service.get_causal_chain(universe, run_id, trace_id)

    def _identify_alliance_groups(self, diplomacy_list: List[Dict]) -> List[List[str]]:
        adj = {}
        all_factions = set()
        for entry in diplomacy_list:
            if entry['type'] == 'Alliance':
                pair = entry['members']
                adj.setdefault(pair[0], []).append(pair[1])
                adj.setdefault(pair[1], []).append(pair[0])
                all_factions.update(pair)
        
        visited = set(); groups = []
        for faction in all_factions:
            if faction not in visited:
                component = []; queue = [faction]; visited.add(faction)
                while queue:
                    curr = queue.pop(0); component.append(curr)
                    for neighbor in adj.get(curr, []):
                        if neighbor not in visited: visited.add(neighbor); queue.append(neighbor)
                groups.append(sorted(component))
        groups.sort(key=lambda x: (-len(x), x[0]))
        return groups

    def _get_group_color(self, index: int) -> str:
        colors = [CYAN, YELLOW, MAGENTA, BLUE, WHITE]
        return colors[index % len(colors)]

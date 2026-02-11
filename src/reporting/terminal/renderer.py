
import os
import sys
from typing import Dict, Any, List
from src.core.constants import FACTION_ABBREVIATIONS
from .constants import *

class DashboardRenderer:
    """
    Handles all ASCII/Rich layout and formatting logic for the Terminal Dashboard.
    """
    @staticmethod
    def render_header(buffer: List[str], title: str, output_dir: str, gpu_str: str):
        buffer.append(f"{CYAN}{'━' * 80}{RESET}")
        buffer.append(f" {BOLD}{WHITE}{title.center(78)}{RESET}")
        buffer.append(f" {DIM}Output: {output_dir} | {GREEN}GPU: {gpu_str}{RESET}")
        buffer.append(f"{CYAN}{'━' * 80}{RESET}")

    @staticmethod
    def render_help_overlay(buffer: List[str]):
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
        buffer.append(f"   ║ {YELLOW}i{RESET} : Toggle Causal Inspector   ║")
        buffer.append(f"   ║ {YELLOW}e{RESET} : Export / Save Screenshot  ║")
        buffer.append(f"   ║ {YELLOW}h{RESET} : Toggle Help Overlay       ║")
        buffer.append(f"   ║ {YELLOW}1-9{RESET} : Quick Filter Index      ║")
        buffer.append(f"   {BOLD}{WHITE}╚═══════════════════════════════╝{RESET}")

    @staticmethod
    def render_boxed_summary(stats: dict, buffer: list):
        """Renders a detailed boxed galactic summary."""
        turn = stats.get('turn', 0)
        uncol = stats.get('GLOBAL_NEUTRAL', 0)
        planets = stats.get('GLOBAL_PLANETS', 1)
        contested = stats.get('GLOBAL_CONTESTED_PLANETS', 0)
        
        ntl_pct = (uncol / planets) * 100 if planets > 0 else 0
        cont_pct = (contested / planets) * 100 if planets > 0 else 0
        held_count = max(0, planets - uncol - contested)
        held_pct = (held_count / planets) * 100 if planets > 0 else 0
        
        battles = stats.get('GLOBAL_BATTLES', 0)
        s_battles = stats.get('GLOBAL_SPACE_BATTLES', 0)
        g_battles = stats.get('GLOBAL_GROUND_BATTLES', 0)
        
        casualties_s = stats.get('GLOBAL_CASUALTIES_SHIP', 0)
        casualties_g = stats.get('GLOBAL_CASUALTIES_GROUND', 0)
        casualties_total = casualties_s + casualties_g
        
        total_casualties_s = stats.get('GLOBAL_TOTAL_CASUALTIES_SHIP', 0)
        total_casualties_g = stats.get('GLOBAL_TOTAL_CASUALTIES_GROUND', 0)
        total_casualties_all = total_casualties_s + total_casualties_g
        
        dip_data = stats.get('GLOBAL_DIPLOMACY', [])
        wars = sum(1 for d in dip_data if d['type'] == 'War')
        allies = sum(1 for d in dip_data if d['type'] == 'Alliance')
        trades = sum(1 for d in dip_data if d['type'] == 'Trade')
        
        velocity = stats.get('GLOBAL_ECON_VELOCITY', 100.0)
        econ_status = f"{GREEN}Flowing{RESET}" if velocity > 50 else (f"{YELLOW}Stable{RESET}" if velocity > 0 else f"{RED}Stagnant{RESET}")
        tech_avg = stats.get('GLOBAL_TECH_AVG', 0)
        tech_pts = int(tech_avg)
        storms = stats.get('GLOBAL_STORMS_BLOCKING', 0)
        
        latest_crit = "SYSTEMS NOMINAL"
        raw_alerts = stats.get('GLOBAL_ALERTS', [])
        for a in reversed(raw_alerts):
            if a.get('severity') == 'critical':
                latest_crit = a.get('message', 'UNKNOWN CRITICAL ERROR')
                break

        width = 74
        title = " GLOBAL GALACTIC SUMMARY "
        side_border = (width - len(title)) // 2
        buffer.append(f"     ╔{'═' * side_border}{BOLD}{WHITE}{title}{RESET}{'═' * (width - side_border - len(title))}╗")
        
        def format_line(content):
            inner_w = width - 4
            v_w = visual_width(content)
            padding = inner_w - v_w
            return f"     ║  {content}{' ' * max(0, padding)}║"

        buffer.append(format_line(f"{BOLD}Planets:{RESET} {WHITE}{planets}{RESET} total | {CYAN}{uncol}{RESET} ntl ({int(ntl_pct)}%) | {YELLOW}{contested}{RESET} cont ({int(cont_pct)}%) | {GREEN}{held_count}{RESET} held ({int(held_pct)}%)"))
        buffer.append(format_line(f"{BOLD}Battles:{RESET} {RED}⚔ {battles}{RESET} active | {BLUE}🚀 {s_battles}{RESET} space | {GREEN}🪖 {g_battles}{RESET} ground"))
        buffer.append(format_line(f"{BOLD}Turn Losses:{RESET} {RED}💀 {format_large_num(casualties_total)}{RESET} | {BLUE}🚀 {casualties_s}{RESET} ships | {GREEN}🪖 {casualties_g}{RESET} ground"))
        buffer.append(format_line(f"{BOLD}Total Deaths:{RESET} {RED}💀 {format_large_num(total_casualties_all)}{RESET} | {BLUE}🚀 {total_casualties_s}{RESET} ships | {GREEN}🪖 {total_casualties_g}{RESET} ground"))
        buffer.append(format_line(f"{BOLD}Diplomacy:{RESET} {RED}⚔ {wars}{RESET} wars | {CYAN}🤝 {allies}{RESET} allies | {GREEN}📦 {trades}{RESET} trade"))
        buffer.append(format_line(f"{BOLD}Economy:{RESET} 💰 {econ_status} | {BOLD}Tech:{RESET} 🔬 {CYAN}{tech_pts}{RESET} pts | {BOLD}Flux:{RESET} ⚡ {YELLOW}{storms}{RESET} blocking"))
        buffer.append(format_line(f"{RED}![CRIT]{RESET} {DIM}{latest_crit[:width-14]}{RESET}"))
        buffer.append(f"     ╚{'═' * (width - 2)}╝")

    @staticmethod
    def render_victory_overlay(stats: dict, buffer: list):
        """Displays progress towards victory conditions."""
        turn = stats.get('turn', 0)
        victory = stats.get('GLOBAL_VICTORY', {})
        
        width = 74
        title = f" GALACTIC VICTORY PROGRESS - Turn {turn} "
        side_border = (width - len(title)) // 2
        
        buffer.append(f"\n     {YELLOW}╔{'═' * side_border}{BOLD}{title}{RESET}{YELLOW}{'═' * (width - side_border - len(title))}╗{RESET}")
        
        if not victory:
            buffer.append(f"     ║ {DIM}Calculating progress...{RESET}{' ' * (width - 24)}║")
        else:
            sorted_vic = sorted(victory.items(), key=lambda x: x[1], reverse=True)
            for f_name, pct in sorted_vic:
                parts = f_name.rsplit(' ', 1)
                base = parts[0]
                instance = parts[1] if len(parts) > 1 and parts[1].isdigit() else ""
                abbr = FACTION_ABBREVIATIONS.get(base, base[:18]).strip()
                tag = f"{abbr} [{instance}]" if instance else abbr
                
                if pct > 60: bar_color = GREEN
                elif pct > 30: bar_color = YELLOW
                else: bar_color = DIM
                
                bar_len = 35
                bar = make_bar(pct, 100, length=bar_len)
                tag_display = f"{WHITE}{tag:<25}{RESET}"
                pct_display = f"{BOLD}{pct:>5.1f}%{RESET}"
                
                content = f" {tag_display} ║ {bar_color}{bar}{RESET} ║ {pct_display} "
                raw_len = len(strip_ansi(content))
                padding = width - raw_len
                buffer.append(f"     ║{content}{' ' * padding}║")
                
        buffer.append(f"     {YELLOW}╚{'═' * width}╝{RESET}")

    @staticmethod
    def render_alerts_overlay(stats: dict, buffer: list):
        """Displays recent critical and warning alerts."""
        alerts = stats.get('GLOBAL_ALERTS', [])
        buffer.append(f"\n     {BOLD}{RED}╔════════════ CRITICAL ALERT HISTORY ════════════╗{RESET}")
        if not alerts:
             buffer.append(f"     ║ {DIM}No alerts detected in current log window.{RESET}       ║")
        else:
            for a in alerts[-10:]:
                sev = a.get('severity', 'info').upper()
                sev_color = RED if sev == "CRITICAL" else (YELLOW if sev == "WARNING" else WHITE)
                msg = a.get('message', 'No message')
                msg = (msg[:45] + '..') if len(msg) > 45 else msg
                buffer.append(f"     ║ {sev_color}{sev:<8}{RESET} | {msg:<45} ║")
        buffer.append(f"     {BOLD}{RED}╚════════════════════════════════════════════════╝{RESET}")

    @staticmethod
    def render_map_overlay(stats: dict, buffer: list):
        """Displays a tactical galaxy map."""
        map_data = stats.get('GLOBAL_MAP_DATA', [])
        width = 72
        buffer.append(f"\n     {BLUE}╔═══════════════════════[ {BOLD}{WHITE}SDR-9 SCANNER{RESET}{BLUE} ]═══════════════════════╗{RESET}")
        buffer.append(f"     {BLUE}║{RESET}  {DIM}Y-AXIS{RESET}{' ' * (width-10)}{BLUE}║{RESET}")
        
        if not map_data:
             buffer.append(f"     {BLUE}║{RESET}      {RED}ERR: NO SIGNAL IN SECTOR{RESET}{' ' * (width-30)}{BLUE}║{RESET}")
        else:
            grid_w, grid_h = 56, 14
            grid = [[f"{DIM}·{RESET}" for _ in range(grid_w)] for _ in range(grid_h)]
            xs = [s['x'] for s in map_data]; ys = [s['y'] for s in map_data]
            min_x, max_x = min(xs), max(xs); min_y, max_y = min(ys), max(ys)
            range_x = max(1, max_x - min_x); range_y = max(1, max_y - min_y)
            
            for s in map_data:
                nx = int(((s['x'] - min_x) / range_x) * (grid_w - 1))
                ny = int(((s['y'] - min_y) / range_y) * (grid_h - 1))
                owner = s.get('owner', 'Neutral')
                if owner == 'Neutral':
                    grid[ny][nx] = f"{WHITE}●{RESET}"
                else:
                    raw_faction = owner.rsplit(' ', 1)[0]
                    f_idx = list(FACTION_ABBREVIATIONS.keys()).index(raw_faction) if raw_faction in FACTION_ABBREVIATIONS else (hash(raw_faction) % 6)
                    # Simple color cycling
                    colors = [CYAN, YELLOW, MAGENTA, BLUE, WHITE, GREEN]
                    color = colors[f_idx % len(colors)]
                    char = owner[0].upper()
                    grid[ny][nx] = f"{color}{BOLD}{char}{RESET}"
                
            for i, row in enumerate(grid):
                y_lbl = f"{DIM}{14-i:2}{RESET}" if i % 4 == 0 else "  "
                content = "".join(row)
                buffer.append(f"     {BLUE}║{RESET} {y_lbl} │ {content} │    {BLUE}║{RESET}")
            
            x_ax = "─" * grid_w
            buffer.append(f"     {BLUE}║{RESET}    └──{x_ax}──    {BLUE}║{RESET}")
            buffer.append(f"     {BLUE}║{RESET}        {DIM}00   10   20   30   40   54  X-AXIS{RESET}      {BLUE}║{RESET}")

        buffer.append(f"     {BLUE}╚═[ {BOLD}{CYAN}LIVE FEED OK{RESET}{BLUE} ]══════════════════════════════[ {BOLD}{WHITE}m:CLOSE{RESET}{BLUE} ]═╝{RESET}")
        legend = f"{WHITE}●{RESET} Neutral | {BOLD}{GREEN}H{RESET}eld | {BOLD}{YELLOW}C{RESET}apital | {DIM}·{RESET} Deep Space"
        buffer.append(f"     {DIM}SENSORS:{RESET} {legend}")
    @staticmethod
    def render_inspector_overlay(buffer: List[str], alerts: List[Dict], selected_idx: int, trace_chain: List[Dict]):
        """Displays the Causal Inspector with event lineage."""
        width = 60
        buffer.append(f"\n     {BOLD}{MAGENTA}╔═══════════════[ CAUSAL INSPECTOR ]═══════════════╗{RESET}")
        
        if not alerts:
            buffer.append(f"     ║ {DIM}No alerts to inspect.{RESET}{' ' * (width - 24)}║")
        else:
            buffer.append(f"     ║ {BOLD}SELECT ALERT TO TRACE:{RESET}{' ' * (width - 24)} ║")
            # Show last 5 alerts for selection
            recent_alerts = alerts[-5:]
            for i, a in enumerate(reversed(recent_alerts)):
                prefix = f"{GREEN} > {RESET}" if i == selected_idx else "   "
                msg = a.get('message', 'No message')[:40]
                buffer.append(f"     ║ {prefix}{i+1}. {msg:<40} {' ' * (width - 47)}║")
        
        buffer.append(f"     {BOLD}{DIM}╟──────────────────[ CAUSAL CHAIN ]──────────────────╢{RESET}")
        
        if not trace_chain:
            buffer.append(f"     ║ {DIM}No trace data available for selection.{RESET}{' ' * (width - 40)}║")
        else:
            # Render ASCII tree for the chain
            for i, event in enumerate(trace_chain):
                indent_str = "  " * min(i, 4) # Limit indent
                connector = "└─ " if i > 0 else "● "
                category = event.get('category', 'EVENT').upper()
                msg = event.get('message', 'No message')[:35]
                
                color = CYAN if i == 0 else (YELLOW if i < len(trace_chain)-1 else RED)
                line = f"{indent_str}{color}{connector}[{category}]{RESET} {msg}"
                raw_len = visual_width(line)
                padding = width - raw_len - 2
                buffer.append(f"     ║ {line}{' ' * padding}║")
                
                if i < len(trace_chain) - 1:
                    pipe_line = f"{indent_str} │"
                    buffer.append(f"     ║ {pipe_line}{' ' * (width - visual_width(pipe_line) - 2)}║")

        buffer.append(f"     {BOLD}{MAGENTA}╚════════════════════════════════════[ i:CLOSE / Esc ]═╝{RESET}")

    @staticmethod
    def render_god_mode_overlay(buffer: List[str], selection_idx: int, configs: List[Dict] = None, faction_idx: int = 0, preset_idx: int = 0):
        """Displays the God Mode Menu."""
        width = 60
        buffer.append(f"\n     {BOLD}{RED}╔═══════════════[ GOD MODE CONTROL ]═══════════════╗{RESET}")
        buffer.append(f"     ║ {DIM}Directly manipulate simulation state.{RESET}{' ' * (width - 36)}║")
        
        # Resolve Dynamic Values
        factions = ["Humanity"]
        if configs and len(configs) > 0:
            cfg = configs[0]
            if "factions" in cfg and cfg["factions"]:
                factions = list(cfg["factions"].keys()) if isinstance(cfg["factions"], dict) else cfg["factions"]
            
        target_faction = factions[faction_idx % len(factions)] if factions else "Humanity"
        
        presets = ["Patrol", "Battlegroup", "Wolfpack", "Armada", "Invasion Force"]
        target_preset = presets[preset_idx % len(presets)]

        options = [
            f"Spawn Fleet ({target_preset}) -> {target_faction}",
            f"Spawn Pirate Raid -> {target_faction}",
            f"Add 100,000 Requisition ({target_faction})",
            "Force Global Peace",
            "Trigger Chaos Incursion"
        ]
        
        for i, opt in enumerate(options):
            prefix = f"{RED} > {RESET}" if i == selection_idx else "   "
            style = BOLD if i == selection_idx else WHITE
            # Truncate if too long
            opt_display = opt[:50]
            buffer.append(f"     ║ {prefix}{style}{i+1}. {opt_display:<50}{RESET}{' ' * (width - 58)}║")
            
        buffer.append(f"     {BOLD}{RED}╟──────────────────────────────────────────────────╢{RESET}")
        buffer.append(f"     ║ {YELLOW}Controls: UP/DOWN select, ENTER execute.{RESET}           ║")
        buffer.append(f"     ║ {YELLOW}< > Cycle Faction | [ ] Cycle Preset{RESET}             ║")
        buffer.append(f"     {BOLD}{RED}╚════════════════════════════════════[ G:CLOSE / Esc ]═╝{RESET}")

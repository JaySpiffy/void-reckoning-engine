
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

        width = 76
        side_border = (width - 25) // 2 # Fixed len for " GLOBAL GALACTIC SUMMARY "
        buffer.append(f"     ╔{'═' * side_border}{BOLD} GLOBAL GALACTIC SUMMARY {RESET}{'═' * (width - side_border - 25)}╗")
        
        line1 = f"  {BOLD}Planets:{RESET} {WHITE}{planets}{RESET} total | {CYAN}{uncol}{RESET} ntl ({int(ntl_pct)}%) | {YELLOW}{contested}{RESET} cont ({int(cont_pct)}%) | {GREEN}{held_count}{RESET} held ({int(held_pct)}%)"
        buffer.append(f"     ║ {line1}{' ' * (width - visual_width(line1) - 1)}║")
        
        line2 = f"  {BOLD}Battles:{RESET} {RED}⚔ {battles}{RESET} active | {BLUE}🚀 {s_battles}{RESET} space | {GREEN}🪖 {g_battles}{RESET} ground"
        buffer.append(f"     ║ {line2}{' ' * (width - visual_width(line2) - 1)}║")
        
        line3 = f"  {BOLD}Turn Losses:{RESET} {RED}💀 {format_large_num(casualties_total)}{RESET} | {BLUE}🚀 {casualties_s}{RESET} ships | {GREEN}🪖 {casualties_g}{RESET} ground"
        buffer.append(f"     ║ {line3}{' ' * (width - visual_width(line3) - 1)}║")
        
        line3b = f"  {BOLD}Total Deaths:{RESET} {RED}💀 {format_large_num(total_casualties_all)}{RESET} | {BLUE}🚀 {total_casualties_s}{RESET} ships | {GREEN}🪖 {total_casualties_g}{RESET} ground"
        buffer.append(f"     ║ {line3b}{' ' * (width - visual_width(line3b) - 1)}║")

        line3c = f"  {BOLD}Diplomacy:{RESET} {RED}⚔ {wars}{RESET} wars | {CYAN}🤝 {allies}{RESET} allies | {GREEN}📦 {trades}{RESET} trade"
        buffer.append(f"     ║ {line3c}{' ' * (width - visual_width(line3c) - 1)}║")
        
        line4 = f"  {BOLD}Economy:{RESET} 💰 {econ_status} | {BOLD}Tech:{RESET} 🔬 {CYAN}{tech_pts}{RESET} pts | {BOLD}Flux:{RESET} ⚡ {YELLOW}{storms}{RESET} blocking"
        buffer.append(f"     ║ {line4}{' ' * (width - visual_width(line4) - 1)}║")
        
        line5 = f"  {RED}![CRIT]{RESET} {DIM}{latest_crit[:width-12]}{RESET}"
        buffer.append(f"     ║ {line5}{' ' * (width - visual_width(line5) - 1)}║")
        
        buffer.append(f"     ╚{'═' * width}╝")

    @staticmethod
    def render_victory_overlay(stats: dict, buffer: list):
        """Displays progress towards domination victory (75% planet control)."""
        turn = stats.get('turn', 0)
        victory = stats.get('GLOBAL_VICTORY', {})
        
        width = 74
        title = f" GALACTIC DOMINATION - Turn {turn} "
        side_border = (width - len(title)) // 2
        
        buffer.append(f"\n     {YELLOW}╔{'═' * side_border}{BOLD}{title}{RESET}{YELLOW}{'═' * (width - side_border - len(title))}╗{RESET}")
        
        # Victory explanation
        legend = f" {DIM}Win Condition: Control 75% of all planets (cities count for contested){RESET}"
        buffer.append(f"     ║{legend}{' ' * (width - len(strip_ansi(legend)))}║")
        buffer.append(f"     ║{'─' * width}║")
        
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
                tag_display = f"{WHITE}{tag:<20}{RESET}"
                pct_display = f"{BOLD}{pct:>5.1f}%{RESET}"
                
                content = f" {tag_display} ║ {bar_color}{bar}{RESET} ║ {pct_display} 🪐"
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

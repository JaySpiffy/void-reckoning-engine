import os
import sys
if os.name == 'nt':
    import msvcrt
else:
    import select
    import termios
    import tty

from .constants import *

class TUIInputHandler:
    """
    Manages keyboard events, menus, and interaction state for the terminal dashboard.
    """
    @staticmethod
    def get_key() -> str | None:
        """Reads a single keypress without blocking."""
        if os.name == 'nt':
            if msvcrt.kbhit():
                try:
                    char = msvcrt.getch()
                    # Handle special keys (arrows, function keys)
                    if char in (b'\x00', b'\xe0'):
                        code = msvcrt.getch()
                        if code == b'H': return "up"
                        if code == b'P': return "down"
                        if code == b'M': return "right"
                        if code == b'K': return "left"
                        return "SPECIAL"
                    return char.decode('utf-8', errors='ignore') # No lower() to preserve Case
                except:
                    return None
            return None
        else:
            # Unix-like non-blocking read
            if select.select([sys.stdin], [], [], 0)[0]:
                c = sys.stdin.read(1)
                if c == '\x1b':
                    sys.stdin.read(2) # skip [A etc
                    return "special" # Lazy unix impl for now
                return c
            return None

    @staticmethod
    def handle_input(dashboard, key: str | None):
        """Processes keyboard input to update dashboard state."""
        if not key:
            return

        if dashboard.is_filtering:
            if key == '\r' or key == '\n':
                dashboard.faction_filter = dashboard.filter_buffer.upper()
                dashboard.filter_buffer = ""
                dashboard.is_filtering = False
            elif key == '\x08' or key == '\x7f': # Backspace
                dashboard.filter_buffer = dashboard.filter_buffer[:-1]
            elif key == '\x1b': # Esc
                dashboard.filter_buffer = ""
                dashboard.is_filtering = False
            else:
                dashboard.filter_buffer += key
            return

        if key == 'q':
            dashboard.quit_requested = True
        elif key == 'p':
            dashboard.is_paused = not dashboard.is_paused
        elif key == 'd':
            # Cycle diplomacy view
            modes = ["OFF", "SUMMARY", "EVERYTHING", "NO_WAR"]
            curr_idx = modes.index(dashboard.show_diplomacy) if dashboard.show_diplomacy in modes else 0
            dashboard.show_diplomacy = modes[(curr_idx + 1) % len(modes)]
        elif key == 'y':
            # Cycle faction details
            modes = ["HIDDEN", "SUMMARY", "EVERYTHING"]
            curr_idx = modes.index(dashboard.faction_detail_mode)
            dashboard.faction_detail_mode = modes[(curr_idx + 1) % len(modes)]
        elif key == '?':
            dashboard.show_help = not dashboard.show_help
        elif key == 'f':
            dashboard.is_filtering = True
            dashboard.filter_buffer = ""
        elif key == 't':
            dashboard.show_theaters = not dashboard.show_theaters
        elif key == 'v':
            dashboard.show_victory = not dashboard.show_victory
        elif key == 'a':
            dashboard.show_alerts = not dashboard.show_alerts
        elif key == 'h' or key == '?':
            dashboard.show_help = not dashboard.show_help
        elif key == 'i':
            dashboard.show_inspector = not dashboard.show_inspector
            if dashboard.show_inspector:
                dashboard.inspector_selection_idx = 0
                dashboard.inspector_trace_chain = []
        elif key == 'm':
            dashboard.show_map = not dashboard.show_map

        elif key == 'G' or key == 'g': # Case insensitive
            dashboard.show_god_mode = not getattr(dashboard, 'show_god_mode', False)
        elif key == 'P': # True Pause (Shift+P)
             dashboard.trigger_simulation_pause()


        
        elif dashboard.show_god_mode:
            # Data Access for cycling limits
            # Try to get faction count from config
            num_factions = 1
            factions_list = ["Humanity"]
            if hasattr(dashboard, 'last_universe_configs') and dashboard.last_universe_configs:
                cfg = dashboard.last_universe_configs[0]
                if "factions" in cfg and cfg["factions"]:
                    factions_list = list(cfg["factions"].keys()) if isinstance(cfg["factions"], dict) else cfg["factions"]
                    num_factions = len(factions_list)

            presets = ["Patrol", "Battlegroup", "Wolfpack", "Armada", "Invasion Force"]
            num_presets = len(presets)

            # Menu Navigation
            if key == 'up':
                 dashboard.god_mode_selection = max(0, dashboard.god_mode_selection - 1)
            elif key == 'down':
                 dashboard.god_mode_selection = min(4, dashboard.god_mode_selection + 1)
            elif key == 'left':
                 dashboard.god_mode_target_faction_idx = (dashboard.god_mode_target_faction_idx - 1) % num_factions
            elif key == 'right':
                 dashboard.god_mode_target_faction_idx = (dashboard.god_mode_target_faction_idx + 1) % num_factions
            elif key == '[':
                 dashboard.god_mode_preset_idx = (dashboard.god_mode_preset_idx - 1) % num_presets
            elif key == ']':
                 dashboard.god_mode_preset_idx = (dashboard.god_mode_preset_idx + 1) % num_presets

            elif key == '\r' or key == '\n':
                 # Execute
                 idx = dashboard.god_mode_selection
                 target_faction = factions_list[dashboard.god_mode_target_faction_idx]
                 target_preset = presets[dashboard.god_mode_preset_idx]
                 
                 cmd = None
                 if idx == 0: 
                     cmd = {"action": "SPAWN_FLEET", "payload": {"faction": target_faction, "system": "Sol", "preset": target_preset}}
                 elif idx == 1: 
                     # Spawn Pirate
                     cmd = {"action": "SPAWN_PIRATE_FLEET", "payload": {"system": "Sol", "target_faction": target_faction}}
                 elif idx == 2: 
                     cmd = {"action": "ADD_RESOURCES", "payload": {"faction": target_faction, "amount": 100000}}
                 elif idx == 3: 
                     cmd = {"action": "FORCE_PEACE", "payload": {}}
                 elif idx == 4:
                     cmd = {"action": "TRIGGER_EVENT", "payload": {"event_type": "chaos_incursion"}}
                 
                 if cmd:
                     dashboard._broadcast_command({"action": "GOD_EXECUTE", "payload": cmd})
                     dashboard.show_god_mode = False # Close on execute
        
        elif key == '\x1b': # Esc
            if dashboard.show_inspector:
                dashboard.show_inspector = False
            elif dashboard.show_god_mode: # Close God Mode
                dashboard.show_god_mode = False
            elif dashboard.show_map:
                dashboard.show_map = False
            elif dashboard.show_help:
                dashboard.show_help = False
        elif key == 'e' or key == 'c':
            dashboard._export_session_data() # Export / Capture
        elif key == 's':
            dashboard.global_stats_mode = "COMPACT" if dashboard.global_stats_mode == "FULL" else "FULL"

        elif key == 'r':
            pass
        elif key.isdigit():
            dashboard.faction_filter = f"INDEX_{key}"

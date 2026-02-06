
from .constants import *

class TUIInputHandler:
    """
    Manages keyboard events, menus, and interaction state for the terminal dashboard.
    """
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
        elif key == 'm':
            dashboard.show_map = not dashboard.show_map
        elif key == 'e' or key == 'c':
            dashboard._export_session_data() # Export / Capture
        elif key == 's':
            dashboard.global_stats_mode = "COMPACT" if dashboard.global_stats_mode == "FULL" else "FULL"
        elif key == 'r':
            pass
        elif key.isdigit():
            dashboard.faction_filter = f"INDEX_{key}"

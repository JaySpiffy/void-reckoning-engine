
import re
from src.core.constants import FACTION_ABBREVIATIONS

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

def strip_ansi(text: str) -> str:
    """Removes ANSI escape sequences for length calculation."""
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def visual_width(text: str) -> int:
    """Calculates visual column width, accounting for double-width characters."""
    stripped = strip_ansi(text)
    width = 0
    for char in stripped:
        # Simple heuristic for double-width emojis/icons
        if ord(char) > 0xFFFF or char in "💀🚀🪖💰🔬⚡⚔●HCP":
            width += 2
        else:
            width += 1
    return width

def make_bar(value, total, length=20):
    if total == 0: total = 1
    pct = min(1.0, value / total)
    filled_len = int(length * pct)
    
    bar_color = GREEN
    empty_color = DIM + WHITE
    
    # Block characters
    bar_str = "█" * filled_len
    empty_str = "░" * (length - filled_len)
    
    return f"{bar_color}{bar_str}{empty_str}{RESET}"

def get_tag_with_instance(name):
    """Derives a 4-char tag from a faction name and optional instance ID."""
    parts = name.rsplit(' ', 1)
    base = parts[0]
    instance = parts[1] if len(parts) > 1 and parts[1].isdigit() else ""
    abbr = FACTION_ABBREVIATIONS.get(base, base[:3].upper())
    return f"{instance}{abbr}"[:4]

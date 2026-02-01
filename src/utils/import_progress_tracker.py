
import time
import sys
from typing import Optional
from datetime import timedelta

try:
    from src.utils.game_logging import GameLogger, LogCategory
except ImportError:
    # Fallback if GameLogger is not available in specific context
    GameLogger = None

class ImportProgressTracker:
    """
    Tracks and displays progress for long-running import operations.
    Supports stages, nested items, and ETA calculation.
    """
    
    def __init__(self, quiet: bool = False, logger=None):
        self.quiet = quiet
        self.logger = logger
        self.current_stage = 0
        self.total_stages = 8
        self.current_stage_name = ""
        self.start_time = time.time()
        self.stage_start_time = 0
        self.stage_items_total = 0
        self.stage_items_processed = 0
        
    def start_stage(self, name: str, total_items: int = 0):
        """Starts a new tracking stage."""
        self.current_stage += 1
        self.current_stage_name = name
        self.stage_items_total = total_items
        self.stage_items_processed = 0
        self.stage_start_time = time.time()
        
        msg = f"[{self.current_stage}/{self.total_stages}] :: {name}..."
        if not self.quiet:
            print(f"\n{msg}")
            
        if self.logger:
            self.logger.log("IMPORT", f"Started stage: {name} (Total items: {total_items})")
            
    def update(self, current: int, message: str = ""):
        """Updates progress within the current stage."""
        self.stage_items_processed = current
        
        if self.quiet:
            return
            
        # simple ASCII progress bar
        # [████████░░] 80% (40/50) Processing units...
        
        if self.stage_items_total > 0:
            percent = min(1.0, current / self.stage_items_total)
            bar_len = 20
            filled = int(bar_len * percent)
            bar = "=" * filled + "-" * (bar_len - filled)
            percent_str = f"{int(percent * 100)}%"
            count_str = f"({current}/{self.stage_items_total})"
        else:
            # Indeterminate
            bar = "-" * 20
            percent_str = "..."
            count_str = f"({current})"
            
        # Clear line and print
        sys.stdout.write(f"\r  [{bar}] {percent_str} {count_str} {message}")
        sys.stdout.flush()
        
    def complete_stage(self, summary: str):
        """Completes the current stage."""
        duration = time.time() - self.stage_start_time
        
        if not self.quiet:
            # Clear any progress bar
            sys.stdout.write(f"\r{' '*80}\r")
            sys.stdout.write(f"  [+] {summary} ({duration:.1f}s)\n")
            sys.stdout.flush()
            
        if self.logger:
            self.logger.log("IMPORT", f"Completed stage: {self.current_stage_name} - {summary} in {duration:.2f}s")
            
    def fail_stage(self, error_message: str):
        """Marks the current stage as failed."""
        duration = time.time() - self.stage_start_time
        
        if not self.quiet:
            sys.stdout.write(f"\r{' '*80}\r")
            sys.stdout.write(f"  [!] FAILED: {error_message} ({duration:.1f}s)\n")
            sys.stdout.flush()
            
        if self.logger:
             self.logger.log("IMPORT", f"Failed stage: {self.current_stage_name} - {error_message}")

    def set_total_stages(self, total: int):
        self.total_stages = total

    def log(self, message: str):
        """General logging output associated with progress."""
        if not self.quiet:
             print(f"  {message}")

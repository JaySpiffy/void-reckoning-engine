
import os
import json
from typing import Dict, List, Any, Optional

from src.utils.format_detector import FormatDetector

class CampaignExtractor:
    """
    Orchestrates the extraction of campaign structures from game files.
    Generates campaign_config.json containing missions, victory conditions, and starting states.
    
    Note: Third-party universe-specific campaign extraction functions (Stellaris, EaW) have been removed.
    To add custom universe campaign extraction, add new methods here.
    """
    
    def __init__(self, game_dir: str, game_format: str = None):
        self.game_dir = game_dir
        self.format = game_format or FormatDetector.detect_game_engine(game_dir)

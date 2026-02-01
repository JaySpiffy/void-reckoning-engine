import os
import json
import pytest
from src.utils.game_logging import GameLogger, LogCategory
from src.combat.combat_tracker import CombatTracker

def test_logger_functionality(tmp_path):
    """Verify detailed logging functionality including JSON structuring and kwargs."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    
    GameLogger.reset_instance()
    logger = GameLogger(log_dir=str(log_dir), console_verbose=False)
    
    # 1. Context & Levels
    logger.context.clear() # Ensure clean state
    logger.info("Info message without context")
    
    # 2. Kwargs Merging
    logger.info("Message with explicit kwarg", run_id="EXPLICIT_ID")
    
    # 3. Performance
    logger.log_performance("calc_path", 45.2, memory_mb=128.5)
    
    # Verify Text Log
    text_log = log_dir / "campaign.log"
    assert text_log.exists(), "campaign.log not created"
            
    # Verify JSON Log
    json_path = log_dir / "campaign.json"
    assert json_path.exists(), "campaign.json not created"
        
    with open(json_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        assert len(lines) >= 3, "Not enough log lines generated"
        
        # Line 0 usually header/init, Line 1 first message
        # Note: GameLogger might write init line first
        
        # Check explicit kwarg (Line 2 or 3 depending on implementation)
        # We'll search for the line with run_id="EXPLICIT_ID"
        explicit_found = False
        default_null_found = False
        perf_found = False
        
        for line in lines:
            try:
                data = json.loads(line)
                if data.get("message") == "Info message without context":
                    # Check default nulls if expected schema has them, 
                    # or ensure unrelated keys aren't polluted
                    if data.get("run_id") is None:
                        default_null_found = True
                        
                if data.get("run_id") == "EXPLICIT_ID":
                    explicit_found = True
                    
                if data.get("category") == "PERFORMANCE" and data.get("performance", {}).get("duration_ms") == 45.2:
                    perf_found = True
            except json.JSONDecodeError:
                continue

        assert default_null_found, "Missing or incorrect default run_id in normal logs"
        assert explicit_found, "Explicit kwarg merging failed"
        assert perf_found, "JSON log content or Performance log failed"

def test_combat_tracker_functionality(tmp_path):
    """Verify CombatTracker JSON output."""
    json_path = tmp_path / "combat_test.json"
    
    tracker = CombatTracker(json_path=str(json_path))
    tracker.start_round(1)
    tracker.log_round_performance(1, {"pathfinding": 12.5, "damage_calc": 3.4})
    tracker.finalize("Imperium", 1, {}, {})
    tracker.save()
    
    assert json_path.exists(), "combat_test.json not created"
        
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert "performance" in data
        assert len(data["performance"]) > 0
        perf_entry = data["performance"][0]
        assert perf_entry["metrics"]["pathfinding"] == 12.5
        assert perf_entry["round"] == 1


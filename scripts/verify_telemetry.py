import sys
import os
import time

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.core.interfaces import IEngine
from src.managers.campaign_manager import CampaignEngine
from src.reporting.telemetry import TelemetryCollector, EventCategory

def verify_telemetry():
    print("--- Verification: Economic Telemetry ---")
    
    # 1. Setup Engine
    engine = CampaignEngine(universe_name="eternal_crusade")
    engine.generate_galaxy(num_systems=5)
    engine.spawn_start_fleets()
    
    # 2. Force Crisis Scenario
    victim = "Zealot_Legions"
    f_mgr = engine.get_faction(victim)
    
    if not f_mgr:
        print(f"[ERROR] Faction {victim} not found!")
        return
        
    print(f"Forcing {victim} into crisis...")
    f_mgr.requisition = 2000  # Low funds, but positive
    f_mgr.income = 100
    f_mgr.upkeep = 600  # Burn rate -500/turn -> 4 turns to zero
    
    # Mock Telemetry
    telemetry_buffer = []
    
    # Monkeypatch EconomyManager to force our values
    original_calc = engine.economy_manager._calculate_economics
    
    def mock_calc_economics(f_name):
        if f_name == victim:
            # Force values for the victim
            return {
                "income": 100, 
                "upkeep": 600, 
                "total_upkeep": 600,
                "margin": 0.16, 
                "active_mode": {"name": "TEST_CRISIS", "budget": {"recruitment": 0, "construction": 0, "research": 0}},
                "income_by_category": {"Tax": 100},
                "military_upkeep": 500,
                "infrastructure_upkeep": 100
            }
        return original_calc(f_name)
        
    engine.economy_manager._calculate_economics = mock_calc_economics
    # Also need to bypass cache or ensure it uses this
    # process_faction_economy uses cache if passed, or calls _calculate_economics if not.
    # But process_economy populates cache!
    # We need to patch precalculate_economics maybe? 
    # Or easier: Patch process_faction_economy to ignore cache for victim?
    # Actually, if I patch _calculate_economics, and ensure cache is empty or ignored...
    # process_economy calls resource_handler.precalculate_economics().
    
    # Better approach: Just patch ResourceHandler.precalculate_economics?
    # Let's just update the cache manually before processing? 
    # process_economy does precalculate then loop.
    # I can't inject between them.
    
    # Let's monkeypatch `process_economy` to inject our data into the cache after precalc.
    original_process_economy = engine.economy_manager.process_economy
    
    def mock_process_economy():
        # Let it run normally-ish? No, simpler:
        # We can't easily wrap the middle.
        # Let's just set the cache ourself and only run process_faction_economy loop manually in our script?
        # NO, process_turn calls process_economy.
        
        # Let's patch `resource_handler.precalculate_economics`!
        real_precalc = engine.economy_manager.resource_handler.precalculate_economics
        def mock_precalc():
            data = real_precalc()
            if victim in data:
                data[victim]["income"] = 100
                data[victim]["upkeep"] = 600
                data[victim]["total_upkeep"] = 600
                data[victim]["military_upkeep"] = 500
            return data
        
        engine.economy_manager.resource_handler.precalculate_economics = mock_precalc
        original_process_economy()
        
    engine.economy_manager.process_economy = mock_process_economy
    
    # Proxy method to capture logs
    original_log = engine.telemetry.log_event
    
    def output_log_proxy(*args, **kwargs):
        # Infer arguments for buffer (Best effort)
        # Signature: log_event(self, category, event_name, data, turn=0, faction=None)
        # But since we are proxying bound method or unbound instance? 
        # engine.telemetry.log_event is a bound method.
        # So args[0] is category, args[1] is event_name... OR they are in kwargs.
        
        category = kwargs.get('category') or (args[0] if len(args) > 0 else None)
        event = kwargs.get('event_name') or kwargs.get('event') or (args[1] if len(args) > 1 else None)
        data = kwargs.get('data') or (args[2] if len(args) > 2 else {})
        turn = kwargs.get('turn') or (args[3] if len(args) > 3 else 0)
        faction = kwargs.get('faction') or (args[4] if len(args) > 4 else None)
        
        telemetry_buffer.append({"category": category, "event": event, "data": data, "turn": turn, "faction": faction})
        
        try:
            original_log(*args, **kwargs)
        except Exception as e:
            print(f"Proxy Log Error: {e}")
        
    engine.telemetry.log_event = output_log_proxy
    
    # 3. Process Turns
    print("Running simulation (5 turns)...")
    for i in range(1, 6):
        engine.process_turn()
        
    # 4. Analyze Results
    print("\n--- Telemetry Analysis ---")
    
    found_health_score = False
    found_insolvency = False
    found_recovery = False
    
    for log in telemetry_buffer:
        evt = log["event"]
        cat = log["category"]
        fac = log["faction"]
        
        if fac != victim: continue
        
        if evt == "economic_health_score":
            found_health_score = True
            print(f"  [Health Score] Score: {log['data']['score']} (Debt: {log['data']['stockpile']})")
            
        if evt == "insolvency_prediction":
            found_insolvency = True
            pred = log['data']['predicted_turns_until_zero']
            print(f"  [Insolvency] Predicted turns: {pred} (Confidence: {log['data']['confidence']})")
            
        if evt == "recovery_event":
            found_recovery = True
            print(f"  [Recovery] Type: {log['data']['event_type']} (Severity: {log['data']['severity']})")
            
    # 5. Assertions
    if found_health_score:
        print("\n[SUCCESS] Economic Health Score tracking verified.")
    else:
        print("\n[FAIL] No Health Score events found.")
        
    if found_insolvency:
        print("[SUCCESS] Insolvency Prediction verified.")
    else:
        print("[FAIL] No Insolvency Prediction events found (Check threshold?).")
        
    if found_recovery:
        print("[SUCCESS] Recovery Events verified.")
    else:
        print("[FAIL] No Recovery events found (Maybe needs deeper debt?).")

if __name__ == "__main__":
    verify_telemetry()

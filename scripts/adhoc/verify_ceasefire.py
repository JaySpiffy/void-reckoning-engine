
import sys
import os
from unittest.mock import MagicMock

# Ensure project root is in path
sys.path.append(os.getcwd())

from src.managers.diplomacy_manager import DiplomacyManager
from src.managers.treaty_coordinator import TreatyCoordinator
from src.services.relation_service import RelationService

def test_ceasefire_logic():
    # Setup
    factions = ["Imperium", "Chaos"]
    
    # Mock Engine
    engine = MagicMock()
    engine.turn_counter = 10
    engine.factions = {f: MagicMock() for f in factions}
    engine.get_faction = lambda f: engine.factions.get(f)
    
    # Mock UniverseDataManager to avoid database/singleton issues
    from src.core.universe_data import UniverseDataManager
    UniverseDataManager.get_instance = MagicMock(return_value=MagicMock(get_historical_bias=lambda: {}))

    # Initialize components
    dm = DiplomacyManager(factions, engine)
    
    # 1. Start at War
    dm.treaty_coordinator.set_treaty("Imperium", "Chaos", "War")
    dm.relation_service.relations["Imperium"]["Chaos"] = -100
    
    print(f"Initial State: {dm.get_treaty('Imperium', 'Chaos')} (Turn {engine.turn_counter})")
    
    # 2. Forge Peace (should trigger 10-turn ceasefire)
    # Set relations to allow peace
    dm.relation_service.relations["Imperium"]["Chaos"] = -20
    dm.relation_service.relations["Chaos"]["Imperium"] = -20
    
    print("Attempting to sign peace treaty...")
    dm._try_make_peace("Imperium", "Chaos", -20, engine.turn_counter)
    
    current_state = dm.get_treaty("Imperium", "Chaos")
    print(f"State after peace offer: {current_state}")
    
    # 3. Verify Cooldown
    is_on_cd = dm.treaty_coordinator.is_on_cooldown("Imperium", "Chaos", engine.turn_counter)
    expiry = dm.treaty_coordinator.state_change_cooldowns.get("Chaos_Imperium", 0)
    print(f"Is on cooldown: {is_on_cd} (Expires turn {expiry})")
    
    if current_state == "Peace" and is_on_cd and expiry == (engine.turn_counter + 10):
        print("SUCCESS: 10-turn ceasefire correctly enforced.")
    else:
        print(f"FAILURE: Expected Peace with 10-turn CD. Got {current_state} with expiry {expiry}")
        return

    # 4. Verify War Declaration is blocked
    print("\nAttempting to re-declare war during ceasefire (Turn 15)...")
    engine.turn_counter = 15
    dm.relation_service.relations["Imperium"]["Chaos"] = -100
    
    # Run decisions
    dm._process_ai_decisions(engine.turn_counter)
    
    state_after_decision = dm.get_treaty("Imperium", "Chaos")
    print(f"State at Turn 15: {state_after_decision}")
    
    if state_after_decision == "Peace":
        print("SUCCESS: War declaration blocked by ceasefire.")
    else:
        print("FAILURE: War re-declared during ceasefire!")
        return

    # 5. Verify War Declaration works after expiry
    print(f"\nAttempting to re-declare war after ceasefire expiry (Turn {expiry})...")
    engine.turn_counter = expiry
    dm._process_ai_decisions(engine.turn_counter)
    
    state_final = dm.get_treaty("Imperium", "Chaos")
    print(f"State at Turn {engine.turn_counter}: {state_final}")
    
    if state_final == "War":
        print("SUCCESS: War re-declared after ceasefire expired.")
    else:
        print("FAILURE: War declaration failed to trigger after ceasefire.")

if __name__ == "__main__":
    test_ceasefire_logic()

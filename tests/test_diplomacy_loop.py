import pytest
from unittest.mock import MagicMock
from src.managers.diplomacy_manager import DiplomacyManager
from dataclasses import dataclass, field

# Mock needed classes
@dataclass
class MockFaction:
    name: str
    stats: dict = field(default_factory=lambda: {"turn_diplomacy_actions": 0})
    quirks: dict = field(default_factory=dict) # Added quirks 

@dataclass
class MockPersonality:
    quirks: dict = field(default_factory=dict)

@dataclass
class MockAI:
    personalities: dict = field(default_factory=dict)
    def get_faction_personality(self, faction):
        return self.personalities.get(faction, MockPersonality())

@dataclass
class MockTelemetry:
    def log_event(self, *args, **kwargs): pass

class MockEngine:
    def __init__(self):
        self.factions = {}
        self.turn_counter = 1
        self.logger = None
        self.faction_reporter = None
        self.telemetry = MockTelemetry() # Fix: Provide mock
        self.strategic_ai = MockAI()
        self.report_organizer = None 
        
        # Add Faction Reporter Mock
        class MockReporter:
            def log_event(self, *args, **kwargs): pass
        self.faction_reporter = MockReporter() 

    def get_faction(self, name):
        return self.factions.get(name) 

class TestDiplomacyLoop:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.engine = MockEngine()
        # Mock TreatyCoordinator to isolate DiplomacyManager logic
        self.mock_coordinator = MagicMock()
        self.mock_coordinator.get_treaty.return_value = "War" # Default state
        self.mock_coordinator.is_on_cooldown.return_value = False
        
        self.factions = ["FactionA", "FactionB"]
        for f in self.factions:
            self.engine.factions[f] = MockFaction(f)
            
        self.diplomacy = DiplomacyManager(self.factions, self.engine)
        self.diplomacy.treaty_coordinator = self.mock_coordinator # Inject Mock
        
        # Override relations to create the loop condition
        self.diplomacy.relations["FactionA"]["FactionB"] = -80
        self.diplomacy.relations["FactionB"]["FactionA"] = 0
        
        # Set State to WAR (via mock return value or side effect if needed)
        def get_treaty_side_effect(f1, f2):
            return "War"
        self.mock_coordinator.get_treaty.side_effect = get_treaty_side_effect

    def test_mutual_consent_prevents_loop(self):
        """
        Verify that FactionB cannot unilaterally declare peace when FactionA hates them.
        """
        # Run process_turn logic
        self.diplomacy.process_turn()
        
        # Check Result: set_treaty should NOT be called for Peace
        # Because FactionA (-80) rejects Peace.
        # FactionB (0) wants Peace.
        # But _try_make_peace checks MUTUAL relations.
        # Rel(A->B) = -80. -80 < -30? Yes. So FactionA wants War.
        # _try_make_peace for (A, B): A hates B. Won't propose.
        # _try_make_peace for (B, A): B likes A (> -30). Proposes?
        # Logic: 
        # elif rel > -30 and state == "War": self._try_make_peace(f1, f2...)
        # Iteration (FactionA, FactionB): Rel -80. Condition fails.
        # Iteration (FactionB, FactionA): Rel 0. Condition (0 > -30) Passes. Calls _try_make_peace(B, A).
        # Inside _try_make_peace(B, A):
        # rel_target = get_relation(A, B) = -80.
        # if rel_target > -50: set_treaty(Peace).
        # -80 is NOT > -50.
        # So set_treaty is NOT called.
        
        # Assert set_treaty was NOT called with args (FactionB, FactionA, "Peace")
        # Assert set_treaty was NOT called with args (FactionA, FactionB, "Peace")
        
        calls = self.mock_coordinator.set_treaty.mock_calls
        peace_calls = [c for c in calls if c.args[2] == "Peace"]
        assert len(peace_calls) == 0, f"Peace should NOT be signed. Calls: {calls}"
        
    def test_mutual_consent_allows_peace_when_liked(self):
        """
        Verify peace is signed if BOTH parties like each other.
        """
        # Set Relations to Friendly
        self.diplomacy.relations["FactionA"]["FactionB"] = 10
        self.diplomacy.relations["FactionB"]["FactionA"] = 10
        
        # Run process_turn logic
        self.diplomacy.process_turn()
        
        # Iteration (B, A): Rel 10 > -30. Call _try_make_peace(B, A).
        # Target Rel (A->B) = 10. 10 > -50.
        # Should call set_treaty(B, A, "Peace")
        
        self.mock_coordinator.set_treaty.assert_any_call("FactionB", "FactionA", "Peace")

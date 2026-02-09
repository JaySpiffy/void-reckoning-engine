
import sys
import os
import unittest
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.reporting.terminal.orchestrator import TerminalDashboard

class TestDashboardUI(unittest.TestCase):
    def setUp(self):
        self.dashboard = TerminalDashboard()
        # Mock colors and styles to avoid ANSI clutter in comparison if needed, 
        # but here we want to see if the borders align.
        
    def test_summary_border_alignment(self):
        """Verifies that the summary box borders align correctly with emojis."""
        stats = {
            'turn': 42,
            'GLOBAL_PLANETS': 100,
            'GLOBAL_NEUTRAL': 20,
            'GLOBAL_CONTESTED_PLANETS': 5,
            'GLOBAL_BATTLES': 3,
            'GLOBAL_SPACE_BATTLES': 1,
            'GLOBAL_GROUND_BATTLES': 2,
            'GLOBAL_CASUALTIES_SHIP': 500,
            'GLOBAL_CASUALTIES_GROUND': 1200,
            'GLOBAL_TOTAL_CASUALTIES_SHIP': 5000,
            'GLOBAL_TOTAL_CASUALTIES_GROUND': 12000,
            'GLOBAL_REQUISITION': 1000000,
            'GLOBAL_TECH_AVG': 5.5,
            'GLOBAL_DIPLOMACY': [
                {'members': ['F1', 'F2'], 'type': 'War'},
                {'members': ['F3', 'F4'], 'type': 'Alliance'},
                {'members': ['F5', 'F6'], 'type': 'Trade'}
            ],
            'GLOBAL_ALERTS': [],
            'GLOBAL_ECON_VELOCITY': 75.0,
            'GLOBAL_STORMS_BLOCKING': 2
        }
        
        buffer = []
        self.dashboard._render_boxed_summary(stats, buffer)
        
        # Check alignment
        width = 76
        for i, line in enumerate(buffer):
            # Strip ANSI to check visual characters, 
            # though _visual_width is what we really care about.
            stripped = self.dashboard._strip_ansi(line)
            # The box lines start with 5 spaces padding "     ║"
            # So total width including "║" and border should be consistent.
            
            # The actual line in buffer should have exactly 'width' characters 
            # between the ║ markers internally, OR the total line length should 
            # result in a straight edge.
            
            # Let's count visual width of the content inside the box
            # Line format: "     ║ content ║"
            if '║' in line and '╚' not in line and '╔' not in line:
                # Content is between first and last ║
                parts = line.split('║')
                if len(parts) >= 3:
                    content = parts[1]
                    v_width = self.dashboard._visual_width(content)
                    # Width should be exactly 76 (the 'width' variable in the implementation)
                    self.assertEqual(v_width, 76, f"Line {i} is misaligned! Content: {content}")

    def test_victory_turn_display(self):
        """Verifies that the victory page shows the correct turn."""
        stats = {
            'turn': 123,
            'GLOBAL_VICTORY': {'Faction A': 45.5}
        }
        buffer = []
        self.dashboard._render_victory_overlay(stats, buffer)
        
        # Join buffer and strip to find the turn number
        full_text = self.dashboard._strip_ansi("".join(buffer))
        self.assertIn("Turn 123", full_text)

if __name__ == "__main__":
    unittest.main()

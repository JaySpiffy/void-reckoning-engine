import time
from src.reporting.terminal_dashboard import TerminalDashboard

def test_dashboard_logic():
    print("Testing TerminalDashboard Logic...")
    dash = TerminalDashboard()
    
    # Test initial state
    assert dash.is_paused == False
    assert dash.show_detailed == True
    assert dash.show_galactic_summary == True
    assert dash.show_diplomacy == True
    
    # Test 'p' (pause)
    dash.handle_input('p')
    assert dash.is_paused == True
    dash.handle_input('p')
    assert dash.is_paused == False
    
    # Test 'd' (detailed)
    dash.handle_input('d')
    assert dash.show_detailed == False
    dash.handle_input('d')
    assert dash.show_detailed == True
    
    # Test 's' (summary)
    dash.handle_input('s')
    assert dash.show_galactic_summary == False
    dash.handle_input('s')
    assert dash.show_galactic_summary == True

    # Test 'y' (diplomacy)
    dash.handle_input('y')
    assert dash.show_diplomacy == False
    dash.handle_input('y')
    assert dash.show_diplomacy == True
    
    # Test 'h' (help)
    dash.handle_input('h')
    assert dash.show_help == True
    dash.handle_input('h')
    assert dash.show_help == False
    
    # Test 'f' (filter)
    dash.handle_input('f')
    assert dash.is_filtering == True
    dash.handle_input('1')
    dash.handle_input('b')
    dash.handle_input('i')
    dash.handle_input('o')
    dash.handle_input('\r')
    assert dash.is_filtering == False
    assert dash.faction_filter == "1BIO"
    
    # Test 'q' (quit)
    assert dash.quit_requested == False
    dash.handle_input('q')
    assert dash.quit_requested == True
    
    print("Dashboard Logic Tests Passed!")

if __name__ == "__main__":
    test_dashboard_logic()

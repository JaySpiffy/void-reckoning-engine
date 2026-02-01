import os
import sys
# Add src to path
sys.path.append(os.getcwd())

from src.reporting.indexer import ReportIndexer
from src.reporting.dashboard_data_provider import DashboardDataProvider

# Config
DB_PATH = "reports/campaign_data.db"
RUN_ID = "run_1768696819"
UNIVERSE = "eternal_crusade"
BATCH_ID = "batch_20260118_004019" # From directory name or known batch
# Note: Provider resolves batch_id if unknown/None usually.

def verify_economy():
    print(f"--- Verifying Economy API for {RUN_ID} ---")
    
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    indexer = ReportIndexer(DB_PATH)
    provider = DashboardDataProvider(indexer)
    
    # 1. Test Specific Faction
    print("\n[TEST 1] Specific Faction (Ascended_Order)")
    data = provider.get_faction_revenue_breakdown(UNIVERSE, RUN_ID, "Ascended_Order", None, (0, 100))
    print(f"Keys: {list(data.keys())}")
    print(f"Income: {data.get('income', {}).keys()}")
    print(f"Expenses: {data.get('expenses', {}).keys()}")
    
    # 2. Test ALL Factions (Global View)
    print("\n[TEST 2] Global View (All Factions)")
    # Pass comma-separated list of factions to simulate API behavior?
    # Or 'all'? The Code uses 'all' only if faction=='all', but the API route constructed a CSV string.
    # We should test the provider's CSV handling.
    
    # Get active factions first
    active_factions = provider.get_active_factions(UNIVERSE, RUN_ID, None)
    csv_factions = ",".join(active_factions)
    
    data_global = provider.get_faction_revenue_breakdown(UNIVERSE, RUN_ID, csv_factions, None, (0, 100))
    print(f"Keys: {list(data_global.keys())}")
    
    inc = data_global.get('income', {})
    exp = data_global.get('expenses', {})
    
    print(f"Global Income Categories: {inc}")
    print(f"Global Expense Categories: {exp}")
    
    if 'research' in exp:
        print("\nSUCCESS: Research found in expenses!")
    else:
        print("\nFAILURE: Research NOT found in expenses.")

if __name__ == "__main__":
    verify_economy()

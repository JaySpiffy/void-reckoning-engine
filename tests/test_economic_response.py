import requests
import json

BASE_URL = "http://localhost:8000/api/economic"

def check_endpoint(name, url):
    print(f"--- Checking {name} ---")
    try:
        # Pass a turn_range to avoid large payloads, though defaults should work
        response = requests.get(url, params={"factions": "all", "turn_range": "0,100"})
        if response.status_code != 200:
            print(f"FAILED: {response.status_code}")
            print(response.text)
            return

        data = response.json()
        print(json.dumps(data, indent=2))
        
        # Check for potentially missing keys that could crash frontend
        if name == "net_profit":
            if "factions" not in data: print("CRITICAL: 'factions' key missing in net_profit")
            if data.get("factions") is None: print("CRITICAL: 'factions' is None")
            
        if name == "revenue_breakdown":
            if "income" not in data: print("CRITICAL: 'income' key missing")
            if "expenses" not in data: print("CRITICAL: 'expenses' key missing")

        if name == "stockpile_velocity":
            if "factions" not in data: print("CRITICAL: 'factions' key missing")
            
    except Exception as e:
        print(f"ERROR: {e}")

check_endpoint("net_profit", f"{BASE_URL}/net_profit")
check_endpoint("revenue_breakdown", f"{BASE_URL}/revenue_breakdown")
check_endpoint("stockpile_velocity", f"{BASE_URL}/stockpile_velocity")
check_endpoint("resource_roi", f"{BASE_URL}/resource_roi")

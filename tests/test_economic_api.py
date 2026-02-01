import requests
import json

def check_api():
    base_url = "http://localhost:8000/api"
    
    # 1. Check Revenue Breakdown
    print("\n--- Checking Revenue Breakdown ---")
    try:
        r = requests.get(f"{base_url}/economic/revenue_breakdown")
        if r.status_code == 200:
            print("Status: 200 OK")
            # print(json.dumps(r.json(), indent=2))
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")

    # 2. Check Net Profit
    print("\n--- Checking Net Profit ---")
    try:
        r = requests.get(f"{base_url}/economic/net_profit?factions=all")
        if r.status_code == 200:
            print("Status: 200 OK")
            # print(json.dumps(r.json(), indent=2))
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")

    # 3. Check Resource ROI
    print("\n--- Checking Resource ROI ---")
    try:
        r = requests.get(f"{base_url}/economic/resource_roi?factions=all")
        if r.status_code == 200:
            print(json.dumps(r.json(), indent=2))
        else:
            print(f"Error {r.status_code}: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    check_api()

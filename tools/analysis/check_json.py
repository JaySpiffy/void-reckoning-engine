import json
import os

path = "universes/star_trek/parsed_country_types.json"
if os.path.exists(path):
    with open(path, 'r') as f:
        data = json.load(f)
        print(f"Total keys: {len(data)}")
        if "borg_collective" in data:
            print(f"Borg Aggression: {data['borg_collective'].get('aggression')}")
            print(f"Borg Data: {data['borg_collective']}")
        else:
            print("borg_collective NOT FOUND")
            # Print keys containing borg
            matches = [k for k in data.keys() if "borg" in k]
            print(f"Keys with 'borg': {matches}")
else:
    print("JSON not found")

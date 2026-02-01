
import sys
import os
import traceback
from src.utils.unit_parser import parse_json_roster

path = "C:/Users/whitt/OneDrive/Desktop/New folder (4)/universes/eternal_crusade/units/procedural_roster.json"
print(f"Testing parse_json_roster on: {path}")

try:
    units = parse_json_roster(path, "Procedural_Test")
    print(f"Success! Parsed {len(units)} units.")
    if units:
        print(f"Sample: {units[0].name}")
except Exception as e:
    print("FAILED to parse roster:")
    traceback.print_exc()

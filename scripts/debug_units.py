
import sys
import os
from src.utils.unit_parser import load_all_units
from src.combat.combat_utils import find_unit_by_name

print("Loading units...")
units = load_all_units()
print(f"Loaded {len(units)} factions.")
for f, us in units.items():
    print(f"  - {f}: {len(us)} units")
    if "Zealot" in f:
        print(f"  Listing {len(us)} units for {f}:")
        for u in us:
            print(f"    * {u.name} (ID: {getattr(u, 'blueprint_id', 'N/A')})")

target = "Zealot_Legions Standard Fighter"
print(f"\nSearching for '{target}'...")
found = find_unit_by_name(units, target)
if found:
    print(f"FOUND: {found.name}")
else:
    print("NOT FOUND.")


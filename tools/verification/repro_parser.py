from src.utils.paradox_parser import ParadoxParser
import os

p = ParadoxParser()
target = "examples_only/star_trak/common/country_types/STH_borg.txt"

print(f"Parsing {target}...")
try:
    data = p.parse_file(target)
    print(f"Keys found: {list(data.keys())}")
    borg = data.get("borg_collective", {})
    ai = borg.get("ai", {})
    print(f"Borg AI keys: {list(ai.keys())}")
    print(f"Min Navy: {ai.get('min_navy_for_wars')}")
except Exception as e:
    print(f"Error: {e}")

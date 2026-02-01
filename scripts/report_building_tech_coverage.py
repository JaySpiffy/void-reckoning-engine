
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
UNIVERSE_DIR = BASE_DIR / "universes" / "eternal_crusade"
INFRA_DIR = UNIVERSE_DIR / "infrastructure"
TECH_DIR = UNIVERSE_DIR / "technology"
FACTIONS_DIR = UNIVERSE_DIR / "factions"
REPORT_FILE = UNIVERSE_DIR / "BUILDINGS_TECH_COVERAGE.md"

def load_json(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_report():
    buildings = load_json(INFRA_DIR / "building_registry.json")
    technologies = load_json(TECH_DIR / "technology_registry.json")
    faction_registry = load_json(FACTIONS_DIR / "faction_registry.json")
    factions = sorted(list(faction_registry.keys()))
    
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Eternal Crusade Building & Technology Coverage\n\n")
        
        # --- BUILDINGS SECTION ---
        f.write("## Infrastructure Coverage\n\n")
        f.write("| Faction | Total Buildings | With Cost | With Tier | Status |\n")
        f.write("|---|---|---|---|---|\n")
        
        for faction in factions:
            faction_buildings = [b for b in buildings.values() if b.get('faction') == faction]
            total = len(faction_buildings)
            with_cost = len([b for b in faction_buildings if b.get('cost', 0) > 0])
            with_tier = len([b for b in faction_buildings if b.get('tier', 0) > 0])
            
            status = "✅ OK" if total > 0 and with_cost == total else "⚠️ Incomplete"
            if total == 0: status = "❌ Missing"
            
            f.write(f"| {faction} | {total} | {with_cost} | {with_tier} | {status} |\n")
            
        f.write("\n")
        
        # --- TECHNOLOGY SECTION ---
        f.write("## Technology Coverage\n\n")
        f.write("| Faction | Total Techs | With Cost | With Tier | Status |\n")
        f.write("|---|---|---|---|---|\n")
        
        for faction in factions:
            faction_techs = [t for t in technologies.values() if t.get('faction') == faction]
            total = len(faction_techs)
            with_cost = len([t for t in faction_techs if t.get('cost', 0) > 0])
            with_tier = len([t for t in faction_techs if t.get('tier', 0) > 0])
            
            status = "✅ OK" if total > 0 and with_cost == total else "⚠️ Incomplete"
            if total == 0: status = "❌ Missing"
            
            f.write(f"| {faction} | {total} | {with_cost} | {with_tier} | {status} |\n")

    print(f"Report generated at {REPORT_FILE}")

if __name__ == "__main__":
    generate_report()

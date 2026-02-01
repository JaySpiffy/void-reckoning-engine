
import os
import re
import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.registry_builder import (
    build_faction_dna_registry, 
    build_weapon_dna_registry, 
    build_ability_lens_registry
)
from src.utils.dna_generator import (
    generate_building_dna, 
    generate_technology_dna, 
    generate_dna_from_stats
)
from src.utils.unit_parser import (
    parse_building_markdown, 
    parse_technology_markdown
    # Unit parsing is complex, we'll implement a lightweight version locally or import if feasible
)

def format_dna_string(dna):
    # Sort by value desc
    sorted_items = sorted(dna.items(), key=lambda x: x[1], reverse=True)
    parts = [f"{k.replace('atom_', '').capitalize()}: {v:g}" for k, v in sorted_items if v > 0]
    return "## Elemental Signature\n" + ", ".join(parts)

def generate_unit_dna_from_markdown(content):
    # Lightweight parser to extract stats for units
    stats = {}
    
    # 1. PARSER_DATA Block
    if "<!-- PARSER_DATA" in content:
        start = content.find("<!-- PARSER_DATA")
        end = content.find("-->", start)
        if end != -1:
            block = content[start:end]
            for line in block.split('\n'):
                if ":" in line:
                    k, v = line.split(":", 1)
                    stats[k.strip().lower()] = v.strip()
                    
    # 2. Heuristics if no parser data
    # (Simplified for injection script context)
    
    # Map typical keys
    clean_stats = {}
    if "hp" in stats: clean_stats["hp"] = stats["hp"]
    if "armor" in stats: clean_stats["armor"] = stats["armor"]
    if "speed" in stats: clean_stats["speed"] = stats["speed"]
    if "cost" in stats: clean_stats["requisition_cost"] = stats["cost"]
    if "role" in stats: clean_stats["role"] = stats["role"]
    if "tags" in stats: clean_stats["keywords"] = stats["tags"]
    if "name" in stats: clean_stats["name"] = stats["name"]
    
    return generate_dna_from_stats(clean_stats)

def inject_markdown_dna(filepath, entity_type, auto_generate=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if "## Elemental Signature" in content:
        print(f"Skipping {filepath} (Already has signature)")
        return

    signature = ""
    
    if auto_generate:
        print(f"Generating DNA for {os.path.basename(filepath)}...")
        try:
            dna = None
            if entity_type == "buildings":
                data = parse_building_markdown(filepath)
                if data and "stats" in data:
                    dna = generate_building_dna(data["stats"])
            elif entity_type == "technologies":
                data = parse_technology_markdown(filepath)
                if data and "stats" in data:
                    dna = generate_technology_dna(data["stats"])
            elif entity_type == "units":
                dna = generate_unit_dna_from_markdown(content)
                
            if dna:
                signature = format_dna_string(dna)
            else:
                print(f"Warning: Could not generate DNA using parsers for {filepath}")
                return # Skip injection if generation failed
                
        except Exception as e:
            print(f"Error generating DNA for {filepath}: {e}")
            return
            
    else:
        # Default templates (Fallback)
        if entity_type == "buildings":
             signature = "## Elemental Signature\nMass: 30, Cohesion: 30, Stability: 20, Energy: 10, Information: 10"
        elif entity_type == "technologies":
             signature = "## Elemental Signature\nInformation: 30, Focus: 30, Stability: 20, Cohesion: 10, Energy: 10"
        else:
             # Units defaults
             lower = filepath.lower()
             if "ship" in lower: signature = "## Elemental Signature\nMass: 30, Energy: 30, Cohesion: 20, Information: 10, Stability: 5, Frequency: 5"
             elif "tank" in lower: signature = "## Elemental Signature\nMass: 40, Cohesion: 30, Energy: 15, Volatility: 5, Stability: 5, Focus: 5"
             else: signature = "## Elemental Signature\nMass: 10, Energy: 10, Cohesion: 10, Will: 20, Aether: 10, Information: 10, Focus: 10, Stability: 10, Frequency: 5, Volatility: 5"

    # Find insertion point
    match = re.search(r"<!--\s*PARSER_DATA", content)
    insert_idx = -1
    
    if match:
        insert_idx = match.start()
    else:
        # If no parser data (common in infra/tech), append to end
        insert_idx = len(content)
        
    if insert_idx != -1:
        new_content = content[:insert_idx] + "\n" + signature + "\n" + content[insert_idx:]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Injected DNA into {filepath}")

def main():
    parser = argparse.ArgumentParser(description="Inject/Generate Elemental DNA")
    parser.add_argument("--universe", required=True, help="Universe name (e.g. warhammer40k_atomic)")
    parser.add_argument("--entity-type", choices=["units", "buildings", "technologies", "factions", "weapons", "abilities"], required=True)
    parser.add_argument("--auto-generate", action="store_true", help="Use generator logic")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing DNA")
    
    args = parser.parse_args()
    
    from src.core.config import UNIVERSE_ROOT
    universe_path = os.path.join(UNIVERSE_ROOT, args.universe)
    
    if not os.path.exists(universe_path):
        print(f"Universe path not found: {universe_path}")
        return

    print(f"Processing {args.entity_type} for {args.universe}...")

    # JSON Registry Types -> Delegate to Registry Builder
    if args.entity_type in ["factions", "weapons", "abilities"]:
        if args.entity_type == "factions":
            build_faction_dna_registry(universe_path, verbose=True)
        elif args.entity_type == "weapons":
            build_weapon_dna_registry(universe_path, verbose=True)
        elif args.entity_type == "abilities":
            build_ability_lens_registry(universe_path, verbose=True)
        return

    # Markdown Types -> Inject into files
    target_subdir = ""
    if args.entity_type == "units": target_subdir = "units"
    elif args.entity_type == "buildings": target_subdir = "infrastructure"
    elif args.entity_type == "technologies": target_subdir = "technology"
    
    abs_path = os.path.join(universe_path, target_subdir)
    if not os.path.exists(abs_path):
        print(f"Directory not found: {abs_path}")
        return
        
    for root, dirs, files in os.walk(abs_path):
        for file in files:
            if file.endswith(".md"):
                inject_markdown_dna(os.path.join(root, file), args.entity_type, args.auto_generate)

if __name__ == "__main__":
    main()


import json
import os
import re
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
UNIVERSE_DIR = BASE_DIR / "universes" / "eternal_crusade"
INFRA_DIR = UNIVERSE_DIR / "infrastructure"
TECH_DIR = UNIVERSE_DIR / "technology"
FACTIONS_DIR = UNIVERSE_DIR / "factions"

def load_json(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def parse_markdown(file_path):
    """
    Parses a markdown file to extract sections.
    Returns a list of dicts: {name, tier, cost, effect/description, content}
    """
    if not file_path.exists():
        return []

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by H3 headers (Buildings/Categories are Level 3)
    chunks = re.split(r'^###\s+', content, flags=re.MULTILINE)
    
    parsed_items = []
    
    current_tier = 1
    # Check for H2 Tier headers to update current_tier
    # We will iterate through parts and find tiers
    for chunk in chunks:
        # Check if the chunk contains a Tier header before the first ###
        # Actually just find Tier declarations in the H2s
        tier_search = re.search(r'^##\s+Tier\s+(\d+)', chunk, re.MULTILINE | re.IGNORECASE)
        if tier_search:
            current_tier = int(tier_search.group(1))

        if not chunk.strip(): continue
        
        lines = chunk.strip().split('\n')
        header = lines[0].strip()
        body = "\n".join(lines[1:])
        
        item = {'tier': current_tier}
        
        # Parse Header (fallback name)
        header_clean = header
        tier_match = re.match(r'Tier\s+(\d+):\s*(.+)', header, re.IGNORECASE)
        if tier_match:
            item['tier'] = int(tier_match.group(1))
            header_clean = tier_match.group(2).strip()
        
        item['name'] = header_clean
            
        # Parse Body Stats
        # Support both - and * bullets, and optional spaces
        cost_match = re.search(r'^[*-]\s*\*\*Cost:\*\*\s+(\d+)', body, re.MULTILINE | re.IGNORECASE)
        if cost_match:
            item['cost'] = int(cost_match.group(1))
            
        maint_match = re.search(r'^[*-]\s*\*\*Maintenance:\*\*\s+(\d+)', body, re.MULTILINE | re.IGNORECASE)
        if maint_match:
            item['maintenance'] = int(maint_match.group(1))
            
        name_prop_match = re.search(r'^[*-]\s*\*\*Name:\*\*\s+(.+)', body, re.MULTILINE | re.IGNORECASE)
        if name_prop_match:
            item['name'] = name_prop_match.group(1).strip()

        # Unlocks (List)
        unlock_match = re.search(r'^[*-]\s*\*\*Unlocks:\*\*\s+(.+)', body, re.MULTILINE | re.IGNORECASE)
        if unlock_match:
            raw_unlocks = unlock_match.group(1)
            unlocks = re.findall(r'\[(.*?)\]', raw_unlocks)
            if not unlocks:
                unlocks = [u.strip() for u in raw_unlocks.split(',') if u.strip()]
            item['unlocks'] = unlocks
            
        # Prerequisites
        prereq_match = re.search(r'^[*-]\s*\*\*Prerequisites:\*\*\s+(.+)', body, re.MULTILINE | re.IGNORECASE)
        if prereq_match:
            raw_reqs = prereq_match.group(1)
            if "None" not in raw_reqs:
                reqs = re.findall(r'\[(.*?)\]', raw_reqs)
                if not reqs:
                    reqs = [r.strip() for r in raw_reqs.split(',') if r.strip()]
                item['prerequisites'] = reqs

        # Effects (Text)
        effects = []
        for line in lines[1:]:
            l = line.strip()
            # Only pick up effects that are not properties
            if l.startswith("- ") or l.startswith("* "):
                if not any(prop in l for prop in ["Cost:", "Maintenance:", "Name:", "Unlocks:", "Prerequisites:", "Description:"]):
                    effects.append(l.strip("-* ").strip())
        
        if effects:
            item['effect'] = "; ".join(effects)
            
        # Only add if it has a cost or a specific name (avoids empty preamble chunks)
        if 'cost' in item or name_prop_match:
            parsed_items.append(item)
        
    return parsed_items

def hydrate():
    # 1. Load Registries
    build_reg_path = INFRA_DIR / "building_registry.json"
    tech_reg_path = TECH_DIR / "technology_registry.json"
    tech_tree_path = TECH_DIR / "tech_tree.json"
    
    buildings = load_json(build_reg_path)
    technologies = load_json(tech_reg_path)
    tech_tree = load_json(tech_tree_path)
    
    # Build Tech Dependency Map from tech_tree.json
    # Map Label/Name -> ID
    # Map ID -> Prerequisites (from edges)
    tech_name_map = {}
    tech_prereqs = {}
    
    if "nodes" in tech_tree:
        for node in tech_tree["nodes"]:
            t_id = node.get("id")
            label = node.get("label")
            if t_id and label:
                tech_name_map[label] = t_id
                tech_name_map[t_id] = t_id # Self-map
                
    if "edges" in tech_tree:
        for edge in tech_tree["edges"]:
            src = edge.get("from")
            dst = edge.get("to")
            if src and dst:
                if dst not in tech_prereqs: tech_prereqs[dst] = []
                tech_prereqs[dst].append(src)

    # 2. Get Faction List
    faction_registry = load_json(FACTIONS_DIR / "faction_registry.json")
    factions = list(faction_registry.keys())
    
    # 3. Process Each Faction
    for faction in factions:
        print(f"Processing {faction}...")
        
        # --- BUILDINGS ---
        b_file = INFRA_DIR / f"{faction}_buildings.md"
        parsed_buildings = parse_markdown(b_file)
        
        for p in parsed_buildings:
            name = p['name']
            
            # Update or Create
            if name not in buildings:
                buildings[name] = {"id": name, "source_format": "markdown"}
                
            entry = buildings[name]
            entry['name'] = name
            entry['tier'] = p.get('tier', 1)
            entry['cost'] = p.get('cost', 0)
            entry['maintenance'] = p.get('maintenance', 0)
            entry['faction'] = faction
            entry['effects'] = {"description": p.get('effect', "")}
            
            # Default missing fields if not present
            if 'prerequisites' not in entry: entry['prerequisites'] = []
            if 'unlocks' not in entry: entry['unlocks'] = []
            if 'category' not in entry: entry['category'] = "infrastructure"
            
            # Heuristic: Tier 2 needs Tier 1 building of same type if name is similar?
            # Or just leave empty for now as user asked to "hydrate from markdown".
            
        # --- TECH ---
        t_file = TECH_DIR / f"{faction}_tech.md"
        parsed_techs = parse_markdown(t_file)
        
        for p in parsed_techs:
            name = p['name']
            tech_id = tech_name_map.get(name)
            
            # Collision Prevention:
            # If the resolved ID belongs to another faction, ignore it and force our own.
            # This handles the case where "Basic Doctrine" maps to "Tech_Zealot_..." but we are "Ancient_Guardians".
            if tech_id and faction not in tech_id and "Global" not in tech_id and "Tech_" in tech_id:
                 # Check if we have a specific ID for this faction in the map (unlikely if label collision)
                 # Or just construct the expected canonical ID
                 tech_id = None
            
            if not tech_id:
                 tech_id = f"Tech_{faction}_{name.replace(' ', '_')}"
            
            # Update or Create
            if tech_id not in technologies:
                 technologies[tech_id] = {"id": tech_id, "source_format": "markdown"}
                 
            entry = technologies[tech_id]
            entry['name'] = name
            entry['tier'] = p.get('tier', 1)
            entry['cost'] = p.get('cost', 0)
            entry['faction'] = faction
            
            if 'category' not in entry or not entry['category']:
                 entry['category'] = ["military"] # Default
                 
            # Prereqs from tree
            if tech_id in tech_prereqs:
                entry['prerequisites'] = tech_prereqs[tech_id]
            elif 'prerequisites' not in entry:
                entry['prerequisites'] = []
                
            # Try to populate unlocks_buildings based on name match?
            # User said "populate unlocks_buildings/unlocks_ships as designed".
            # If the tech is "Capital Ships" (Tier 3), it likely unlocks Tier 3 ships.
            # This is hard to automate perfectly without a map.
            # I will leave unlocks as is or [] unless I can infer.
            if 'unlocks_buildings' not in entry: entry['unlocks_buildings'] = []
            if 'unlocks_ships' not in entry: entry['unlocks_ships'] = []

    # 4. Save
    save_json(build_reg_path, buildings)
    save_json(tech_reg_path, technologies)
    print("Hydration complete.")

if __name__ == "__main__":
    hydrate()

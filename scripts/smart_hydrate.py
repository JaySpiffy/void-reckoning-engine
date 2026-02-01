
import json
import os
import re
from pathlib import Path
from collections import defaultdict

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
    Parses a markdown file with robust handling for bold keys.
    """
    if not file_path.exists(): return []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find building blocks starting with ### Tier X: Name
    building_pattern = re.compile(r'###\s+Tier\s+(\d+):\s+(.+?)\n(.*?)(?=\n#+|$)', re.DOTALL)
    
    parsed_items = []
    
    matches = building_pattern.findall(content)
    for tier_str, name, body in matches:
        item = {
            "name": name.strip(),
            "tier": int(tier_str)
        }
        
        # Robust parsing for "Key: Value" or "**Key:** Value"
        def extract_int(key, text):
            # Matches "Key:", optional markup, space, digits
            m = re.search(rf'{key}:.*?(\d+)', text, re.IGNORECASE)
            return int(m.group(1)) if m else 0
            
        item['cost'] = extract_int('Cost', body)
        item['maintenance'] = extract_int('Maintenance', body)
        item['build_time'] = extract_int('Build Time', body)

        # Unlocks
        unlocks_match = re.search(r'Unlocks:.*?(?:\n|$|(?<=\:))\s*(.+)', body, re.IGNORECASE)
        if unlocks_match:
            raw = unlocks_match.group(1)
            # Clean markup like **, [], etc.
            clean = raw.replace('*', '').replace('[', '').replace(']', '').strip()
            item['unlocks'] = [u.strip() for u in clean.split(',') if u.strip()]
        else:
            item['unlocks'] = []

        # Prerequisites
        prereqs_match = re.search(r'Prerequisites:.*?(?:\n|$|(?<=\:))\s*(.+)', body, re.IGNORECASE)
        if prereqs_match:
            raw = prereqs_match.group(1)
            clean = raw.replace('*', '').replace('[', '').replace(']', '').strip()
            # Filter 'None'
            item['prerequisites'] = [p.strip() for p in clean.split(',') if p.strip() and p.lower() != 'none']
        else:
            item['prerequisites'] = []

        # Effects
        effects_list = []
        # Find "Effects:" line, catch subsequent lines until empty/header
        effects_section = re.search(r'Effects:.*?\n((?:\s*[-*].+\n?)+)', body, re.IGNORECASE)
        if effects_section:
            raw_lines = effects_section.group(1).strip().split('\n')
            for line in raw_lines:
                # Strip bullets, bold markers, spaces
                clean = re.sub(r'^\s*[-*]\s*', '', line).strip() 
                clean = clean.replace('**', '') # Remove bold inside text if desired, or keep it. Let's keep text clean.
                if clean: 
                    # Try to parse structure?
                    # " +15 Morale (Planet-wide)"
                    eff_type = "generic"
                    if "morale" in clean.lower(): eff_type = "morale_bonus"
                    elif "resource" in clean.lower() or "requisition" in clean.lower(): eff_type = "resource_generation"
                    elif "defense" in clean.lower(): eff_type = "planetary_defense"
                    elif "research" in clean.lower(): eff_type = "research_bonus"
                    elif "unlocks" in clean.lower(): eff_type = "unlock"
                    
                    effects_list.append({"type": eff_type, "description": clean})
        
        item['effects'] = effects_list
        item['description'] = body.strip() # Or extract Lore specifically
        
        parsed_items.append(item)
        
    return parsed_items

def parse_tech_markdown(file_path):
    if not file_path.exists(): return []
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # New Hierarchical Format:
    # ## Tier 1
    # ### Basic Doctrine
    if "## Tier" in content and "###" in content:
        items = []
        current_tier = 1
        
        # Split by H2 "Tier" headers
        # Use regex to split but keep delimiters to know which tier
        # Actually, iterating lines or blocks is safer.
        
        # Let's split by "## Tier"
        tier_sections = re.split(r'^##\s+Tier\s+(\d+)', content, flags=re.MULTILINE)
        # Result: [Intro, TierNum, Body, TierNum, Body...]
        
        for i in range(1, len(tier_sections), 2):
            try:
                tier_num = int(tier_sections[i])
                tier_body = tier_sections[i+1]
                
                # Now split tier body by H3 "### Name"
                # Pattern: ### Name \n Body
                tech_blocks = re.split(r'^###\s+(.+)$', tier_body, flags=re.MULTILINE)
                
                for j in range(1, len(tech_blocks), 2):
                    t_name = tech_blocks[j].strip()
                    t_body = tech_blocks[j+1].strip()
                    
                    item = {"name": t_name, "tier": tier_num}
                    
                    # Extract fields
                    # Extract fields
                    # Robust regex for "**Cost:** 1000" or "Cost: 1000"
                    cost_match = re.search(r'Cost[:*]*\s*(\d+)', t_body, re.IGNORECASE)
                    item['cost'] = int(cost_match.group(1)) if cost_match else 1000
                    
                    # Description/Name/Effects
                    # My files have:
                    # - **Cost:** ...
                    # - **Name:** ...
                    # - **Description:** ...
                    # - **Effects:** ...
                    
                    # Extract Description
                    desc_match = re.search(r'Description:\s*(.+)', t_body, re.IGNORECASE)
                    item['description'] = desc_match.group(1).strip() if desc_match else ""
                    
                    # Extract Effects (could be single line or list)
                    # "Effects: +10% Morale..."
                    eff_match = re.search(r'Effects:\s*(.+)', t_body, re.IGNORECASE)
                    if eff_match:
                         # Split commas or just store string
                         item['effects'] = [{"description": eff_match.group(1).strip()}]
                    else:
                         item['effects'] = []
                         
                    items.append(item)
            except Exception as e:
                print(f"Error parsing tier section: {e}")
                continue
                
        return items

    return parse_markdown(file_path) # Fallback if structure differs

def smart_hydrate():
    print("Starting Smart Hydration (Robust H3 Support)...")
    
    buildings_reg_data = {}
    tech_reg_data = {}
    
    # 1. Load Skeleton
    tech_tree = load_json(TECH_DIR / "tech_tree.json")
    tree_nodes = {n['id']: n for n in tech_tree.get("nodes", [])}
    tree_edges = tech_tree.get("edges", [])
    
    tree_reverse_edges = defaultdict(list)
    for e in tree_edges:
        tree_reverse_edges[e['to']].append(e['from'])
        
    # 2. Get Factions
    faction_registry = load_json(FACTIONS_DIR / "faction_registry.json")
    factions = sorted(list(faction_registry.keys()))
    
    # 3. Process
    for faction in factions:
        print(f"  Hydrating {faction}...")
        
        try:
            md_techs = parse_tech_markdown(TECH_DIR / f"{faction}_tech.md")
            md_buildings = parse_markdown(INFRA_DIR / f"{faction}_buildings.md")
            
            print(f"    Found {len(md_buildings)} buildings, {len(md_techs)} techs.")
        except Exception as e:
            print(f"    Error parsing {faction}: {e}")
            continue

        # --- BUILDINGS ---
        faction_building_ids = []
        md_b_by_tier = defaultdict(list)
        for b in md_buildings:
            md_b_by_tier[b.get('tier', 1)].append(b)
            
        for b in md_buildings:
            b_name = b['name']
            safe_name = b_name.replace(" ", "_").replace("-", "_")
            b_id = f"{faction}_{safe_name}"
            
            faction_building_ids.append(b_id)
            b_tier = b.get('tier', 1)
            
            prereqs = b.get('prerequisites', [])
            
            # Heuristic: If Tier > 1 and no building prereq, link to T-1
            has_building_prereq = any("_" in p or "Building" in p for p in prereqs)
            if b_tier > 1 and not has_building_prereq:
                 lower = md_b_by_tier[b_tier - 1]
                 if lower:
                     l_name = lower[0]['name'].replace(" ", "_").replace("-", "_")
                     # ID of lower tier building
                     prereqs.append(f"{faction}_{l_name}")

            buildings_reg_data[b_id] = {
                "id": b_id,
                "name": b_name,
                "tier": b_tier,
                "cost": b['cost'],
                "maintenance": b['maintenance'],
                "build_time": b['build_time'],
                "prerequisites": prereqs,
                "unlocks": b['unlocks'],
                "effects": {
                    "list": b['effects'],
                    "provides_tech_tier": b_tier if "Research" in str(b['effects']) else 0
                },
                "faction": faction,
                "category": "infrastructure",
                "source_file": "markdown"
            }

        # --- TECHS ---
        # Same slotting logic
        # --- TECHS ---
        # Robust Label-Based Matching
        
        # 1. Map MD techs by Header Name (e.g. "Basic Doctrine")
        md_tech_map = {t['name'].lower(): t for t in md_techs}
        
        # 2. Iterate through Generic Tree Nodes
        node_id_map = {} # Generic_ID -> Faction_Specific_ID
        
        for node in tree_nodes.values():
            generic_id = node['id']
            generic_label = node['label']
            tier = node['tier']
            
            # Find flavor in MD
            flavor = md_tech_map.get(generic_label.lower())
            
            # Construct Faction ID
            # e.g. Tech_Zealot_Legions_Conviction_Doctrines OR Tech_Zealot_Legions_Basic_Doctrine?
            # User plan used: Tech_Zealot_Legions_Conviction_Doctrines
            # I should prefer the Flavor Name for the ID if possible, BUT prerequisites act on IDs.
            # If I use Flavor IDs, I must re-map all edges dynamically.
            # "Tech_Basic_Doctrine" -> "Tech_Zealot_Legions_Conviction_Doctrines" works if I keep a map.
            
            flavor_name = flavor['name'] if flavor else generic_label
            # Sanitize name for ID
            safe_flavor_name = str(re.search(r'Name:\s*(.+)', str(flavor.get('description', ''))).group(1) if flavor and 'Name:' in str(flavor.get('description', '')) else flavor_name).strip()
            # Wait, I put "Name: ..." in the bullet points in MD. 
            # My parser puts bullet points in 'effects' list OR just body.
            # Let's check how parser handles "Name: ..." lines.
            # The parser extracts "Cost", "Maintenance". It does NOT extract "Name".
            # It blindly captures the Header as 'name'.
            # So flavor['name'] is "Basic Doctrine".
            # The *Real* faction name is in the body text `Name: Conviction Doctrines`.
            
            # Let's extract specific faction name from body if present
            real_name_match = re.search(r'Name:\s*(.+)', flavor['description'] if flavor else "", re.IGNORECASE)
            real_name = real_name_match.group(1).strip() if real_name_match else flavor_name
            
            safe_id_suffix = real_name.replace(" ", "_").replace("-", "_").replace("'", "")
            new_id = f"Tech_{faction}_{safe_id_suffix}"
            
            node_id_map[generic_id] = new_id
            
            # Prepare Entry
            effs = flavor['effects'] if flavor else []
            
            # Calculate DNA-based bonuses? (Future step)
            # For now just use text.
            
            # Link to Buildings (Unlock)
            unlocks_builds = []
            for b_id in faction_building_ids:
                b_entry = buildings_reg_data[b_id]
                # Heuristic: If Building T1 requires Tech T1?
                # or match keywords.
                if b_entry['tier'] == tier:
                     unlocks_builds.append(b_id)
                     # Add Tech as Prereq to Building
                     if new_id not in b_entry['prerequisites']:
                         b_entry['prerequisites'].append(new_id)

            tech_entry = {
                "id": new_id,
                "name": real_name,
                "tier": tier,
                "cost": flavor.get('cost', node.get('cost', 1000)),
                "prerequisites": [], # Filled later
                "unlocks_buildings": unlocks_builds,
                "unlocks_ships": [],
                "faction": faction,
                "area": "engineering",
                "category": [node.get('category', 'military')],
                "effects": effs,
                "source_file": "smart_hydrate"
            }
            tech_reg_data[new_id] = tech_entry

        # 3. Wire Prerequisites using Generic Graph
        for generic_id, new_id in node_id_map.items():
            if generic_id in tree_reverse_edges:
                parent_generics = tree_reverse_edges[generic_id]
                for p_gen in parent_generics:
                    if p_gen in node_id_map:
                        p_new_id = node_id_map[p_gen]
                        tech_reg_data[new_id]['prerequisites'].append(p_new_id)
                        
    save_json(INFRA_DIR / "building_registry.json", buildings_reg_data)
    save_json(TECH_DIR / "technology_registry.json", tech_reg_data)
    print(f"Hydration Complete. Nodes: {len(tech_reg_data)} Techs, {len(buildings_reg_data)} Buildings.")

if __name__ == "__main__":
    smart_hydrate()

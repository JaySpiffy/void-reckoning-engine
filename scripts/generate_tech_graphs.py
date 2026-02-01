
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
UNIVERSE_DIR = BASE_DIR / "universes" / "eternal_crusade"
TECH_DIR = UNIVERSE_DIR / "technology"
GRAPHS_DIR = TECH_DIR / "graphs"

def load_json(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def ensure_dir(path):
    if not path.exists():
        os.makedirs(path)

def generate_graphs():
    ensure_dir(GRAPHS_DIR)
    
    registry = load_json(TECH_DIR / "technology_registry.json")
    # Groups by faction
    by_faction = {}
    for t_id, t_data in registry.items():
        f = t_data['faction']
        if f not in by_faction: by_faction[f] = []
        by_faction[f].append(t_data)
        
    # Generate Faction Graphs
    for faction, techs in by_faction.items():
        mmd_lines = ["graph TD"]
        mmd_lines.append("    classDef tier1 fill:#90EE90,stroke:#333,stroke-width:2px;")
        mmd_lines.append("    classDef tier2 fill:#FFD700,stroke:#333,stroke-width:2px;")
        mmd_lines.append("    classDef tier3 fill:#FF6347,stroke:#333,stroke-width:2px;")
        
        nodes = []
        edges = []
        
        # Load Unlocks
        unlocked_map = load_json(TECH_DIR / "tech_unlock_map.json")

        for t in techs:
            tid = t['id']
            label = t['name'].replace('"', "'")
            tier = t['tier']
            cost = t['cost']
            
            # Node definition
            class_name = f"tier{tier}"
            mmd_lines.append(f'    {tid}["{label}<br/>(T{tier} | {cost})"]:::{class_name}')
            
            nodes.append({
                "id": tid,
                "label": label,
                "tier": tier,
                "cost": cost
            })
            
            # Prereqs (Solid)
            for p in t['prerequisites']:
                if p in registry:
                    mmd_lines.append(f"    {p} --> {tid}")
                    edges.append({"from": p, "to": tid, "type": "prerequisite"})
            
            # Unlocks (Dashed)
            if tid in unlocked_map:
                u_entry = unlocked_map[tid]
                # Buildings
                for b_id in u_entry['unlocks']['buildings']:
                    # Add Building Node (Different Shape)
                    b_clean = b_id.replace(f"{faction}_", "")
                    mmd_lines.append(f'    {b_id}([{b_clean}])')
                    mmd_lines.append(f"    {tid} -.-> {b_id}")
                    edges.append({"from": tid, "to": b_id, "type": "unlock"})

                    
        # Write MMD
        mmd_path = GRAPHS_DIR / f"{faction}_tech_tree.mmd"
        with open(mmd_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(mmd_lines))
            
        # Write JSON
        json_path = GRAPHS_DIR / f"{faction}_tech_tree.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({"nodes": nodes, "edges": edges}, f, indent=2)
            
    # Generate Global Graph (Simplified)
    global_mmd = ["graph TD"]
    for faction, techs in by_faction.items():
        global_mmd.append(f"    subgraph {faction}")
        for t in techs:
            tid = t['id']
            # Only nodes, edges might be too messy? Include edges.
            for p in t['prerequisites']:
                if p in registry and registry[p]['faction'] == faction:
                    global_mmd.append(f"        {p} --> {tid}")
        global_mmd.append("    end")
        
    with open(GRAPHS_DIR / "Global_tech_tree.mmd", 'w', encoding='utf-8') as f:
        f.write("\n".join(global_mmd))
        
    print(f"Generated graphs for {len(by_faction)} factions in {GRAPHS_DIR}")

if __name__ == "__main__":
    generate_graphs()

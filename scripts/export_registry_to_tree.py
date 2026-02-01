
import json
import os
from pathlib import Path

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
UNIVERSE_DIR = BASE_DIR / "universes" / "eternal_crusade"
TECH_DIR = UNIVERSE_DIR / "technology"

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def export_tree():
    print("Exporting Registry to Tech Tree...")
    registry = load_json(TECH_DIR / "technology_registry.json")
    
    nodes = []
    edges = []
    
    for t_id, t_data in registry.items():
        # Node
        nodes.append({
            "id": t_id,
            "label": t_data['name'],
            "tier": t_data['tier'],
            "cost": t_data['cost'],
            "category": t_data.get('category', ['military'])[0],
            "faction": t_data.get('faction', 'Generic')
        })
        
        # Edges
        for p_id in t_data.get('prerequisites', []):
            if p_id in registry:
                edges.append({
                    "from": p_id,
                    "to": t_id
                })
                
    tree = {
        "nodes": nodes,
        "edges": edges
    }
    
    save_json(TECH_DIR / "tech_tree.json", tree)
    print(f"Exported {len(nodes)} nodes and {len(edges)} edges to tech_tree.json")

if __name__ == "__main__":
    export_tree()


import json
import os
from pathlib import Path
from collections import deque

BASE_DIR = Path(r"c:\Users\whitt\OneDrive\Desktop\New folder (4)")
TECH_DIR = BASE_DIR / "universes" / "eternal_crusade" / "technology"

def load_json(path):
    if not path.exists(): return {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_integrity():
    print("Checking Tech Tree Integrity...")
    registry = load_json(TECH_DIR / "technology_registry.json")
    
    # 1. Group by Faction
    by_faction = {}
    for t_id, t_data in registry.items():
        f = t_data['faction']
        if f not in by_faction: by_faction[f] = []
        by_faction[f].append(t_data)
        
    report = []
    
    for faction, techs in by_faction.items():
        tech_map = {t['id']: t for t in techs}
        tech_ids = set(tech_map.keys())
        
        # Roots (No prereqs)
        roots = [t['id'] for t in techs if not t.get('prerequisites')]
        
        # Reachability BFS
        reachable = set()
        queue = deque(roots)
        while queue:
            curr = queue.popleft()
            if curr in reachable: continue
            reachable.add(curr)
            
            # Find children (who has curr as prereq)
            # Inefficient scan but fine for small size
            for t in techs:
                if curr in t.get('prerequisites', []):
                    queue.append(t['id'])
                    
        # Analysis
        orphans = tech_ids - reachable
        t3_total = len([t for t in techs if t['tier'] == 3])
        t3_reachable = len([t for t in tech_map[tid] for tid in reachable if tech_map[tid]['tier'] == 3])
        
        status = "OK"
        if orphans: status = f"FAIL ({len(orphans)} orphans)"
        
        report.append(f"Faction: {faction}")
        report.append(f"  Roots: {len(roots)}")
        report.append(f"  Reachable: {len(reachable)}/{len(techs)}")
        report.append(f"  T3 Reachable: {t3_reachable}/{t3_total}")
        if orphans:
            report.append(f"  ORPHANS: {orphans}")
        else:
            report.append(f"  Integrity: PASS")
        report.append("")
        
    print("\n".join(report))

if __name__ == "__main__":
    check_integrity()

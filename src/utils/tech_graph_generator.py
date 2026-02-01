
import json
import os
from typing import Dict, List, Any, Optional

class TechGraphGenerator:
    """
    Generates visual representations of tech trees.
    Supports Mermaid (markdown), Graphviz (dot), and JSON graph formats.
    """
    
    def __init__(self, tech_trees: Dict[str, Dict]):
        self.tech_trees = tech_trees # {faction_name: {tech_id: tech_data}}
        
    def generate_dependency_graph(self, faction: str, output_format: str = "mermaid") -> str:
        """Generates a dependency graph string for a specific faction."""
        if faction not in self.tech_trees:
            return ""
            
        tech_tree = self.tech_trees[faction]
        
        if output_format == "mermaid":
            return self._to_mermaid(tech_tree)
        elif output_format == "json":
            return json.dumps(self._to_json_graph(tech_tree), indent=2)
        else:
            return ""

    def _to_mermaid(self, tech_tree: Dict[str, Any]) -> str:
        """Converts tech tree to Mermaid flowchart syntax."""
        lines = ["graph LR"]
        
        # Add Nodes
        for tech_id, tech_data in tech_tree.items():
            # Style based on tier or category
            tier = tech_data.get("tier", 0)
            name = tech_data.get("name", tech_id).replace('"', "'")
            
            # Node definition: id["Label"]
            lines.append(f'    {tech_id}["{name} (T{tier})"]')
            
            # Edges (Prerequisites)
            prereqs = tech_data.get("prerequisites", [])
            for p in prereqs:
                if p in tech_tree:
                    lines.append(f"    {p} --> {tech_id}")
                    
        return "\n".join(lines)

    def _to_json_graph(self, tech_tree: Dict[str, Any]) -> Dict[str, Any]:
        """Converts tech tree to node/edge JSON format."""
        nodes = []
        edges = []
        
        for tech_id, tech_data in tech_tree.items():
            nodes.append({
                "id": tech_id,
                "label": tech_data.get("name", tech_id),
                "tier": tech_data.get("tier", 0),
                "cost": tech_data.get("cost", 0)
            })
            
            prereqs = tech_data.get("prerequisites", [])
            for p in prereqs:
                if p in tech_tree:
                    edges.append({"source": p, "target": tech_id})
                    
        return {"nodes": nodes, "edges": edges}

    def generate_unlock_timeline(self, faction: str) -> List[Dict]:
        """
        Analyzes tech tree to determine optimal research order (timeline).
        Returns a list of tiers, where each tier contains techs unlockable 
        after completing previous tiers.
        """
        if faction not in self.tech_trees: return []
        
        tree = self.tech_trees[faction]
        unlocked = set()
        timeline = []
        
        # Simple topological sort by tiers logic
        # Or just grouping by defined logical tiers?
        # Let's do logical tiers based on prereqs.
        
        remaining = set(tree.keys())
        current_tier_num = 1
        
        while remaining:
            # Find all techs whose prereqs are met
            available = []
            for t_id in list(remaining):
                prereqs = tree[t_id].get("prerequisites", [])
                if all(p in unlocked for p in prereqs):
                    available.append(t_id)
            
            if not available:
                # Cycle detected or unreachable
                break
                
            timeline_entry = {
                "tier": current_tier_num,
                "techs": []
            }
            
            for t in available:
                timeline_entry["techs"].append(tree[t].get("name", t))
                unlocked.add(t)
                remaining.remove(t)
                
            timeline.append(timeline_entry)
            current_tier_num += 1
            
        return timeline

    def export_to_json_graph(self, faction: str, output_path: str):
        """Exports the graph to a JSON file."""
        if faction not in self.tech_trees: return
        data = self._to_json_graph(self.tech_trees[faction])
        
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def validate_tech_tree(self, faction: str) -> List[str]:
        """Checks for cycles and missing prerequisites."""
        if faction not in self.tech_trees: return ["Faction not found"]
        
        tree = self.tech_trees[faction]
        errors = []
        
        # 1. Check Missing Prereqs
        for t_id, data in tree.items():
            for p in data.get("prerequisites", []):
                if p not in tree:
                    errors.append(f"Tech {t_id} requires missing tech {p}")
                    
        # 2. Check Cycles (DFS)
        visited = set()
        rec_stack = set()
        
        def is_cyclic(v, path):
            visited.add(v)
            rec_stack.add(v)
            path.append(v)
            
            prereqs = tree.get(v, {}).get("prerequisites", [])
            for neighbor in prereqs:
                if neighbor not in tree: continue
                if neighbor not in visited:
                    if is_cyclic(neighbor, path): return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(v)
            path.pop()
            return False
            
        for node in tree:
            if node not in visited:
                if is_cyclic(node, []):
                    errors.append(f"Cycle detected involving {node}")
                    
        return errors

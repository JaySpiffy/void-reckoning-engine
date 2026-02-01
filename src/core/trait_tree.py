
from typing import Dict, List, Any, Optional

class TraitNode:
    """
    A single node in a trait tree.
    """
    def __init__(self, trait_id: str, parent: str = None, 
                 children: List[str] = None, 
                 tier: int = 0,
                 requirements: List[str] = None):
        self.trait_id = trait_id
        self.parent = parent
        self.children = children or []
        self.tier = tier
        self.requirements = requirements or []

    def to_dict(self):
        return {
            "trait_id": self.trait_id,
            "parent": self.parent,
            "children": self.children,
            "tier": self.tier,
            "requirements": self.requirements
        }

class TraitTree:
    """
    Represents a hierarchical tree of traits with prerequisites.
    e.g. Resonant Path: Latent Resonant -> Resonant -> Master Resonant
    """
    def __init__(self, tree_id: str, name: str, category: str):
        self.tree_id = tree_id
        self.name = name
        self.category = category
        self.nodes: Dict[str, TraitNode] = {}
        self.root_traits: List[str] = []

    def add_node(self, node: TraitNode):
        self.nodes[node.trait_id] = node
        if not node.parent:
            self.root_traits.append(node.trait_id)
            
    def get_children(self, trait_id: str) -> List[TraitNode]:
        node = self.nodes.get(trait_id)
        if not node: return []
        return [self.nodes[c] for c in node.children if c in self.nodes]
        
    def get_available_upgrades(self, current_traits: List[str]) -> List[str]:
        """Returns list of trait_ids that can be unlocked based on current traits."""
        available = []
        # Check roots
        for root in self.root_traits:
            if root not in current_traits:
                # Add if reqs met (TODO: check external requirements too)
                available.append(root)
        
        # Check children of owned traits
        for tid in current_traits:
            if tid in self.nodes:
                children = self.get_children(tid)
                for child in children:
                    if child.trait_id not in current_traits:
                        available.append(child.trait_id)
        return available

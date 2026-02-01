from typing import List, Dict, Any

class TraitComponent:
    """Manages unit traits and keywords."""
    
    def __init__(self, traits: List[str], abilities: Any):
        self.traits = traits
        # [Compatibility] Convert list-based abilities to dict-based
        if isinstance(abilities, list):
            self.abilities = {"Tags": abilities}
        else:
            self.abilities = abilities or {}
        self.type = "Traits"
        self.is_destroyed = False
        
    def has_trait(self, trait_name: str) -> bool:
        return trait_name in self.traits
        
    def has_ability(self, ability_name: str) -> bool:
        return ability_name in self.abilities
        
    def get_ability_value(self, ability_name: str, default: Any = None) -> Any:
        return self.abilities.get(ability_name, default)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "traits": self.traits,
            "abilities": self.abilities
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TraitComponent':
        return cls(data["traits"], data["abilities"])

from typing import Dict, Any, Optional
from src.core.resource_synthesizer import synthesize_material_properties

class Item:
    """
    Represents an item or resource bundle in the game.
    Uses Elemental DNA to determine its properties and value.
    """
    def __init__(self, name: str, quantity: int = 1, elemental_dna: Optional[Dict[str, float]] = None, properties: Optional[Dict[str, Any]] = None):
        self.name = name
        self.quantity = quantity
        self.elemental_dna = elemental_dna
        
        # Hybrid Stat System: Manual properties take priority
        if properties:
            self.properties = properties
        else:
            self.properties = {}
            if self.elemental_dna:
                self.recalc_properties()
            else:
                # Fallback / Default
                self.properties = {
                    "economic_value": 1,
                    "tags": ["Generic"]
                }

    def recalc_properties(self):
        """Derives material properties from DNA."""
        if self.elemental_dna:
            self.properties = synthesize_material_properties(self.elemental_dna)
    
    @property
    def total_value(self) -> int:
        """Returns total value of stack."""
        return self.properties.get("economic_value", 0) * self.quantity
        
    @property
    def total_mass(self) -> float:
        """Returns total mass of stack."""
        # Need to infer "Mass per unit" from DNA or config.
        # Simplification: Use "Density" score as mass proxy for now?
        # Or just use the Atom Mass directly if it represents Kg? 
        # White Paper says Atom Mass is "Physical bulk".
        unit_mass = self.elemental_dna.get("atom_mass", 1.0) if self.elemental_dna else 1.0
        return unit_mass * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "elemental_dna": self.elemental_dna,
            "properties": self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        return cls(
            name=data.get("name", "Unknown Item"),
            quantity=data.get("quantity", 1),
            elemental_dna=data.get("elemental_dna"),
            properties=data.get("properties")
        )

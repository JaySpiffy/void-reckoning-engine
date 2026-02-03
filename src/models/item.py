from typing import Dict, Any, Optional


class Item:
    """
    Represents an item or resource bundle in the game.
    """
    def __init__(self, name: str, quantity: int = 1, properties: Optional[Dict[str, Any]] = None):
        self.name = name
        self.quantity = quantity
        
        if properties:
            self.properties = properties
        else:
            # Fallback / Default
            self.properties = {
                "economic_value": 1,
                "tags": ["Generic"]
            }

    @property
    def total_value(self) -> int:
        """Returns total value of stack."""
        return self.properties.get("economic_value", 0) * self.quantity
        
    @property
    def total_mass(self) -> float:
        """Returns total mass of stack."""
        return self.properties.get("mass", 1.0) * self.quantity

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "properties": self.properties
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        return cls(
            name=data.get("name", "Unknown Item"),
            quantity=data.get("quantity", 1),
            properties=data.get("properties")
        )

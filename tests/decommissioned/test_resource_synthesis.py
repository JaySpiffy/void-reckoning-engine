import pytest
from src.core.resource_synthesizer import synthesize_material_properties
from src.models.item import Item
from src.core.elemental_signature import (
    ATOM_MASS, ATOM_ENERGY, ATOM_COHESION, ATOM_VOLATILITY, ATOM_AETHER, ATOM_WILL
)

class TestResourceSynthesis:
    
    def test_promethium_fuel(self):
        """Test that Promethium is identified as Fuel and Volatile."""
        dna = {
            ATOM_ENERGY: 60.0,
            ATOM_VOLATILITY: 50.0,
            ATOM_MASS: 10.0
        }
        props = synthesize_material_properties(dna)
        
        assert "Fuel" in props["tags"]
        assert "Explosive" in props["tags"]
        assert props["fuel_potential"] > 70 

    def test_wraithbone_psycho(self):
        """Test that Wraithbone is identified as Psycho-Active."""
        dna = {
            ATOM_COHESION: 30.0,
            ATOM_WILL: 40.0,
            ATOM_AETHER: 30.0
        }
        item = Item("Wraithbone", 10, dna)
        
        assert "Psycho-Active" in item.properties["tags"]
        assert item.total_value > 500 # Should be valuable due to Aether/Will weights

    def test_adamantium_density(self):
        """Test Adamantium density and structural integrity."""
        dna = {
            ATOM_MASS: 50.0,
            ATOM_COHESION: 40.0,
            ATOM_ENERGY: 10.0
        }
        props = synthesize_material_properties(dna)
        
        assert props["density"] > 45
        assert props["integrity"] > 35

    def test_inert_material(self):
        """Test generic inert material."""
        dna = {
            ATOM_MASS: 10.0,
            ATOM_COHESION: 10.0
        }
        item = Item("Dust", 100, dna)
        assert item.properties["primary_application"] == "Inert Filler"

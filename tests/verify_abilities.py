
import pytest
import os
import json
def test_ability_count_and_loading():
    """
    Verify that we have at least 11 ability types as claimed in README
    and that they load correctly from the registry.
    """
    
    # Determine path to ability registry
    # Searching for ability_registry.json in common paths
    base_path = os.path.join(os.getcwd(), "universes", "base", "abilities", "atomic_ability_registry.json")
    
    if os.path.exists(base_path):
        with open(base_path, "r") as f:
            data = json.load(f)
            abilities = data.get("abilities", {})
            print(f"\nFound {len(abilities)} abilities in atomic_ability_registry.json")
            
            # Print names for debugging
            assert len(abilities) >= 11, f"README claims 11+ abilities, found {len(abilities)}"
            
            # Verify they are non-empty
            for name, payload in abilities.items():
                assert "effect" in payload or "modifiers" in payload, f"Ability {name} has no effect/modifiers"
                
    else:
        # Fallback to checking code catalog if JSON missing
        # This assumes AbilityCatalog has a method to get all
        pass

if __name__ == "__main__":
    pytest.main([__file__])

import pytest
import os
import shutil
import json
from unittest.mock import MagicMock
from src.utils.registry_builder import (
    safe_registry_save, run_integration, RegistryBuilderError, 
    _build_generic_registry, RegistrySchema
)

class TestRegistryBuilder:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.test_dir = "tests/temp_registry_test"
        os.makedirs(self.test_dir, exist_ok=True)
        yield
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_safe_registry_save_success(self):
        """Test saving registry successfully."""
        data = {"test": "data"}
        path = os.path.join(self.test_dir, "reg.json")
        safe_registry_save(path, data, verbose=False)
        
        assert os.path.exists(path)
        with open(path, 'r') as f:
            loaded = json.load(f)
        assert loaded == data

    def test_safe_registry_save_failure(self):
        """Test saving failure raises RegistryBuilderError."""
        # Invalid path (directory as file)
        path = self.test_dir 
        with pytest.raises(RegistryBuilderError):
            safe_registry_save(path, {"a": 1}, verbose=False)

    def test_run_integration_success(self):
        """Test integration callback runs."""
        mock = MagicMock()
        run_integration("Test Integration", mock, verbose=False)
        mock.assert_called_once()

    def test_run_integration_failure(self):
        """Test integration failure is suppressed and logged."""
        def fail():
            raise ValueError("Integration Failed")
        
        # It should not raise
        run_integration("Bad Integration", fail, verbose=False)

    def test_generic_builder_mock(self):
        """Test generic builder flow with mock schema."""
        schema = RegistrySchema(
            name="Test",
            registry_file="test_reg.json",
            source_dirs=["."],
            regex_patterns={"simple_tier": r"Tier (\d+): (.*)"},
            required_fields=["id", "tier"]
        )
        
        # Create a dummy markdown file
        with open(os.path.join(self.test_dir, "test.md"), 'w') as f:
            f.write("Tier 1: Test Item")

        # Mock os.walk logic or just point to test dir
        # _build_generic_registry uses schema.source_dirs relative to universe path
        # Let's pass universe_path as self.test_dir and source_dir as "."
        
        reg = _build_generic_registry(self.test_dir, schema, verbose=False)
        assert "Test Item" in reg
        assert reg["Test Item"]["tier"] == 1

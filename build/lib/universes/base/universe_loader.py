import os
import json
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from .universe_config import UniverseConfig

class UniverseLoader:
    """
    Handles dynamic discovery, validation, and loading of universes.
    
    This class scan the 'universes/' directory for valid universe
    configurations and provides access to them.
    """
    
    def __init__(self, universes_root: Path):
        self.universes_root = Path(universes_root)
        self._cached_universes: Dict[str, UniverseConfig] = {}

    def discover_universes(self) -> List[str]:
        """Scans the universes directory for subdirectories containing config.json."""
        universes = []
        if not self.universes_root.is_dir():
            return universes
            
        for item in self.universes_root.iterdir():
            if item.is_dir() and (item / "config.json").exists():
                universes.append(item.name)
        return universes

    def load_universe(self, universe_name: str) -> UniverseConfig:
        """Loads a universe configuration by name."""
        if universe_name in self._cached_universes:
            return self._cached_universes[universe_name]
            
        universe_path = self.universes_root / universe_name
        config_file = universe_path / "config.json"
        
        if not config_file.exists():
            raise FileNotFoundError(f"Universe '{universe_name}' not found at {universe_path}")
            
        with open(config_file, "r") as f:
            data = json.load(f)
            
        # Ensure root is set correctly in config object
        data["root"] = str(universe_path)
        
        config = UniverseConfig.from_dict(data)
        self._cached_universes[universe_name] = config
        return config

    def validate_universe(self, universe_name: str) -> Tuple[bool, List[str]]:
        """
        Validates a universe configuration and its directory structure.
        
        Returns:
            Tuple[bool, List[str]]: (Success, List of error messages)
        """
        errors = []
        universe_path = self.universes_root / universe_name
        
        if not universe_path.is_dir():
            return False, [f"Directory {universe_path} does not exist"]
            
        # 1. Config existence and schema
        config_file = universe_path / "config.json"
        if not config_file.exists():
            errors.append("Missing config.json")
        else:
            success, schema_errors = self.validate_config_schema(config_file)
            errors.extend(schema_errors)
                
        # 2. Basic directory check
        try:
            config = self.load_universe(universe_name)
            if not config.validate_structure():
                errors.append("Missing required subdirectories (factions, infrastructure, technology)")
                
            # 3. Data Integrity check
            success, integrity_errors = self.validate_data_integrity(config)
            errors.extend(integrity_errors)

            # 4. Mixed Format Consistency Check
            success, format_errors = self.validate_mixed_format_consistency(config)
            errors.extend(format_errors)
            
        except Exception as e:
            errors.append(f"Failed to load universe: {str(e)}")
            
        return len(errors) == 0, errors

    def validate_config_schema(self, config_file: Path) -> Tuple[bool, List[str]]:
        """Validates config.json against the expected schema."""
        errors = []
        try:
            with open(config_file, "r") as f:
                data = json.load(f)
            
            required_fields = ["name", "version", "factions"]
            for field in required_fields:
                if field not in data:
                    errors.append(f"Missing required field in config.json: {field}")
            
            if "factions" in data and not isinstance(data["factions"], list):
                errors.append("'factions' must be a list in config.json")
                
        except json.JSONDecodeError:
            errors.append("Invalid JSON in config.json")
        return len(errors) == 0, errors

    def validate_data_integrity(self, config: UniverseConfig) -> Tuple[bool, List[str]]:
        """Checks for orphaned data files and verifies registry consistency."""
        errors = []
        
        # Check if factions listed in config actually exist
        try:
            with open(config.universe_root / "config.json", "r") as f:
                data = json.load(f)
                config_factions = data.get("factions", [])
        except:
            config_factions = []

        for faction in config_factions:
            faction_path = config.factions_dir / faction
            if not faction_path.is_dir():
                errors.append(f"Faction '{faction}' listed in config but directory not found at {faction_path}")

        # Check for essential registries
        for name, path in config.registry_paths.items():
            if not path.exists():
                errors.append(f"Missing {name} registry at {path}")

        # 4. Combat Rules Module Check
        try:
            with open(config.universe_root / "config.json", "r") as f:
                data = json.load(f)
                combat_rules_cfg = data.get("combat_rules", {})
                module_path_str = combat_rules_cfg.get("module")
                
                if module_path_str:
                    module_path = config.universe_root / module_path_str
                    if not module_path.exists():
                        errors.append(f"Combat rules module specified in config but not found at {module_path}")
                    elif not module_path_str.endswith(".py"):
                        errors.append(f"Combat rules module must be a .py file: {module_path_str}")
        except Exception as e:
            errors.append(f"Error validating combat rules: {str(e)}")

        if not config.translation_table_path.exists():
            errors.append(f"Missing translation_table.json at {config.translation_table_path}")

        return len(errors) == 0, errors

    def detect_unit_formats(self, config: UniverseConfig) -> Dict[str, List[str]]:
        """
        Scans faction directories and identifies which formats are present (XML, markdown, or both).
        """
        from src.utils.format_detector import FormatDetector
        formats_map = {}
        for faction in config.factions:
            faction_path = config.factions_dir / faction
            formats = FormatDetector.scan_faction_formats(faction_path)
            if formats:
                formats_map[faction] = formats
        return formats_map

    def validate_mixed_format_consistency(self, config: UniverseConfig) -> Tuple[bool, List[str]]:
        """
        Performs consistency checks for universes using hybrid formats.
        """
        errors = []
        formats_map = self.detect_unit_formats(config)
        
        # Note: Third-party universe-specific dependency validation has been removed.
        # To add custom universe dependency validation, add logic here.

        # 2. Check for Duplicate IDs and Missing Parser Data
        from src.utils.unit_parser import detect_file_format, parse_unit_file
        
        for faction in config.factions:
            faction_path = config.factions_dir / faction
            if not faction_path.is_dir(): continue
            
            unit_ids = set()
            
            for root, _, files in os.walk(faction_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        fmt = detect_file_format(file_path)
                    except ValueError:
                        continue # Skip non-unit files

                    if fmt == "markdown" and "template" not in file and "SPEC" not in file:
                        # Validate parser data existence
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        has_parser_data = "<!-- PARSER_DATA" in content or "## Parser Data" in content or "PARSER_DATA:{" in content
                        if not has_parser_data:
                            errors.append(f"Missing PARSER_DATA block in {file} ({faction})")
                        
                        # Check ID via parsing (lightweight check)
                        u = parse_unit_file(file_path, faction)
                        if u:
                            if u.name in unit_ids:
                                errors.append(f"Duplicate Unit Identifier '{u.name}' found in {file} ({faction})")
                            unit_ids.add(u.name)
                            
                    # elif fmt == "xml":
                    #      # XML parsing has been deprecated. Use Markdown sources.
                    #      pass
                    # Note: Third-party Stellaris parsing has been removed.
                    # To add custom universe parsing logic, add it here.

        return len(errors) == 0, errors

    def get_available_universes(self) -> Dict[str, UniverseConfig]:
        """Returns all valid, discoverable universes."""
        available = {}
        for name in self.discover_universes():
            success, _ = self.validate_universe(name)
            if success:
                available[name] = self.load_universe(name)
        return available

    def reload_universe(self, universe_name: str) -> UniverseConfig:
        """Clears cache and reloads a universe configuration."""
        if universe_name in self._cached_universes:
            del self._cached_universes[universe_name]
        return self.load_universe(universe_name)

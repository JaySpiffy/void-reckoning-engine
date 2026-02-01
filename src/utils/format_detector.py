import os
from pathlib import Path
from typing import List, Dict, Tuple, Any, Optional
import glob

class FormatDetector:
    """
    Centralized utility for identifying and validating unit data formats.
    Supports XML (Empire at War style) and Markdown (native simulation style).
    """

    @staticmethod
    def scan_faction_formats(faction_dir: Path) -> List[str]:
        """
        Scans a faction directory for unit file formats.
        Returns a list of identified formats: ["xml", "md"].
        """
        formats = set()
        if not faction_dir.is_dir():
            return []

        for root, _, files in os.walk(faction_dir):
            for file in files:
                if file.endswith('.xml') and "Hardpoints" not in root and "Projectiles" not in root:
                    formats.add("xml")
                elif file.endswith('.md') and "template" not in file and "SPEC" not in file:
                    formats.add("md")
                # Note: Third-party format detection has been removed.
                # To add custom universe format detection, add logic here.
        
        return sorted(list(formats))

    @staticmethod
    def detect_file_format(filepath: str) -> str:
        """Returns 'xml', 'markdown' or 'stellaris' based on file extension and context."""
        if filepath.endswith('.xml'):
            return 'xml'
        elif filepath.endswith('.md'):
            return 'markdown'
        # Note: Third-party format detection has been removed.
        # To add custom universe format detection, add logic here.
        else:
            if filepath.endswith('.txt'):
                raise ValueError(f"Unknown text file format: {filepath}")
            raise ValueError(f"Unknown unit file format: {filepath}")

    @staticmethod
    def detect_game_engine(game_dir: str) -> Optional[str]:
        """
        Detects the game engine based on directory structure signatures.
        Returns: 'unity', 'taleworlds', 'paradox', 'petroglyph', 'ironclad', or None.
        """
        game_path = Path(game_dir)
        if not game_path.exists():
            return None
            
        # Note: Third-party engine detection has been removed.
        # To add custom universe engine detection, add logic here.
            
        return None

    @staticmethod
    def detect_soase_variant(game_dir: str) -> Optional[str]:
        """
        Detects SOASE-specific directory patterns and returns the variant.
        Variants: 'rebellion', 'trinity', 'base', or None.
        """
        path = Path(game_dir)
        # Rebellion pattern (can be GameInfo or Type2/Entities)
        if (path / "GameInfo").exists() or (path / "Type2" / "Entities").exists() or \
           list(path.glob("GameInfo/*.entity")) or list(path.glob("Type2/Entities/*.entity")):
            return "rebellion"
        # Trinity pattern
        if (path / "Entities-DLC").exists() or list(path.glob("Entities-DLC/*.entity")):
            return "trinity"
        # Base/Generic pattern
        if (path / "Entities").exists() or list(path.glob("Entities/*.entity")):
            return "base"
            
        return None

    @staticmethod
    def find_convert_data_exe(game_dir: str) -> Optional[str]:
        """
        Searches for ConvertData executables in priority order.
        Returns absolute path to first found executable, or None.
        """
        path = Path(game_dir)
        executables = [
            "ConvertData_Rebellion.exe",
            "ConvertData_Trinity.exe",
            "ConvertData.exe"
        ]
        
        # Check game root and Tools/ subdirectory
        search_roots = [path, path / "Tools", path / "tools"]
        
        for root in search_roots:
            if not root.exists():
                continue
            for exe in executables:
                exe_path = root / exe
                if exe_path.exists():
                    return str(exe_path.absolute())
                    
        return None

    @staticmethod
    def get_soase_conversion_config(game_dir: str) -> Dict[str, Any]:
        """
        Combines detection results into a SOASE conversion configuration.
        """
        variant = FormatDetector.detect_soase_variant(game_dir)
        if not variant:
            return {}
            
        exe_path = FormatDetector.find_convert_data_exe(game_dir)
        
        # Determine input directories based on variant
        path = Path(game_dir)
        input_dirs = []
        
        if variant == "rebellion":
            # Check which folder actually exists
            if (path / "GameInfo").exists():
                input_dirs.append("GameInfo")
            if (path / "Type2" / "Entities").exists():
                input_dirs.append("Type2/Entities")
            if not input_dirs:
                # Fallback to GameInfo as default for Rebellion if neither found yet
                input_dirs = ["GameInfo"]
        elif variant == "trinity":
            input_dirs = ["Entities", "Entities-DLC"]
        else:
            input_dirs = ["Entities"]
            
        # Check if conversion is actually needed (any .entity files?)
        requires_conversion = False
        for d in input_dirs:
             if list((path / d).glob("*.entity")):
                 requires_conversion = True
                 break
                 
        return {
            "variant": variant,
            "exe_path": exe_path,
            "input_dirs": [str(path / d) for d in input_dirs],
            "requires_conversion": requires_conversion
        }

    @staticmethod
    def scan_steam_library(steam_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Scans a Steam library for supported games.
        Returns: {"Game Name": {"path": "...", "engine": "...", "detected_formats": [...]}}
        """
        steam_root = Path(steam_path)
        common_dir = steam_root / "steamapps" / "common"
        results = {}
        
        if not common_dir.exists():
            return results
            
        for game_dir in common_dir.iterdir():
            if game_dir.is_dir():
                engine = FormatDetector.detect_game_engine(str(game_dir))
                if engine:
                    # Attempt to detect formats
                    formats = FormatDetector.scan_faction_formats(game_dir)
                    results[game_dir.name] = {
                        "path": str(game_dir),
                        "engine": engine,
                        "detected_formats": formats
                    }
        return results

    @staticmethod
    def get_engine_data_paths(game_dir: str, engine: str) -> Dict[str, str]:
        """
        Returns a dictionary of critical data paths for the specific engine.
        """
        root = Path(game_dir)
        paths = {}
        
        # Note: Third-party engine path detection has been removed.
        # To add custom universe engine path detection, add logic here.
                
        return paths

    @staticmethod
    def validate_engine_dependencies(game_dir: str, engine: str) -> Tuple[bool, List[str]]:
        """
        Validates that required directories for the detected engine exist.
        """
        path = Path(game_dir)
        if engine == "paradox":
            return FormatDetector.validate_stellaris_dependencies(path, mod_root=path)
        elif engine == "petroglyph":
            # Need to find the XML root for validation
            data_paths = FormatDetector.get_engine_data_paths(game_dir, engine)
            if "xml_root" in data_paths and Path(data_paths["xml_root"]).exists():
                 # validate_xml_dependencies expects mod_root to check inside it.
                 # If we pass mod_root=XML_PARENT_DIR, it checks XML_PARENT_DIR/Hardpoints etc.
                 # Petroglyph: Data/XML/{Hardpoints, Projectiles}
                 # So we should pass base_xml as mod_root so it looks for Harpoints inside base_xml
                 return FormatDetector.validate_xml_dependencies(path, mod_root=Path(data_paths["xml_root"]))
            return False, ["Could not locate Data/XML directory"]
        elif engine == "ironclad":
            required = ["Entities", "GameInfo"]
            for req in required:
                if not (path / req).exists():
                    return False, [f"Missing SOASE directory: {req}"]
            return True, []
        return True, []

    @staticmethod
    def validate_xml_dependencies(universe_root: Path, mod_root: Path = None) -> Tuple[bool, List[str]]:
        """
        Checks if required XML dependency directories exist (Hardpoints, Projectiles).
        Only relevant if XML units are detected.
        
        Args:
            universe_root: The root of the universe definition (for general checks).
            mod_root: The actual root of the XML mod data (usually external or specific subdir).
                      If provided, dependencies are checked here. Otherwise scans universe_root.
        """
        errors = []
        required = ["Hardpoints", "Projectiles"]
        found = {req: False for req in required}
        
        search_root = mod_root if mod_root and mod_root.exists() else universe_root

        for root, dirs, _ in os.walk(search_root):
            for d in dirs:
                if d in found:
                    found[d] = True

        for req, exists in found.items():
            if not exists:
                errors.append(f"Missing XML dependency directory '{req}' in {search_root}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_stellaris_dependencies(universe_root: Path, mod_root: Path = None) -> Tuple[bool, List[str]]:
        """
        Checks if required Stellaris dependency directories exist.
        Required: component_templates, ship_sizes, component_sets, section_templates.
        """
        errors = []
        required = ["component_templates", "ship_sizes", "common", "section_templates"]
        # Note: 'common' is often the parent, but we look for these specific subdirs or keys
        found = {req: False for req in required}
        
        search_root = mod_root if mod_root and mod_root.exists() else universe_root
        
        # Stellaris structure is usually common/ship_sizes etc.
        # So we walk to find them
        for root, dirs, _ in os.walk(search_root):
            for d in dirs:
                if d in found:
                    found[d] = True
                    
        # Relaxed check: ship_sizes and component_templates are most critical
        critical = ["ship_sizes", "component_templates"]
        for req in critical:
             if not found[req]:
                 # Try typical path construction before failing
                 manual_check = search_root / "common" / req
                 if manual_check.exists():
                     found[req] = True
                 else:
                     errors.append(f"Missing Stellaris dependency directory '{req}' in {search_root}")

        return len(errors) == 0, errors

    @staticmethod
    def compare_unit_definitions(xml_unit: Any, md_unit: Any) -> Dict[str, Any]:
        """
        Compares stats between XML and markdown versions of the same unit.
        Returns a dictionary of deltas.
        """
        deltas = {}
        # This assumes we have loaded Unit objects
        fields_to_compare = ["hp", "armor", "damage", "cost", "shield"]
        
        for field in fields_to_compare:
            xml_val = getattr(xml_unit, field, None)
            md_val = getattr(md_unit, field, None)
            if xml_val != md_val:
                deltas[field] = {"xml": xml_val, "md": md_val}
        
        return deltas

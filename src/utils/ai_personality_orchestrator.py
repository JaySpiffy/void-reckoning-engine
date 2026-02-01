
import os
import json
import importlib.util
from typing import Dict, Any, List, Tuple
from src.utils.format_detector import FormatDetector
from src.utils.parser_registry import registry
from src.utils.ai_personality_generator import AIPersonalityGenerator
from src.utils.ai_personality_file_generator import AIPersonalityFileGenerator
from src.utils.diplomacy_extractor import DiplomacyExtractor
from src.utils.faction_quirk_mapper import FactionQuirkMapper

class AIPersonalityOrchestrator:
    """
    Orchestrates the AI personality extraction pipeline.
    Coordinating Parsing -> Processing -> Code Generation.
    """
    
    def __init__(self):
        self.detector = FormatDetector()
        self.generator = AIPersonalityGenerator()
        self.file_gen = AIPersonalityFileGenerator()
        self.quirk_mapper = FactionQuirkMapper()
        
    def extract_and_generate(self, game_dir: str, universe_name: str, engine_hint: str = None) -> Dict[str, Any]:
        """
        Main entry point for AI extraction.
        """
        print(f"Starting AI Extraction for {universe_name}...")
        
        # 1. Detect Engine
        engine = engine_hint
        if not engine:
             # detect_game_engine returns string ID, not dict
             engine = self.detector.detect_game_engine(game_dir) or "unknown"
        
        # 2. Get Extractor
        try:
            extractor = registry.get_ai_extractor(engine, game_dir)
            print(f"Using {type(extractor).__name__} for {engine} engine.")
        except Exception as e:
            print(f"Warning: {e}. Falling back to Generic extraction.")
            extractor = None

        # 3. Extract Raw Data
        # Note: Third-party-specific extraction logic (Stellaris, EaW) has been removed.
        # To add custom universe-specific extraction, add logic here.
        parsed_personalities = {}
        raw_diplomacy = {}
        faction_entries = {}
        
        if extractor:
            # Use generic extraction for custom universes
            if hasattr(extractor, 'parse_ai_personalities'):
                parsed_personalities = extractor.parse_ai_personalities()
            if hasattr(extractor, 'generate_faction_entries'):
                faction_entries = extractor.generate_faction_entries()

        # 4. Diplomacy Extraction
        # Note: Third-party diplomacy extraction has been removed.
        # To add custom universe-specific diplomacy extraction, add logic here.
        diplo_extractor = DiplomacyExtractor(game_dir)
        # Use generic diplomacy extraction for custom universes
        if hasattr(diplo_extractor, 'extract_generic_diplomacy'):
            raw_diplomacy = diplo_extractor.extract_generic_diplomacy()
            
        # 5. Generate Personalities
        final_personalities = {}
        combat_doctrines = {}
        
        # Main Generation Loop - Generic for custom universes
        # If we have faction entries, drive by faction_id to ensure full quirk linkage
        if faction_entries:
            for f_id, f_data in faction_entries.items():
                p_key = f_data.get("personality_id")
                if not p_key or p_key not in parsed_personalities:
                    continue # Skip factions without valid mapped personalities
                    
                p_data = parsed_personalities[p_key]
                
                # Consolidate Quirks: Faction Entry + Mapper
                entry_quirks = f_data.get("quirks", {})
                behaviors = p_data.get("behaviour", {})
                
                # Use generic quirk mapping
                b_quirks = self.quirk_mapper.merge_quirks({}, {}, entry_quirks)
                final_quirks = b_quirks

                wrapped_data = {
                    "ai_personality": p_data,
                    "quirks": final_quirks,
                    "ethics": f_data.get("ethics", [])
                }
                
                # Generate using generic method
                p_obj = self.generator.generate_from_generic(f_id, wrapped_data)
                final_personalities[f_id] = p_obj
                
        else:
            # Legacy/Fallback Loop (Personalities only)
            iterate_source = parsed_personalities
            
            for p_id, p_data in iterate_source.items():
                # Use generic generation for custom universes
                wrapped_data = {
                    "ai_personality": p_data,
                    "quirks": self.quirk_mapper.merge_quirks({}, {}, p_data.get("quirks", {})),
                    "ethics": p_data.get("ethics", [])
                }
                p_obj = self.generator.generate_from_generic(p_id, wrapped_data)
                final_personalities[p_id] = p_obj

            # Doctrines Collection
            if p_obj.combat_doctrine:
                pass

        # Generate Definitions for Doctrines
        combat_doctrines = self.file_gen.generate_combat_doctrines(list(final_personalities.values()))

        # 6. Write Files
        output_dir = os.path.join(os.getcwd(), "universes", universe_name)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            
        # ai_personalities.py
        code = self.file_gen.generate_personality_module(universe_name, final_personalities, combat_doctrines)
        self.file_gen.write_to_file(output_dir, code)
        
        # diplomacy_rules.json
        dr_path = os.path.join(output_dir, "diplomacy_rules.json")
        with open(dr_path, 'w', encoding='utf-8') as f:
            json.dump(raw_diplomacy, f, indent=2)
            
        # parsed_ai_data.json (for registry builder)
        ai_data_path = os.path.join(output_dir, "parsed_ai_data.json")
        encoded_parsed = {}
        for fid, pid in final_personalities.items():
            # Convert object to dict for JSON
            p_dict = pid.to_dict() if hasattr(pid, 'to_dict') else pid.__dict__.copy()
            # Ensure quirks are top-level accessible for RegistryBuilder logic if needed
            # RegistryBuilder expects { 'quirks': ... } which is in p_dict['quirks']
            encoded_parsed[fid] = p_dict
            
        with open(ai_data_path, 'w', encoding='utf-8') as f:
            json.dump(encoded_parsed, f, indent=2)
        
        return {
            "count": len(final_personalities),
            "engine": engine,
            "output": output_dir
        }

    def validate_generated_personalities(self, universe_name: str) -> Tuple[bool, List[str]]:
        """
        Validates that the generated module is importable and follows protocol.
        """
        module_path = os.path.join(os.getcwd(), "universes", universe_name, "ai_personalities.py")
        if not os.path.exists(module_path):
            return False, ["File not found"]
            
        try:
            spec = importlib.util.spec_from_file_location(f"{universe_name}.ai_personalities", module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Check Protocol
            if not hasattr(module, "get_personality"): return False, ["Missing get_personality"]
            if not hasattr(module, "get_all_personalities"): return False, ["Missing get_all_personalities"]
            
            return True, []
        except Exception as e:
            return False, [str(e)]

from typing import Dict, Type, List, Optional, Any

class ParserRegistry:
    """
    Singleton registry for game engine parsers.
    Manages detection, instantiation, and metadata for supported game engines.
    """
    _instance = None

    def __init__(self):
        if ParserRegistry._instance is not None:
            raise Exception("This class is a singleton!")
        self._parsers: Dict[str, Type] = {}
        self._parser_instances: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict] = {}
        ParserRegistry._instance = self

    @staticmethod
    def get_instance():
        if ParserRegistry._instance is None:
            ParserRegistry()
        return ParserRegistry._instance

    def register_parser(self, engine: str, parser_class: Type, metadata: Dict):
        """
        Register a parser class for a specific game engine.

        Args:
            engine: Unique identifier (e.g., 'petroglyph', 'paradox')
            parser_class: Class reference for the parser
            metadata: Config dict containing 'supported_formats', 'required_directories',
                      'data_paths', 'importer_module', 'importer_class', etc.
        """
        self._parsers[engine] = parser_class
        self._metadata[engine] = metadata

    def get_parser(self, engine: str, mod_root: str) -> Any:
        """
        Get an instantiated parser for the given engine and mod root.
        Uses caching to avoid re-instantiating for the same mod_root.
        """
        cache_key = f"{engine}:{mod_root}"
        if cache_key in self._parser_instances:
            return self._parser_instances[cache_key]

        if engine not in self._parsers:
            raise ValueError(f"No parser registered for engine: {engine}")

        parser_cls = self._parsers[engine]
        # Most parsers expect mod_root as first argument
        instance = parser_cls(mod_root)
        self._parser_instances[cache_key] = instance
        return instance

    def get_parser_class(self, engine: str) -> Type:
        if engine not in self._parsers:
             raise ValueError(f"No parser registered for engine: {engine}")
        return self._parsers[engine]

    def get_ai_extractor(self, engine: str, mod_root: str) -> Any:
        """
        Returns an instantiated AI extractor for the given engine.
        """
        meta = self.get_metadata(engine)
        extractor_cls = meta.get("ai_extractor_class")

        if not extractor_cls:
            raise ValueError(f"No AI extractor defined for engine: {engine}")

        return extractor_cls(mod_root)

    def get_metadata(self, engine: str) -> Dict:
        return self._metadata.get(engine, {})

    def list_registered_parsers(self) -> List[str]:
        return list(self._parsers.keys())

    def validate_parser(self, engine: str, mod_root: str) -> bool:
        """
        Checks if the mod_root is valid for the given engine using registered metadata.
        This provides a basic check; stricter validation happens in FormatDetector.
        """
        # This can be expanded to use metadata['required_directories'] check if needed here,
        # but FormatDetector.validate_engine_dependencies handles that.
        return engine in self._parsers

# Auto-registration
# We access the singleton instance directly
registry = ParserRegistry.get_instance()

# Note: Third-party parser registrations have been removed.
# To add custom universe parsers, register them here following the pattern:
# registry.register_parser("engine_name", ParserClass, {
#     "supported_formats": [".ext"],
#     "required_directories": ["dir1", "dir2"],
#     "data_paths": {...},
#     "importer_module": "tools.custom_importer",
#     "importer_class": "CustomImporter",
#     "supports_ai_extraction": True/False,
#     "ai_extractor_class": OptionalAIExtractorClass
# })

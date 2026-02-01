from pydantic import BaseModel, Field, validator, root_validator
from typing import Dict, Any, Optional, List, Union, Tuple
import multiprocessing
from collections import defaultdict
import src.core.config as config_module
from universes.base.universe_loader import UniverseLoader

class GameConfig(BaseModel):
    """
    Central configuration object for the campaign simulation.
    Replaces loose dictionaries with typed parameters.
    """
    max_turns: int = Field(50, gt=0)
    num_systems: int = Field(20, gt=0)
    min_planets_per_system: int = Field(1, gt=0)
    max_planets_per_system: int = Field(5, gt=0)
    starting_fleets: int = Field(1, ge=0)
    base_requisition: int = Field(2500, ge=0)
    
    # Game Balance (Item 8.2)
    colonization_cost: int = Field(1000, ge=0)
    max_fleet_size: int = Field(20, gt=0)
    max_build_time: int = Field(5, gt=0)
    max_build_time: int = Field(5, gt=0)
    victory_planet_threshold: int = Field(10, gt=0)
    tech_cost_multiplier: float = Field(5.0, gt=0.0)
    
    diplomacy_enabled: bool = True
    fow_enabled: bool = True
    
    # Performance
    performance_logging_level: str = "summary"
    performance_log_interval: int = 10
    performance_profile_methods: bool = True
    
    raw_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Unification: Paths (Runtime populated)
    paths: Dict[str, str] = Field(default_factory=dict)
    
    # PPS (Persistent Procedural Sandbox) Configuration
    sandbox_mode: bool = False
    procedural_faction_limit: int = Field(5, ge=0)

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_dict(cls, data: Optional[Dict[str, Any]]) -> Union['GameConfig', 'MultiUniverseConfig']:
        """
        Creates a GameConfig instance from a nested dictionary structure.
        Maps 'campaign', 'economy', 'mechanics' sections to flat attributes.
        """
        if not data:
            return cls()
            
        mode = data.get("mode", "single")
        if mode == "multi":
            return MultiUniverseConfig.from_dict(data)
            
        # Defaults
        params = {}
        
        # logical mapping
        if "campaign" in data:
            c = data["campaign"]
            if "turns" in c: params["max_turns"] = c["turns"]
            if "num_systems" in c: params["num_systems"] = c["num_systems"]
            if "min_planets" in c: params["min_planets_per_system"] = c["min_planets"]
            if "max_planets" in c: params["max_planets_per_system"] = c["max_planets"]
            
        if "economy" in data:
            e = data["economy"]
            if "base_income_req" in e: params["base_requisition"] = e["base_income_req"]
            
        if "mechanics" in data:
            m = data["mechanics"]
            if "enable_diplomacy" in m: params["diplomacy_enabled"] = m["enable_diplomacy"]
            if "enable_weather" in m: params["fow_enabled"] = m.get("enable_weather", True) # heuristics
            
        if "units" in data:
            u = data["units"]
            if "max_fleet_size" in u: params["max_fleet_size"] = u["max_fleet_size"]
            # Map max_land_army_size if we decide to add it as a field later, but for now max_fleet_size is critical
            
        if "performance" in data:
            p = data["performance"]
            if "logging_level" in p: params["performance_logging_level"] = p["logging_level"]
            if "log_interval" in p: params["performance_log_interval"] = p["log_interval"]
            if "profile_methods" in p: params["performance_profile_methods"] = p["profile_methods"]
            
        # PPS Sandbox Mode Configuration
        if "sandbox_mode" in data:
            params["sandbox_mode"] = data["sandbox_mode"]
        if "procedural_faction_limit" in data:
            params["procedural_faction_limit"] = data["procedural_faction_limit"]
            
        # Fallback for flat keys (CLI overrides)
        # Handle Pydantic V1/V2 differences safely with lazy evaluation to avoid warnings
        fields_dict = getattr(cls, "model_fields", None)
        if fields_dict is None:
            fields_dict = getattr(cls, "__fields__", {})
            
        for k in fields_dict.keys():
            if k in data:
                params[k] = data[k]

        # Preserve raw
        params["raw_config"] = data
        
        return cls(**params)

    def is_sandbox_mode(self) -> bool:
        """
        Returns whether sandbox mode is enabled.
        Sandbox mode allows procedural faction generation and testing.
        """
        return self.sandbox_mode

    def get_procedural_faction_limit(self) -> int:
        """
        Returns the maximum number of procedural factions allowed.
        Used in sandbox mode to limit faction generation.
        """
        return self.procedural_faction_limit

class UniverseInstanceConfig(BaseModel):
    """Configuration for a single universe instance in multi-universe mode."""
    name: str = ""
    enabled: bool = True
    processor_affinity: List[int] = Field(default_factory=list)
    num_runs: int = Field(1, gt=0)
    game_config: Dict[str, Any] = Field(default_factory=dict)

class MultiUniverseConfig(BaseModel):
    """Configuration for multi-universe parallel execution."""
    mode: str = "single"  # "single" or "multi"
    active_universe: str = "void_reckoning"
    universes: List[UniverseInstanceConfig] = Field(default_factory=list)
    sync_turns: bool = False
    cross_universe_events: bool = False
    aggregate_reports: bool = True
    
    # PPS (Persistent Procedural Sandbox) Configuration
    sandbox_mode: bool = False
    procedural_faction_limit: int = Field(5, ge=0)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MultiUniverseConfig':
        """Parse simulation_config.json into MultiUniverseConfig."""
        if not data:
            return cls()
            
        mode = data.get("mode", "single")
        
        if mode == "single":
            # Wrap single universe as a multi-config with one entry? 
            # Or just return a minimal MultiUniverseConfig that indicates single mode.
            # The plan says: "If 'single': return single universe config wrapped..."
            # For backward compatibility, the caller should check mode.
            return cls(mode="single", active_universe=data.get("active_universe", "void_reckoning"))
            
        # Multi Mode
        universes_data = data.get("universes", [])
        uni_configs = []
        
        for u_data in universes_data:
            # Merge base config with overrides
            merged_game_config = merge_universe_config(data, u_data)
            
            # Use specific num_runs if present, else fallback to global simulation settings (or default)
            # logic: simulation.num_runs -> universe.num_runs override
            runs = u_data.get("num_runs", data.get("simulation", {}).get("num_runs", 1))
            
            uni_configs.append(UniverseInstanceConfig(
                name=u_data.get("name", ""),
                enabled=u_data.get("enabled", True),
                processor_affinity=u_data.get("processor_affinity", []),
                num_runs=runs,
                game_config=merged_game_config
            ))
            
        multi_settings = data.get("multi_universe_settings", {})
        
        # PPS Sandbox Mode Configuration
        sandbox_mode = data.get("sandbox_mode", False)
        procedural_faction_limit = data.get("procedural_faction_limit", 5)
        
        config = cls(
            mode="multi",
            universes=uni_configs,
            sync_turns=multi_settings.get("sync_turns", False),
            cross_universe_events=multi_settings.get("cross_universe_events", False),
            aggregate_reports=multi_settings.get("aggregate_reports", True),
            sandbox_mode=sandbox_mode,
            procedural_faction_limit=procedural_faction_limit
        )
        
        # Validation Hook as requested
        is_valid, errors = validate_multi_universe_config(config)
        if not is_valid:
            error_msg = "\n".join(errors)
            raise ValueError(f"Invalid Multi-Universe Configuration:\n{error_msg}")
            
        return config

    def to_runner_configs(self) -> List[Dict[str, Any]]:
        """
        Converts MultiUniverseConfig to format expected by MultiUniverseRunner.
        Returns list of dicts with keys: universe_name, processor_affinity, num_runs, game_config
        """
        runner_configs = []
        
        for uni_config in self.universes:
            if not uni_config.enabled:
                continue
                
            runner_configs.append({
                "universe_name": uni_config.name,
                "processor_affinity": uni_config.processor_affinity,
                "num_runs": uni_config.num_runs,
                "game_config": uni_config.game_config
            })
        
        return runner_configs

    def is_sandbox_mode(self) -> bool:
        """
        Returns whether sandbox mode is enabled.
        Sandbox mode allows procedural faction generation and testing.
        """
        return self.sandbox_mode

    def get_procedural_faction_limit(self) -> int:
        """
        Returns the maximum number of procedural factions allowed.
        Used in sandbox mode to limit faction generation.
        """
        return self.procedural_faction_limit

def merge_universe_config(base_config: Dict[str, Any], universe_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges base configuration with universe-specific overrides.
    Universe-specific settings take precedence.
    """
    merged = {}
    
    # Copy base sections
    for section in ["simulation", "campaign", "economy", "units", "mechanics", "performance", "reporting", "multi_universe_settings"]:
        if section in base_config:
            merged[section] = base_config[section].copy()
    
    # Override with universe-specific settings
    # Expanding to include simulation, performance, reporting as per verification comment
    for section in ["campaign", "economy", "units", "mechanics", "simulation", "performance", "reporting"]:
        if section in universe_config:
            if section not in merged:
                merged[section] = {}
            # Deep merge could be better, but single-level update is standard behavior here
            merged[section].update(universe_config[section])
            
    return merged

def validate_multi_universe_config(config: MultiUniverseConfig) -> Tuple[bool, List[str]]:
    """
    Validates multi-universe configuration.
    Returns: (is_valid, list_of_errors)
    """
    errors = []
    
    # 1. Check universe existence
    try:
        loader = UniverseLoader(config_module.UNIVERSE_ROOT)
        available = loader.discover_universes()
    except Exception as e:
        return False, [f"Failed to load universe definitions: {e}"]
    
    for uni_config in config.universes:
        if not uni_config.enabled:
            continue
        if uni_config.name not in available:
            errors.append(f"Universe '{uni_config.name}' not found")
    
    # 2. Check processor affinity conflicts
    affinity_map = defaultdict(list)
    for uni_config in config.universes:
        if not uni_config.enabled:
            continue
        for core in uni_config.processor_affinity:
            affinity_map[core].append(uni_config.name)
    
    for core, universes in affinity_map.items():
        if len(universes) > 1:
            errors.append(f"Core {core} assigned to multiple universes: {universes}")
    
    # 3. Check processor affinity range
    try:
        cpu_count = multiprocessing.cpu_count()
        for uni_config in config.universes:
            if not uni_config.enabled: continue
            for core in uni_config.processor_affinity:
                if core >= cpu_count or core < 0:
                    errors.append(f"Invalid core ID {core} for universe '{uni_config.name}' (system has {cpu_count} cores)")
    except Exception:
        pass # Skip hardware check if CPU count undeterminable
    
    # 4. Check configuration completeness
    for uni_config in config.universes:
        if not uni_config.enabled: continue
        if not uni_config.name:
            errors.append("Universe configuration missing 'name' field")
        if uni_config.num_runs < 1:
            errors.append(f"Universe '{uni_config.name}' has invalid num_runs: {uni_config.num_runs}")
    
    return len(errors) == 0, errors

# Monkey-patch GameConfig.from_dict to delegate?
# Or just use a free function factory?
# For now, let's keep GameConfig focused on single runs and handle Multi at a higher level (CLI/Runner).

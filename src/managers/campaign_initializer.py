from typing import Dict, Any, Optional, Union
import os
import time

from src.core.config import REPORTS_DIR, ACTIVE_UNIVERSE, set_active_universe, get_universe_config
from src.core.universe_data import UniverseDataManager
from src.core.game_config import GameConfig
from src.core.constants import MAX_COMBAT_ROUNDS, MAX_LAND_UNITS
from src.utils.game_logging import GameLogger, LogCategory
from src.core import gpu_utils

# Managers
from src.managers.galaxy_state_manager import GalaxyStateManager
from src.managers.faction_manager import FactionManager
from src.models.faction import Faction
from src.repositories.faction_repository import FactionRepository
from src.repositories.planet_repository import PlanetRepository
from src.repositories.system_repository import SystemRepository
from src.repositories.fleet_repository import FleetRepository
from src.repositories.unit_repository import UnitRepository
from src.core.service_locator import ServiceLocator
from src.managers.fleet_manager import FleetManager
from src.managers.economy_manager import EconomyManager
from src.managers.battle_manager import BattleManager
from src.managers.tech_manager import TechManager
from src.managers.asset_manager import AssetManager
from src.managers.intelligence_manager import IntelligenceManager
from src.managers.cache_manager import CacheManager
from src.services.pathfinding_service import PathfindingService
from src.managers.portal_manager import PortalManager
from src.services.construction_service import ConstructionService
from src.reporting.faction_reporter import FactionReporter
from src.reporting.telemetry import TelemetryCollector, EventCategory
from src.services.distance_matrix import DistanceMatrixService

# AI & Mechanics
from src.ai.strategies.standard import StandardStrategy, init_ai_rng
from src.managers.galaxy_generator import GalaxyGenerator, init_galaxy_rng
from src.managers.weather_manager import FluxStormManager
from src.managers.ai_manager import StrategicAI
from src.mechanics.faction_mechanics_engine import FactionMechanicsEngine

class CampaignInitializer:
    """
    Handles the complex initialization and dependency injection for the CampaignEngine.
    Extracts the 'God Class' setup logic from the main engine file.
    """
    
    def __init__(self, engine, battle_log_dir: Optional[str] = None, game_config: Optional[Union[Dict[str, Any], GameConfig]] = None, report_organizer: Optional[object] = None, universe_name: Optional[str] = None, telemetry_collector: Optional[object] = None, manager_overrides: Optional[Dict[str, Any]] = None):
        self.engine = engine
        self.battle_log_dir = battle_log_dir
        self.raw_config = game_config
        self.report_organizer = report_organizer
        self.universe_name = universe_name
        self.telemetry_collector = telemetry_collector
        self.manager_overrides = manager_overrides or {}
        
    def initialize(self):
        """Main entry point for initialization sequence."""
        self._setup_universe_context()
        self._setup_logging()
        self._setup_configuration()
        self._setup_state_managers()
        self._setup_core_managers()
        self._setup_sub_managers()
        self._setup_strategies_and_mechanics()
        self._setup_services()
        
        # [ORDER FIX] Template support must run AFTER all blueprints and managers are ready
        self._setup_template_support()
        
        self._finalize_telemetry()
        
    def _setup_universe_context(self):
        universe = self.universe_name or ACTIVE_UNIVERSE or "void_reckoning"
        set_active_universe(universe)
        self.engine.universe_config = get_universe_config(universe)
        self.engine.universe_data = UniverseDataManager.get_instance()
        self.engine.universe_data.load_universe_data(universe)
        
    def _setup_logging(self):
        log_dir = os.path.join(REPORTS_DIR, "logs")
        if self.report_organizer and hasattr(self.report_organizer, 'run_path'):
            log_dir = self.report_organizer.run_path
            
        self.engine.logger = GameLogger(log_dir=log_dir)
        self.engine.logger.info("CampaignEngine Initializing via CampaignInitializer...")
        
        # [GPU PROBE]
        if gpu_utils.is_available():
            self.engine.logger.info(f"[GPU PROBE] Acceleration ENABLED. Backend: {gpu_utils.get_xp().__name__}")
        else:
            self.engine.logger.warning("[GPU PROBE] Acceleration DISABLED. Backend: NumPy (CPU)")
        
        if self.report_organizer and hasattr(self.report_organizer, 'logger'):
            self.report_organizer.logger = self.engine.logger

    def _setup_configuration(self):
        if isinstance(self.raw_config, GameConfig):
            self.engine.config = self.raw_config
        else:
            self.engine.config = GameConfig.from_dict(self.raw_config)
            
        # [GPU CONFIG] Apply manual overrides from JSON
        gpu_conf = self.engine.config.raw_config.get("gpu")
        if gpu_conf:
            gpu_utils.apply_gpu_config(gpu_conf)
            
        # Constants
        self.engine.max_combat_rounds = MAX_COMBAT_ROUNDS
        self.engine.max_fleet_size = self.engine.config.max_fleet_size
        self.engine.max_land_units = MAX_LAND_UNITS
        self.engine.colony_cost = self.engine.config.colonization_cost
        
        self.engine.turn_counter = 0
        self.engine.report_organizer = self.report_organizer
        self.engine.game_config = self.engine.config.raw_config
        
        # Path Injection
        if self.engine.universe_config:
            self.engine.config.paths["tech"] = str(self.engine.universe_config.technology_dir)
            self.engine.config.paths["factions"] = str(self.engine.universe_config.factions_dir)
            self.engine.config.paths["units"] = str(self.engine.universe_config.units_dir)
            self.engine.config.paths["infra"] = str(self.engine.universe_config.infrastructure_dir)
            
        # RNG
        base_seed = self.engine.game_config.get("simulation", {}).get("random_seed")
        if base_seed is not None:
            init_ai_rng(base_seed)
            init_galaxy_rng(base_seed)

    def _setup_state_managers(self):
        # Initialize Repositories
        faction_repo = FactionRepository()
        planet_repo = PlanetRepository()
        system_repo = SystemRepository()
        fleet_repo = FleetRepository()
        unit_repo = UnitRepository()
        
        # Register in ServiceLocator
        ServiceLocator.register("FactionRepository", faction_repo)
        ServiceLocator.register("PlanetRepository", planet_repo)
        ServiceLocator.register("SystemRepository", system_repo)
        ServiceLocator.register("FleetRepository", fleet_repo)
        ServiceLocator.register("UnitRepository", unit_repo)
        
        # Legacy Managers (Now using repositories under the hood - Phase 7)
        self.engine.galaxy_manager = self.manager_overrides.get("galaxy_manager") or GalaxyStateManager(self.engine.universe_data, self.engine.logger)
        self.engine.faction_manager = self.manager_overrides.get("faction_manager") or FactionManager(self.engine.logger)
        self.engine.fleet_manager = self.manager_overrides.get("fleet_manager") or FleetManager(self.engine)
        
        # [FIX] Populate Factions from Universe Data with Multi-Instance Support (User Request: "Mayhem")
        f_list = self.engine.universe_data.get_factions()
        
        # Determine multiplier (Default 1, but user asked for 30 factions from ~10 templates)
        # We can look for a config "faction_instances" or default to 1.
        # Given the explicit request for "mayhem", we'll implement a scaling factor.
        instance_count = self.engine.game_config.get("simulation", {}).get("faction_instances", 1)
        
        # Override for "Grand Strategy" feel if not specified
        if instance_count == 1 and self.engine.game_config.get("simulation", {}).get("enable_mayhem", False):
            instance_count = 3
            
        if f_list:
            for f_name_base in f_list:
                for i in range(instance_count):
                    # Naming: "Hegemony", "Hegemony (2)", "Hegemony (3)"
                    if instance_count > 1:
                        f_name = f"{f_name_base} {i+1}"
                        # Preserve base ID for blueprint lookups logic (handled via Faction object or lookups)
                        # We need to ensure Faction object knows its "Template ID"
                    else:
                        f_name = f_name_base
                        
                    if f_name not in self.engine.faction_manager.factions:
                        # Pass Base Name/Template ID if Faction supports it (not yet, but we can rely on string parsing)
                        # Actual fix: Faction init takes name. We need to handle blueprint/personality lookups for "Hegemony 2"
                        # to use "Hegemony" data.
                        start_funds = self.engine.game_config.get("economy", {}).get("starting_requisition", 5000)
                        new_f = Faction(f_name, logger=self.engine.logger, initial_req=start_funds)
                        
                        # Hack: Inject "template_id" for lookups
                        new_f.template_id = f_name_base
                        
                        self.engine.faction_manager.register_faction(new_f)
                        
            self.engine.logger.info(f"Initialized {len(self.engine.faction_manager.factions)} factions (Instances: {instance_count}) from UniverseData.")
            
        # Proxies
        self.engine._systems_proxy = []

    def _setup_template_support(self):
        """
        Ensures that cloned factions (e.g. 'Hegemony 2') can access 'Hegemony' blueprints/techs.
        """
        # 1. Duplicate Unit Blueprints
        if hasattr(self.engine, 'unit_blueprints'):
            new_keys = {}
            for f_key, bps in self.engine.unit_blueprints.items():
                for reg_f in self.engine.faction_manager.factions.values():
                    if getattr(reg_f, 'template_id', '') == f_key and reg_f.name != f_key:
                        new_keys[reg_f.name] = bps
            self.engine.unit_blueprints.update(new_keys)
            
        # 2. Duplicate Army/Navy maps
        if hasattr(self.engine, 'navy_blueprints'):
            new_keys = {}
            for f_key, bps in self.engine.navy_blueprints.items():
                for reg_f in self.engine.faction_manager.factions.values():
                    if getattr(reg_f, 'template_id', '') == f_key and reg_f.name != f_key:
                        new_keys[reg_f.name] = bps
            self.engine.navy_blueprints.update(new_keys)
            
        if hasattr(self.engine, 'army_blueprints'):
            new_keys = {}
            for f_key, bps in self.engine.army_blueprints.items():
                for reg_f in self.engine.faction_manager.factions.values():
                    if getattr(reg_f, 'template_id', '') == f_key and reg_f.name != f_key:
                        new_keys[reg_f.name] = bps
            self.engine.army_blueprints.update(new_keys)
            
        # 3. Duplicate Tech Trees (TechManager)
        if hasattr(self.engine, 'tech_manager') and hasattr(self.engine.tech_manager, 'faction_tech_trees'):
            new_trees = {}
            for f_key, tree in self.engine.tech_manager.faction_tech_trees.items():
                for reg_f in self.engine.faction_manager.factions.values():
                    if getattr(reg_f, 'template_id', '').lower() == f_key and reg_f.name.lower() != f_key:
                        new_trees[reg_f.name.lower()] = tree
            self.engine.tech_manager.faction_tech_trees.update(new_trees)

    def _setup_core_managers(self):
        # Economy
        self.engine.economy_manager = self.manager_overrides.get("economy_manager") or EconomyManager(self.engine)
        
        # Battle & Logging
        eff_battle_log_dir = self.battle_log_dir
        if self.report_organizer:
            eff_battle_log_dir = os.path.join(self.report_organizer.run_path, "battles")
            os.makedirs(eff_battle_log_dir, exist_ok=True)

        self.engine.battle_manager = self.manager_overrides.get("battle_manager") or BattleManager(self.engine, eff_battle_log_dir)
        self.engine.battle_log_dir = eff_battle_log_dir
        
        # Tech
        tech_dir_path = self.engine.config.paths.get("tech")
        self.engine.tech_manager = self.manager_overrides.get("tech_manager") or TechManager(tech_dir=tech_dir_path, game_config=self.engine.config)
        
        # Apply Procedural Evolution (Self-Evolving Tech Trees)
        if self.engine.game_config.get("simulation", {}).get("enable_tech_evolution", True):
            self.engine.tech_manager.apply_procedural_evolution(
                self.engine.universe_config.name
            )

        # Asset & Intel
        self.engine.asset_manager = self.manager_overrides.get("asset_manager") or AssetManager(self.engine)
        self.engine.intel_manager = self.manager_overrides.get("intel_manager") or IntelligenceManager(self.engine)
        self.engine.intelligence_manager = self.engine.intel_manager # Alias

    def _setup_sub_managers(self):
        self.engine.galaxy_generator = GalaxyGenerator()
        self.engine.galaxy_generator.load_points_db()
        self.engine.galaxy_generator.load_blueprints()
        
        # [FIX] Link loaded blueprints to engine
        self.engine.unit_blueprints = self.engine.galaxy_generator.unit_blueprints
        self.engine.navy_blueprints = self.engine.galaxy_generator.navy_blueprints
        self.engine.army_blueprints = self.engine.galaxy_generator.army_blueprints
        
        self.engine.cache_manager = CacheManager(self.engine.logger)
        self.engine.faction_reporter = FactionReporter(self.engine)
        
        # Telemetry
        tele_dir = os.path.join(REPORTS_DIR, "telemetry")
        verbosity = self.engine.config.raw_config.get("simulation", {}).get("telemetry_level", "summary")
        if self.report_organizer and hasattr(self.report_organizer, 'run_path'):
            tele_dir = os.path.join(self.report_organizer.run_path, "telemetry")
            
        if self.telemetry_collector:
            self.engine.telemetry = self.telemetry_collector
        else:
            self.engine.telemetry = TelemetryCollector(tele_dir, verbosity=verbosity, universe_name=self.engine.universe_config.name, logger=self.engine.logger)

    def _setup_services(self):
        from src.services.ship_design_service import ShipDesignService
        self.engine.pathfinder = PathfindingService()
        
        # R10: Strategic Distance Matrix
        self.engine.distance_matrix = DistanceMatrixService(self.engine)
        self.engine.pathfinder.set_distance_service(self.engine.distance_matrix)
        
        self.engine.portal_manager = PortalManager(self.engine)
        self.engine.construction_service = ConstructionService(self.engine)
        self.engine.design_service = ShipDesignService(self.engine.ai_manager)
        
        # Blueprints & DB
        # unit_blueprints, navy_blueprints, army_blueprints are now populated in _setup_sub_managers
        self.engine.points_db = {}
        self.engine.planets_by_faction = {}
        
        # Caches
        self.engine.profiling_stats = {}
        self.engine.performance_metrics = {
            'visibility_time': [], 'targeting_time': [], 'threat_calc_time': [],
            'ai_strategy_time': [], 'economy_phase_total': [], 'total_turn_time': []
        }

    def _setup_strategies_and_mechanics(self):
        # AI
        self.engine.default_strategy = StandardStrategy()
        self.engine.strategies = {}
        self.engine.strategic_ai = self.manager_overrides.get("strategic_ai") or StrategicAI(self.engine)
        self.engine.ai_manager = self.engine.strategic_ai # [ALIAS] For legacy/shared access
        self.engine.strategic_ai.load_personalities(self.engine.universe_config.name)
        
        # Mechanics
        mechanics = self.engine.game_config.get("mechanics", {})
        if mechanics.get("enable_diplomacy", True):
            from src.managers.diplomacy_manager import DiplomacyManager
            self.engine.diplomacy = self.manager_overrides.get("diplomacy_manager") or \
                DiplomacyManager(self.engine.faction_manager.get_faction_names(), self.engine)
        else:
            self.engine.diplomacy = None
            
        self.engine.mechanics_engine = FactionMechanicsEngine(self.engine, universe_name=self.engine.universe_config.name)
        if mechanics.get("enable_weather", True):
            self.engine.storm_manager = FluxStormManager(self.engine) if os.path.exists(os.path.join(os.path.dirname(__file__), "../managers/weather_manager.py")) else None
        else:
            self.engine.storm_manager = None

    def _finalize_telemetry(self):
        self.engine.telemetry.log_event(
            EventCategory.SYSTEM, 
            "simulation_start", 
            {"timestamp": time.time(), "config": self.engine.game_config}
        )

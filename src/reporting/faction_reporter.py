import os
import json
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, TYPE_CHECKING
from src.reporting.generators import GENERATORS
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.managers.campaign_manager import CampaignEngine

class FactionReporter:
    def __init__(self, campaign_engine: 'CampaignEngine'):
        self.engine = campaign_engine
        self.current_turn = 0
        self.events: Dict[str, List[Dict[str, Any]]] = {} # faction_name -> list of events
        self.initial_states: Dict[str, Dict[str, Any]] = {} # faction_name -> state dict
        
        # Load generators from config
        self.generators = []
        reporting_config = {}
        if hasattr(self.engine, 'game_config'):
             reporting_config = getattr(self.engine.game_config, 'reporting', {})
        
        formats = reporting_config.get("formats", ["json", "markdown"])
        for fmt in formats:
            if fmt in GENERATORS:
                self.generators.append((fmt, GENERATORS[fmt]()))

        # Analytics Engine Integration
        self.analytics_engine = None
        
        if not self.analytics_engine:
            try:
                from src.reporting.live_dashboard import state
                if getattr(state, 'active', False) and getattr(state, 'indexer', None):
                     from src.reporting.analytics_engine import AnalyticsEngine
                     self.analytics_engine = AnalyticsEngine(state.indexer)
            except ImportError:
                pass
            
        # 2. Offline Fallback
        if not self.analytics_engine and self.engine.report_organizer:
            try:
                # Construct path to index.db in the specific batch or run directory
                # ReportOrganizer typically has base_output_dir or similar. 
                # Assuming batch_dir is accessible or we use a common index.
                # For now, let's try to locate the index.db relative to where we are writing.
                # We can't easily know the full batch path from here without inspecting report_organizer internals
                # But we can try:
                batch_dir = getattr(self.engine.report_organizer, 'batch_dir', None)
                if batch_dir:
                    db_path = os.path.join(batch_dir, "index.db")
                    from src.reporting.indexing import ReportIndexer
                    from src.reporting.analytics_engine import AnalyticsEngine
                    
                    # We create a local indexer instance
                    # Note: Concurrent access to sqlite might normally be an issue, 
                    # but pure read (analytics) vs write (indexer crawler) usually okay with WAL.
                    # However, FactionReporter runs inside the simulation loop.
                    # The Indexer is usually updated by a separate thread or process.
                    # If offline, WE might need to trigger indexing? 
                    # The user comment implies we just want the ENGINE available. 
                    # Whether it has data depends on something indexing it.
                    # For offline runs, maybe we treat this as "read what's there".
                    
                    indexer = ReportIndexer(db_path)
                    self.analytics_engine = AnalyticsEngine(indexer)
            except Exception as e:
                if hasattr(self.engine, 'logger'):
                     self.engine.logger.warning(f"Failed to initialize offline analytics: {e}")
        
    def start_turn(self, turn_num: int):
        self.current_turn = turn_num
        self.events = {f_name: [] for f_name in self.engine.factions}
        self.initial_states = {f_name: self._get_faction_snapshot(f_name) for f_name in self.engine.factions}
        
    def _get_faction_snapshot(self, f_name: str) -> Dict[str, Any]:
        faction = self.engine.factions[f_name]
        
        # Calculate Military Power Score
        mil_power = 0
        fleets = self.engine.fleets_by_faction.get(f_name, [])
        for f in fleets:
            if not f.is_destroyed:
                 mil_power += sum(u.cost for u in f.units if u.is_alive())

        return {
            "requisition": faction.requisition,
            "planet_names": [p.name for p in self.engine.planets_by_faction.get(f_name, [])],
            "fleets_count": len(fleets),
            "military_power": mil_power,
            "techs": list(faction.unlocked_techs),
            "total_req_income": faction.stats.get("total_req_income", 0),
            "total_req_expense": faction.stats.get("total_req_expense", 0),
            "units_recruited": faction.stats.get("units_recruited", 0),
            "buildings_constructed": faction.stats.get("buildings_constructed", 0)
        }

    def log_event(self, faction_name: str, category: str, message: str, data: Optional[Dict[str, Any]] = None):
        if faction_name not in self.events:
            self.events[faction_name] = []
        
        self.events[faction_name].append({
            "category": category,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        })

    def finalize_turn(self):
        if not self.engine.report_organizer: return
        
        # Log Global Survival Rates (Metric #14)
        if hasattr(self.engine, 'telemetry') and self.engine.telemetry:
             total = 0
             active = 0
             eliminated = 0
             bankrupt = 0
             
             for name, f in self.engine.factions.items():
                if name == "Neutral": continue
                total += 1
                if getattr(f, 'is_eliminated', False) or getattr(f, 'is_dead', False): 
                    eliminated += 1
                else: 
                    active += 1
                    if f.requisition < 0: bankrupt += 1
            
             self.engine.telemetry.log_event(
                 EventCategory.CAMPAIGN,
                 "faction_survival_rate",
                 {
                     "total_factions": total,
                     "active_factions": active,
                     "eliminated_factions": eliminated,
                     "bankrupt_factions": bankrupt,
                     "survival_rate": (active / total) if total > 0 else 0.0
                 },
                 turn=self.current_turn
             )

        for f_name, faction in self.engine.factions.items():
            if f_name == "Neutral": continue
            
            # 1. Delta Tracking
            start_state = self.initial_states.get(f_name, {})
            end_state = self._get_faction_snapshot(f_name)
            
            deltas = {
                "requisition": end_state["requisition"] - start_state.get("requisition", 0),
                "planets_count": len(end_state["planet_names"]) - len(start_state.get("planet_names", [])),
                "fleets_count": end_state["fleets_count"] - start_state.get("fleets_count", 0),
                "military_power": end_state["military_power"] - start_state.get("military_power", 0),
                "techs_unlocked": len(end_state["techs"]) - len(start_state.get("techs", []))
            }
            
            # Identify specific planet changes
            start_planets = set(start_state.get("planet_names", []))
            end_planets = set(end_state["planet_names"])
            captured = list(end_planets - start_planets)
            lost = list(start_planets - end_planets)
            
            # Efficiency Calculation
            income = faction.stats.get("turn_req_income", 0)
            expense = faction.stats.get("turn_req_expense", 0)
            efficiency = 0.0
            if expense > 0:
                efficiency = (income / expense) * 100.0
            elif income > 0:
                efficiency = 100.0 # Standard placeholder for infinite
            
            # 2. Aggregation
            summary = {
                "turn": self.current_turn,
                "faction": f_name,
                "universe": self.engine.universe_config.name,
                "deltas": deltas,
                "territory": {
                    "captured": captured,
                    "lost": lost,
                    "total_controlled": len(end_planets)
                },
                "economy": {
                    "income": income,
                    "expense": expense,
                    "efficiency_pct": round(efficiency, 1),
                    "construction_spend": faction.stats.get("turn_construction_spend", 0),
                    "recruitment_spend": faction.stats.get("turn_recruitment_spend", 0)
                },
                "mechanics": {
                    "conviction_stacks": getattr(faction, "conviction_stacks", 0),
                    "biomass_pool": getattr(faction, "biomass_pool", 0),
                    "raid_income": getattr(faction, "raid_income_this_turn", 0)
                },
                "military": {
                    "total_fleets": end_state["fleets_count"],
                    "military_power_score": end_state["military_power"],
                    "units_recruited": faction.stats.get("turn_units_recruited", 0),
                    "units_lost": faction.stats.get("turn_units_lost", 0),
                    "damage_dealt": faction.stats.get("turn_damage", 0),
                    "battles_fought": faction.stats.get("turn_battles_fought", 0),
                    "battles_won": faction.stats.get("turn_battles_won", 0)
                },
                "diplomacy": {
                    "actions": faction.stats.get("turn_diplomacy_actions", 0)
                },
                "construction": {
                    "completed": faction.stats.get("turn_constructions_completed", 0)
                },
                "technology": {
                    "unlocked_count": len(end_state["techs"])
                },
                "events": self.events.get(f_name, [])
            }
            
            # Phase 42: Inject Telemetry Metrics for Indexing
            if hasattr(self.engine, 'telemetry') and hasattr(self.engine.telemetry, 'faction_stats_cache'):
                cached = self.engine.telemetry.faction_stats_cache.get(f_name, {})
                if cached:
                    summary["construction_activity"] = cached.get("construction_activity", {})
                    summary["research_impact"] = cached.get("research_impact", {})
                    summary["tech_depth"] = cached.get("tech_depth", {})
            
            # Inject Analytics Insights (If active)
            if self.analytics_engine:
                try:
                    insights = self.analytics_engine.get_real_time_insights(
                        f_name, self.engine.universe_data.active_universe, self.current_turn
                    )
                    summary["analytics"] = insights
                except Exception as e:
                    if self.engine.logger:
                        import traceback
                        self.engine.logger.warning(f"Analytics injection failed: {e}\n{traceback.format_exc()}")
            
            # 3. Save Reports using Pluggable Generators (Refactored Phase 8)
            try:
                f_dir = self.engine.report_organizer.get_turn_path(self.current_turn, "factions", faction=f_name)
                
                for fmt, gen in self.generators:
                    # Flattened Structure: Use Faction_Turn filename to avoid overwrite and preserve history
                    filename = f"{f_name}_turn_{self.current_turn:03d}.{fmt}"
                    output_path = os.path.join(f_dir, filename)
                    gen.generate(summary, output_path)

                # 5. Finalize Manifest (Phase 7: Metadata)
                schema = {
                    "economy": ["income", "expense", "efficiency_pct", "construction_spend", "recruitment_spend"],
                    "military": ["total_fleets", "military_power_score", "units_recruited", "units_lost", "damage_dealt", "battles_fought", "battles_won"],
                    "territory": ["captured", "lost", "total_controlled"],
                    "deltas": ["requisition", "planets_count", "fleets_count", "military_power", "techs_unlocked"]
                }
                manifest_path = os.path.join(f_dir, "manifest.json")
                self.engine.report_organizer.finalize_manifest(manifest_path, data_schema=schema)

            except IOError as e:
                if self.engine.logger:
                    self.engine.logger.error(f"Failed to write faction report for {f_name}: {e}")
            except Exception as e:
                if self.engine.logger:
                    self.engine.logger.error(f"Unexpected error in faction reporting for {f_name}: {e}")

    def export_analytics_report(self, output_dir: str, formats: List[str] = ["json"], webhook_url: Optional[str] = None):
        """Generates comprehensive analytics report for the campaign."""
        if not self.analytics_engine: return
        
        generated_files = {}
        try:
            universe = self.engine.universe_data.active_universe
            report = self.analytics_engine.generate_comprehensive_report(universe)
            
            # Save JSON
            if "json" in formats:
                path = os.path.join(output_dir, "analytics_summary.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2)
                generated_files["json"] = path
                
            # Generate Visualizations (Needed for PDF)
            viz_dir = os.path.join(output_dir, "visualizations")
            try:
                from src.reporting import visualizations as viz
                os.makedirs(viz_dir, exist_ok=True)
                
                # Analytics Visualizations
                indexer = self.analytics_engine.indexer
                for f_name in self.engine.factions:
                    if f_name == "Neutral": continue
                    df = indexer.query_faction_time_series(f_name, universe, ['requisition', 'promethium', 'fleets_count'])
                    if not df.empty:
                        viz.plot_resource_trends(df, os.path.join(viz_dir, f"{f_name}_resources.png"))
                        # Military Power Proxy
                        df['military_power'] = df['fleets_count'] * 1000 
                        viz.plot_military_power_evolution(df, os.path.join(viz_dir, f"{f_name}_mil_strength.png"))
            except ImportError:
                pass
                
            # Excel Export
            if "excel" in formats:
                try:
                    from src.reporting.generators.excel_generator import ExcelReportGenerator
                    gen = ExcelReportGenerator()
                    path = os.path.join(output_dir, "analytics_report.xlsx")
                    # We need to map analytics report structure to what generator expects or update generator
                    # The generator expects 'summary' dict. We can reuse 'report' as summary
                    # But report structure from analytics engine might differ from turn summary.
                    # ExcelGenerator is built for turn summary. 
                    # ADAPTATION: We'll pass the 'report' dict. We updated ExcelGenerator to handle generic structure?
                    # Actually ExcelGenerator in step 1.2 focuses on 'economy', 'military' keys.
                    # Analytics report uses 'metrics', 'trends', 'anomalies'.
                    # For this implementation, we will use the generator as-is and ensure 'report' has keys or we adapt 'report'.
                    # Or better, we explicitly create the Excel here if the generator is strictly for turn summary.
                    # However, plan step 2 said "Register in generators".
                    # Let's assume we pass what we have and let generator handle missing keys gracefully (which it does via get()).
                    
                    # We wrap report in a structure matching generator expectations if needed
                    # Metadata injection
                    report["metadata"] = {"timestamp": datetime.now().isoformat()}
                    gen.generate(report, path)
                    generated_files["excel"] = path
                except Exception as e:
                    print(f"Excel export failed: {e}")

            # PDF Export
            if "pdf" in formats:
                try:
                    from src.reporting.generators.pdf_generator import PDFReportGenerator
                    gen = PDFReportGenerator()
                    path = os.path.join(output_dir, "analytics_report.pdf")
                    report["metadata"] = {"timestamp": datetime.now().isoformat()}
                    gen.generate(report, path)
                    generated_files["pdf"] = path
                except Exception as e:
                    print(f"PDF export failed: {e}")
                    
            # Webhook Notification
            if webhook_url:
                from src.reporting.report_notifier import ReportNotifier
                from src.reporting.notification_channels import NotificationManager
                # Quick config for NM
                nm = NotificationManager({"webhook": {"enabled": True}})
                notifier = ReportNotifier(nm)
                # Determine run_id (engine usually has it)
                run_id = getattr(self.engine, 'run_id', 'unknown')
                notifier.notify_completion(universe, run_id, generated_files, webhook_url)
                
        except Exception as e:
            if getattr(self.engine, 'logger', None):
                self.engine.logger.error(f"Failed to export analytics report: {e}")

    def generate_run_report(self, run_id: str, output_dir: str, formats: List[str] = ["json"], webhook_url: Optional[str] = None):
        """Generates a specific run report."""
        if not self.analytics_engine:
            print("Analytics engine not initialized.")
            return

        generated_files = {}
        try:
            # For a single run, the universe is implied by the DB or engine
            universe = self.engine.universe_data.active_universe
            report = self.analytics_engine.generate_comprehensive_report(universe)
            report["run_id"] = run_id
            
            # Save JSON
            if "json" in formats:
                path = os.path.join(output_dir, f"run_{run_id}_summary.json")
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(report, f, indent=2)
                generated_files["json"] = path
                
            # Excel
            if "excel" in formats:
                try:
                    from src.reporting.generators.excel_generator import ExcelReportGenerator
                    gen = ExcelReportGenerator()
                    path = os.path.join(output_dir, f"run_{run_id}_report.xlsx")
                    report["metadata"] = {"timestamp": datetime.now().isoformat(), "run_id": run_id}
                    gen.generate(report, path)
                    generated_files["excel"] = path
                except Exception as e:
                    print(f"Excel export failed: {e}")
            
            # PDF
            if "pdf" in formats:
                try:
                    from src.reporting.generators.pdf_generator import PDFReportGenerator
                    gen = PDFReportGenerator()
                    path = os.path.join(output_dir, f"run_{run_id}_report.pdf")
                    report["metadata"] = {"timestamp": datetime.now().isoformat(), "run_id": run_id}
                    gen.generate(report, path)
                    generated_files["pdf"] = path
                except Exception as e:
                    print(f"PDF export failed: {e}")

            # Webhook Notification
            if webhook_url:
                from src.reporting.report_notifier import ReportNotifier
                from src.reporting.notification_channels import NotificationManager
                nm = NotificationManager({"webhook": {"enabled": True}})
                notifier = ReportNotifier(nm)
                notifier.notify_completion(universe, run_id, generated_files, webhook_url)
                
        except Exception as e:
            if hasattr(self.engine, 'logger'):
                self.engine.logger.error(f"Failed to generate run report: {e}")
            else:
                print(f"Failed to generate run report: {e}")

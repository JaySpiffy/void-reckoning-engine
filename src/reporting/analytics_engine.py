import threading
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Import specialized analyzers
from src.reporting.analyzers.trend import TrendAnalyzer
from src.reporting.analyzers.anomaly import AnomalyDetector
from src.reporting.analyzers.economic import EconomicHealthAnalyzer
from src.reporting.analyzers.military import MilitaryEfficiencyAnalyzer
from src.reporting.analyzers.industrial import IndustrialAnalyzer
from src.reporting.analyzers.tech import TechAnalyzer, ResearchAnalyzer
from src.reporting.analyzers.behavior import AIAnalyzer, PortalAnalyzer
from src.reporting.analyzers.meta import (
    ComparativeAnalyzer, 
    DifficultyAnalyzer, 
    ResourceExhaustionAnalyzer, 
    PredictiveAnalytics
)

class AnalyticsEngine:
    """Orchestrator for all analytics components."""
    
    def __init__(self, indexer):
        self.indexer = indexer
        
        # Initialize specialized analyzers
        self.trend_analyzer = TrendAnalyzer(indexer)
        self.anomaly_detector = AnomalyDetector(indexer)
        
        self.economic_health_analyzer = EconomicHealthAnalyzer(indexer)
        self.military_efficiency_analyzer = MilitaryEfficiencyAnalyzer(indexer)
        self.industrial_analyzer = IndustrialAnalyzer(indexer)
        
        self.tech_analyzer = TechAnalyzer(indexer)
        self.research_analyzer = ResearchAnalyzer(indexer)
        
        self.ai_analyzer = AIAnalyzer(indexer)
        self.portal_analyzer = PortalAnalyzer(indexer)
        
        self.comparative_analyzer = ComparativeAnalyzer(indexer)
        self.difficulty_analyzer = DifficultyAnalyzer(indexer)
        self.resource_exhaustion = ResourceExhaustionAnalyzer(indexer)
        self.predictive_analytics = PredictiveAnalytics(indexer)
        
        self.cache = {}
        self.cache_lock = threading.Lock()

    def _cleanup_expired_cache(self, current_turn: int):
        """Removes expired entries."""
        with self.cache_lock:
            keys_to_del = [k for k, v in self.cache.items() if v[1] <= current_turn]
            for k in keys_to_del:
                del self.cache[k]

    def _is_cache_valid(self, cache_key: str, current_turn: int) -> bool:
        with self.cache_lock:
            if cache_key in self.cache:
                _, expiry = self.cache[cache_key]
                return current_turn < expiry
        return False
        
    def get_comprehensive_analysis(self, faction: str, universe: str, current_turn: int, include_sections: List[str] = None) -> Dict[str, Any]:
        """Unified interface for all analytics."""
        self._cleanup_expired_cache(current_turn)
        
        cache_key = f"comprehensive_{faction}_{universe}_{current_turn}"
        if self._is_cache_valid(cache_key, current_turn):
            with self.cache_lock:
                return self.cache[cache_key][0]
                
        # Gather Analysis
        
        # Helper to find a planet for ROI
        key_planet = None
        try:
             pq = "SELECT source_planet FROM resource_transactions WHERE faction=? AND universe=? ORDER BY turn DESC LIMIT 1"
             pdf = pd.read_sql_query(pq, self.indexer.conn, params=(faction, universe))
             if not pdf.empty:
                 key_planet = pdf['source_planet'].iloc[0]
        except:
            pass

        analysis = {
            "economic_health": {
                "velocity": self.economic_health_analyzer.calculate_stockpile_velocity(faction, universe, current_turn=current_turn),
                "death_spiral": self.economic_health_analyzer.detect_economic_death_spiral(faction, universe, current_turn=current_turn),
                "resource_roi": self.economic_health_analyzer.calculate_resource_roi(faction, universe, key_planet if key_planet else "Unknown", current_turn=current_turn)
            },
            "military_efficiency": {
                "combat_effectiveness": self.military_efficiency_analyzer.analyze_combat_effectiveness(faction, universe, current_turn=current_turn),
                "force_composition": self.military_efficiency_analyzer.calculate_force_composition_trends(faction, universe),
                "attrition": self.military_efficiency_analyzer.detect_attrition_patterns(faction, universe)
            },
            "industrial_analysis": {
                "density": self.industrial_analyzer.calculate_industrial_density(faction, universe, current_turn=current_turn),
                "queue_efficiency": self.industrial_analyzer.analyze_queue_efficiency(faction, universe),
                "idle_anomalies": self.industrial_analyzer.detect_idle_time_anomalies(faction, universe)
            },
            "research_analysis": {
                "tech_depth": self.research_analyzer.calculate_tech_tree_depth(faction, universe, current_turn=current_turn),
                "research_roi": self.research_analyzer.measure_research_roi(faction, universe, current_turn=current_turn),
                "competition": self.research_analyzer.compare_tech_progression(faction, universe, current_turn=current_turn)
            },
            "summary_insights": self.get_real_time_insights(faction, universe, current_turn)
        }
        
        # Cache with 5 turn TTL
        with self.cache_lock:
            self.cache[cache_key] = (analysis, current_turn + 5)
            
        return analysis
        
    def generate_alert_insights(self, universe: str) -> Dict[str, Any]:
        """Correlates alerts with simulation patterns."""
        try:
            from src.reporting.alert_manager import AlertManager
            am = AlertManager()
            alerts = am.history.alerts
            
            if not alerts: return {"insight": "No alert data for correlation."}
            
            # Simple count by severity
            severities = {}
            for a in alerts:
                s = a.severity.value
                severities[s] = severities.get(s, 0) + 1
                
            return {
                "severity_distribution": severities,
                "total_alerts": len(alerts),
                "hotspots": "No hotspots identified yet"
            }
        except:
            return {}
        
    def get_real_time_insights(self, faction: str, universe: str, current_turn: int) -> Dict[str, Any]:
        """Generates actionable insights for live dashboard."""
        
        # Check cache
        cache_key = f"insights_{faction}_{universe}_{current_turn}"
        if self._is_cache_valid(cache_key, current_turn):
            with self.cache_lock:
                return self.cache[cache_key][0]

        # Use new analyzers for richer insights
        econ_spiral = self.economic_health_analyzer.detect_economic_death_spiral(faction, universe)
        mil_eff = self.military_efficiency_analyzer.analyze_combat_effectiveness(faction, universe)
        ind_eff = self.industrial_analyzer.analyze_queue_efficiency(faction, universe)
        tech_v = self.tech_analyzer.calculate_tech_velocity(faction, universe)
        
        insights = {
            "trends": self.trend_analyzer.analyze_win_rate_trajectory(faction, universe),
            "anomalies": self.anomaly_detector.detect_resource_spikes(faction, universe),
            "victory_prob": self.predictive_analytics.forecast_victory_probability(faction, universe, current_turn),
            "exhaustion_risk": self.resource_exhaustion.check_exhaustion_risk(faction, universe),
            "tech_velocity": tech_v,
            "ai_behavior": self.ai_analyzer.detect_behavior_deviations(faction, universe),
            
            # New Insights
            "economic_warning": econ_spiral if econ_spiral.get("in_death_spiral") else None,
            "military_rating": mil_eff.get("trend"),
            "industrial_rating": ind_eff.get("efficiency_rating"),
            "research_depth": self.research_analyzer.calculate_tech_tree_depth(faction, universe).get("avg_depth")
        }
        
        with self.cache_lock:
            self.cache[cache_key] = (insights, current_turn + 5)
            
        return insights

    def generate_comprehensive_report(self, universe: str) -> Dict[str, Any]:
        """Compiles a full analytics report for the universe."""
        return {
            "balance_score": self.comparative_analyzer.calculate_faction_balance_score(universe),
            "battle_anomalies": self.anomaly_detector.detect_battle_anomalies(universe),
            "difficulty_rating": self.difficulty_analyzer.calculate_difficulty_rating(universe),
            "portal_patterns": self.portal_analyzer.analyze_usage_patterns(universe),
            "diplomacy_network": self.indexer.query_diplomacy_events(universe) # Raw edges for graph
        }

    def detect_and_trigger_alerts(self, universe: str, current_turn: int):
        """Orchestrates anomaly detection and triggers alerts via AlertManager (Step 5)."""
        # Cache check with 5-turn TTL
        cache_key = f"anomaly_check_{universe}_{current_turn}"
        if self._is_cache_valid(cache_key, current_turn):
            return

        try:
            from src.reporting.alert_manager import AlertManager
            from src.reporting.alert_models import AlertSeverity
            am = AlertManager()
        except ImportError:
            return

        # Query all active factions
        query = "SELECT DISTINCT faction FROM factions WHERE universe = ?"
        try:
            factions_df = pd.read_sql_query(query, self.indexer.conn, params=(universe,))
            factions = factions_df['faction'].tolist()
        except:
            return

        for faction in factions:
            # 1. Economic Spikes & Death Spiral
            anomalies = self.anomaly_detector.detect_resource_spikes(faction, universe)
            for anom in anomalies:
                if anom['type'] == "economic_death_spiral":
                    msg = f"{faction} is experiencing economic death spiral: velocity {round(anom['velocity'], 2)}, bankruptcy projected at turn {anom.get('projected_bankruptcy_turn', 'unknown')}."
                    am.trigger_alert(AlertSeverity.CRITICAL, "Economic Death Spiral", msg, anom)
                elif anom['type'] == "resource_spike":
                    msg = f"{faction} resource spike detected: change of {round(anom['change'], 2)} at turn {anom['turn']}."
                    am.trigger_alert(AlertSeverity.WARNING, "Resource Spike", msg, anom)

            # 2. Military Inefficiency
            mil_anom = self.anomaly_detector.detect_military_inefficiency(faction, universe)
            if mil_anom:
                msg = f"{faction} is experiencing military inefficiency: CER < 0.5 for {mil_anom['consecutive_poor_battles']} consecutive battles."
                am.trigger_alert(AlertSeverity.WARNING, "Military Inefficiency", msg, mil_anom)

            # 3. Idle Infrastructure
            ind_anom = self.anomaly_detector.detect_idle_infrastructure(faction, universe)
            if ind_anom:
                msg = f"{faction} is experiencing idle infrastructure: > 50% idle for {ind_anom['turns_idle']} turns."
                am.trigger_alert(AlertSeverity.WARNING, "Idle Infrastructure", msg, ind_anom)

            # 4. Research Stagnation
            res_anom = self.anomaly_detector.detect_research_stagnation(faction, universe)
            if res_anom:
                msg = f"{faction} is experiencing research stagnation: no progress for {res_anom['turns_without_progress']} turns."
                am.trigger_alert(AlertSeverity.INFO, "Research Stagnation", msg, res_anom)

        # Update cache
        with self.cache_lock:
            self.cache[cache_key] = (True, current_turn + 5)

"""
Logging Configuration
---------------------
Controls feature flags for advanced logging and telemetry.
All high-volume tracers default to False to protect simulation performance.
Enable specific flags only for debugging sessions.
"""

LOGGING_FEATURES = {
    # High Priority
    "ai_decision_trace": True,      # HIGH COST: Detailed AI logic logs
    "task_force_mission_tracking": True, 
    "tech_research_path_analysis": True,
    "planet_strategic_value_assessment": True,
    "combat_engagement_analysis": True, # HIGH COST: Detailed combat stats
    "faction_elimination_analysis": True, # Low cost (once per game)
    
    # Medium Priority
    "intelligence_espionage_tracing": True,
    "portal_wormhole_usage_tracking": True,
    "doctrine_adaptation_tracing": True,
    "resource_production_breakdown": True,
    "fleet_optimization_tracking": True,
    "weather_effects_tracing": True,
    
    # Low Priority
    "hero_lifecycle_tracking": False,
    "trade_route_analysis": False,
    "multi_universe_interactions": False,
    "performance_profiling": True, # Enabled for monitoring effect
    "event_correlation": False,
    "user_action_analysis": False,
    "scenario_objective_tracking": False,
    "consistency_checks": False
}

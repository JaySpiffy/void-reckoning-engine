import json
from datetime import datetime
from typing import List, Dict, Optional, Any
from src.config import logging_config

class CombatTracker:
    """Manages structured JSON logging for combat events.
    Captures weapon-level granularity and unit state snapshots."""
    def __init__(self, json_path: Optional[str] = None, universe_name: str = "void_reckoning", telemetry_collector=None, verbosity: str = "detailed"):
        self.json_path = json_path
        self.telemetry_collector = telemetry_collector
        self.verbosity = verbosity
        
        # Verbosity Levels
        # minimal: rounds, final result
        # standard: kills, abilities
        # detailed: weapon_fire, snapshots (for replay)
        # debug: everything
        
        self.events = []
        self.snapshots = []
        self.performance_stats = []
        self.weapon_statistics = {}
        self.meta = {
            "version": "4.2",
            "timestamp": datetime.now().isoformat(),
            "winner": None,
            "rounds": 0,
            "universe": universe_name
        }
        self.current_round = 0

    def start_round(self, round_num: int):
        self.current_round = round_num

    def log_round_performance(self, round_num: int, metrics: Dict[str, float]):
        self.performance_stats.append({
            "round": round_num,
            "metrics": metrics
        })
        
        # Stream High-Res Metrics if Collector is available
        if self.telemetry_collector:
            # We use a custom event type for granular performance
            from src.reporting.telemetry import EventCategory, VerbosityLevel
            self.telemetry_collector.log_event(
                EventCategory.SYSTEM, 
                "combat_performance_round", 
                {"round": round_num, "metrics": metrics},
                turn=None, # Combat happens within a turn, but this is sub-turn
                level=VerbosityLevel.DEBUG
            )

    def log_snapshot(self, unit):
        # Enhanced snapshot for Phase 4
        snapshot = {
            "round": self.current_round,
            "unit": unit.name,
            "faction": getattr(unit, 'faction', 'Unknown'),
            "hp": int(unit.current_hp),
            "max_hp": int(unit.base_hp),
            "shields": int(getattr(unit, 'shield_current', 0)),
            "is_alive": unit.is_alive(),
            "position": {"x": unit.grid_x, "y": unit.grid_y, "facing": getattr(unit, 'facing', 0)},
            "morale": getattr(unit, 'leadership', 0),
            "suppression": getattr(unit, 'is_suppressed', False),
            "components": [c.to_dict() for c in unit.components],
            "active_modifiers": getattr(unit, 'active_mods', {}),
            "elemental_dna": getattr(unit, 'elemental_dna', None),
            "atomic_abilities": getattr(unit, 'atomic_abilities', {}),
            "cooldowns": getattr(unit, 'ability_cooldowns', {})
        }
        self.snapshots.append(snapshot)

    def log_atomic_trace(self, trace_data: Dict[str, Any]):
        """Logs detailed atomic synthesis calculations."""
        event = {
            "round": self.current_round,
            "type": "atomic_synthesis_trace",
            "timestamp": datetime.now().isoformat()
        }
        event.update(trace_data)
        self.events.append(event)

    def log_event(self, event_type: str, attacker, target, weapon=None, **kwargs):
        # Verbosity Filtering
        if self.verbosity == "minimal":
            return
            
        if self.verbosity == "standard":
            # Only log kills, abilities, high-value events
            if event_type not in ["ability_activation", "unit_death"]:
                if event_type == "weapon_fire_detailed" and not kwargs.get("killed", False):
                    return
                    
        event = {
            "round": self.current_round,
            "type": event_type,
            "attacker": attacker.name if attacker else "World",
            "target": target.name if target else "None",
            "weapon": weapon.name if hasattr(weapon, 'name') else str(weapon) if weapon else "None",
            "timestamp": datetime.now().isoformat()
        }
        event.update(kwargs)
        self.events.append(event)
        
        # Phase 1.3: Weapon Statistics Tracking
        if event_type == "weapon_fire_detailed":
            w_name = event["weapon"]
            if w_name not in self.weapon_statistics:
                self.weapon_statistics[w_name] = {
                    "shots_fired": 0, "shots_hit": 0, "shots_missed": 0, 
                    "total_damage": 0, "kills": 0, "components_destroyed": 0
                }
            
            stats = self.weapon_statistics[w_name]
            stats["shots_fired"] += 1
            if kwargs.get("hit_result", False):
                stats["shots_hit"] += 1
                stats["total_damage"] += kwargs.get("damage_breakdown", {}).get("final", 0)
                if kwargs.get("killed", False):
                    stats["kills"] += 1
                if kwargs.get("component_destroyed"):
                    stats["components_destroyed"] += 1
            else:
                stats["shots_missed"] += 1
    
    def calculate_combat_effectiveness_ratio(self, damage_dealt: float, resources_lost: float) -> float:
        """Computes CER as damage_dealt / resources_lost."""
        if resources_lost <= 0:
            return 0.0
        return damage_dealt / resources_lost

    def _get_force_composition(self, units: List[Any]) -> Dict[str, int]:
        """Categorizes units into capital ships, escorts, and ground units."""
        comp = {"capital_ships": 0, "escorts": 0, "ground_units": 0}
        for u in units:
            # Domain check
            if getattr(u, 'domain', '') == 'ground' or u.__class__.__name__ == 'Regiment':
                comp["ground_units"] += 1
            elif u.__class__.__name__ == 'Ship' or getattr(u, 'domain', '') == 'space':
                s_class = getattr(u, 'ship_class', 'Escort')
                tier = getattr(u, 'tier', 1)
                if s_class == "Battleship" or tier >= 3:
                    comp["capital_ships"] += 1
                elif s_class in ["Escort", "Cruiser"]:
                    comp["escorts"] += 1
                else:
                    # Fallback
                    comp["escorts"] += 1
        return comp

    def finalize(self, winner: str, rounds: int, faction_units: Dict[str, List[Any]], 
                 pre_battle_counts: Dict[str, int] = None, battle_id: str = None, 
                 battle_stats: Dict[str, Any] = None, skip_save: bool = False):
        self.meta["winner"] = winner
        self.meta["rounds"] = rounds
        self.meta["battle_id"] = battle_id
        
        # Final tally of survivors
        tally = {}
        performance_data = {}
        
        for f, units in faction_units.items():
            alive_count = sum(1 for u in units if u.is_alive())
            tally[f] = {
                "total": len(units),
                "alive": alive_count
            }
            
            # Phase 42: Advanced Military Metrics
            # Damage Dealt (extracted from battle_stats if available)
            damage_dealt = 0.0
            if battle_stats and f in battle_stats:
                damage_dealt = battle_stats[f].get("total_damage_dealt", 0.0)
            
            # Resources Lost (sum of cost for dead units)
            resources_lost = sum(getattr(u, 'cost', 150) for u in units if not u.is_alive())
            
            # Attrition Rate
            initial_count = pre_battle_counts.get(f, len(units)) if pre_battle_counts else len(units)
            attrition = ((initial_count - alive_count) / initial_count * 100) if initial_count > 0 else 0.0
            
            # Force Composition
            composition = self._get_force_composition(units)
            
            # CER
            cer = self.calculate_combat_effectiveness_ratio(damage_dealt, resources_lost)
            
            perf = {
                "damage_dealt": damage_dealt,
                "resources_lost": resources_lost,
                "cer": cer,
                "composition": composition,
                "attrition_rate": attrition
            }
            performance_data[f] = perf
            
            # Record to Telemetry if available
            if self.telemetry_collector:
                self.telemetry_collector.metrics.record_battle_performance(
                    battle_id=battle_id or "unknown_battle",
                    faction=f,
                    damage_dealt=damage_dealt,
                    resources_lost=resources_lost,
                    force_composition=composition,
                    attrition_rate=attrition
                )

        self.meta["final_tally"] = tally
        self.meta["performance_metrics"] = performance_data

        # Phase 6: Combat Engagement Analysis
        if logging_config.LOGGING_FEATURES.get('combat_engagement_analysis', False):
            self._log_engagement_analysis(winner, rounds, performance_data, battle_id)

        # Phase 108: Intel Summary
        if battle_stats:
            self.meta["intel_summary"] = {
                f: {
                    "intel_earned": stats.get("intel_points_earned", 0),
                    "tech_discovered": len(stats.get("enemy_tech_encountered", set())),
                    "units_analyzed": len(stats.get("enemy_units_analyzed", []))
                }
                for f, stats in battle_stats.items()
            }
            
            # Wreckage Summary
            self.meta["wreckage_summary"] = {
                f: {
                    "total_wreckage": len(stats.get("wreckage", [])),
                    "blueprints_salvaged": [w["blueprint_id"] for w in stats.get("wreckage", [])]
                }
                for f, stats in battle_stats.items()
            }
        
    def _log_engagement_analysis(self, winner: str, rounds: int, perf_data: Dict[str, Any], battle_id: str):
        """Logs high-resolution combat metrics to central telemetry."""
        if not self.telemetry_collector:
            return

        from src.reporting.telemetry import EventCategory
        
        # Calculate Power Ratios and Attrition
        analysis = {
            "battle_id": battle_id,
            "winner": winner,
            "rounds": rounds,
            "factions": {}
        }

        for faction, metrics in perf_data.items():
            analysis["factions"][faction] = {
                "cer": metrics["cer"],
                "attrition": metrics["attrition_rate"],
                "damage_dealt": metrics["damage_dealt"],
                "resources_lost": metrics["resources_lost"],
                "composition": metrics["composition"]
            }

        self.telemetry_collector.log_event(
            EventCategory.COMBAT,
            "combat_engagement_analysis",
            analysis,
            turn=None # Handled by collector if it has Turn context
        )

    def save(self):
        if not self.json_path: return
        
        # Inject weapon statistics into meta
        self.meta["weapon_statistics"] = self.weapon_statistics
        
        data = {
            "meta": self.meta,
            "performance": self.performance_stats,
            "snapshots": self.snapshots,
            "events": self.events
        }
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            # Using standard print as fallback since Battle State might not have logger access
            print(f"I/O Error saving combat log to {self.json_path}: {e}")
        except Exception as e:
            print(f"Unexpected error saving combat log: {e}")

    def cleanup(self):
        """Clean up resources."""
        pass

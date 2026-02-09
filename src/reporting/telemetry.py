import os
import json
import time
import queue
import threading
import psutil
import gc
from datetime import datetime, timezone
from enum import Enum, auto
from typing import List, Dict, Optional, Any, Callable

# Capture open to prevent GC issues during __del__
_open = open

class EventBatcher(threading.Thread):
    """Background worker that handles persistent event storage and indexing."""
    def __init__(self, collector):
        super().__init__(daemon=True, name="TelemetryBatcher")
        self.collector = collector
        self.queue = queue.Queue()
        self.stop_event = threading.Event()
        self.batch_size = collector.batch_size
        self.indexer = None
        self.batch_id = "unknown"
        self.run_id = "unknown"

    def run(self):
        while not self.stop_event.is_set() or not self.queue.empty():
            batch = []
            try:
                # Block for a bit to avoid busy wait
                timeout = 0.5 if not self.stop_event.is_set() else 0.05
                try:
                    event = self.queue.get(timeout=timeout)
                    batch.append(event)
                except queue.Empty:
                    pass
                
                # Fill batch from queue
                while len(batch) < self.batch_size:
                    try:
                        batch.append(self.queue.get_nowait())
                    except queue.Empty:
                        break
                
                if batch:
                    self.collector._write_to_disk(batch)
                    if self.indexer:
                        self.indexer.index_realtime_events(
                            self.batch_id, 
                            self.run_id, 
                            batch, 
                            self.collector.universe_name
                        )
            except Exception as e:
                # Fail-safe to prevent thread death
                pass

    def stop(self):
        self.stop_event.set()
        self.join(timeout=2.0)

class EventCategory(Enum):
    ECONOMY = "economy"
    COMBAT = "combat"
    DIPLOMACY = "diplomacy"
    MOVEMENT = "movement"
    CONSTRUCTION = "construction"
    SYSTEM = "system"
    CAMPAIGN = "campaign"
    STRATEGY = "strategy"
    DOCTRINE = "doctrine"
    TECHNOLOGY = "technology"
    INTELLIGENCE = "intelligence"
    PORTAL = "portal"
    HERO = "hero"
    OPTIMIZATION = "optimization"
    ENVIRONMENT = "environment"

class VerbosityLevel(Enum):
    SUMMARY = 0
    DETAILED = 1
    DEBUG = 2

    @classmethod
    def from_str(cls, label: str):
        label = label.upper()
        if label == "SUMMARY": return cls.SUMMARY
        if label == "DETAILED": return cls.DETAILED
        if label == "DEBUG": return cls.DEBUG
        return cls.SUMMARY

class MetricsAggregator:
    """
    Real-time aggregation of campaign metrics for dashboard display.
    Maintains sliding windows of recent activity for rate calculation.
    """
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self.battles: List[float] = [] 
        self.total_battles: int = 0
        
        # Split Unit Tracking: {faction: {navy: [t...], army: [t...]}}
        self.units_spawned: Dict[str, Dict[str, List[float]]] = {} 
        self.total_units_spawned: int = 0
        
        self.units_lost: Dict[str, Dict[str, List[float]]] = {}
        self.total_units_lost: int = 0
        
        # Construction Tracking
        self.construction: Dict[str, List[float]] = {}
        self.total_construction: int = 0
        
        # For resource flow, we need timed deltas: (timestamp, amount)
        self.resource_flow: Dict[str, List[tuple]] = {}   
        self.total_income: float = 0.0

        # Phase 42: Advanced Economic Tracking
        self.upkeep_costs: Dict[str, List[tuple]] = {} # (timestamp, amount, type)
        self.total_upkeep: float = 0.0
        self.resource_stockpile_history: Dict[str, List[tuple]] = {} # (timestamp, amount)
        self.categorized_revenue: Dict[str, Dict[str, List[tuple]]] = {} # {faction: {category: [(ts, amt, src)]}}
        self.pending_economic_transactions: List[Dict] = [] # Buffer for DB flushing
        self.battle_performance: Dict[str, List[Dict]] = {} # {faction: [{"battle_id": ..., "cer": ..., "composition": ..., "attrition": ..., "timestamp": ...}]}
        self.lock = threading.RLock()

    def record_battle(self):
        with self.lock:
            self.battles.append(time.time())
            self.total_battles += 1

    def record_unit_spawn(self, faction: str, unit_type: str = "army"):
        with self.lock:
            if faction not in self.units_spawned:
                self.units_spawned[faction] = {"navy": [], "army": []}
            
            # Normalize type
            ut = "navy" if unit_type == "fleet" else "army"
            self.units_spawned[faction][ut].append(time.time())
            self.total_units_spawned += 1

    def record_unit_loss(self, faction: str, count: int = 1, navy_count: int = 0, army_count: int = 0):
        with self.lock:
            if faction not in self.units_lost:
                self.units_lost[faction] = {"navy": [], "army": []}
            
            now = time.time()
            
            # If explicit counts provided (new system)
            if navy_count > 0 or army_count > 0:
                for _ in range(navy_count): self.units_lost[faction]["navy"].append(now)
                for _ in range(army_count): self.units_lost[faction]["army"].append(now)
            else:
                # Legacy Fallback (assume army/mixed)
                for _ in range(count):
                    self.units_lost[faction]["army"].append(now)
                    
            self.total_units_lost += count

    def record_construction(self, faction: str):
        with self.lock:
            if faction not in self.construction:
                self.construction[faction] = []
            self.construction[faction].append(time.time())
            self.total_construction += 1

    def record_resource_gain(self, faction: str, amount: float, category: str = "Unknown", source_planet: str = None):
        with self.lock:
            if faction not in self.resource_flow:
                self.resource_flow[faction] = []
            now = time.time()
            self.resource_flow[faction].append((now, amount))
            self.total_income += amount

            # Categorized Tracking (timestamp, amount, source_planet)
            if faction not in self.categorized_revenue:
                self.categorized_revenue[faction] = {}
            if category not in self.categorized_revenue[faction]:
                self.categorized_revenue[faction][category] = []
            self.categorized_revenue[faction][category].append((now, amount, source_planet))
            
            # Add to pending buffer for persistence
            self.pending_economic_transactions.append({
                "faction": faction,
                "category": category,
                "amount": amount,
                "source_planet": source_planet,
                "timestamp": now
            })

    def record_upkeep_cost(self, faction: str, amount: float, upkeep_type: str = "military"):
        with self.lock:
            if faction not in self.upkeep_costs:
                self.upkeep_costs[faction] = []
            self.upkeep_costs[faction].append((time.time(), amount, upkeep_type))
            self.total_upkeep += amount

            # Add to pending buffer for persistence (Negative for cost)
            self.pending_economic_transactions.append({
                "faction": faction,
                "category": f"upkeep_{upkeep_type}",
                "amount": -amount,
                "source_planet": None,
                "timestamp": time.time()
            })

    def record_resource_spend(self, faction: str, amount: float, category: str, source_planet: str = None):
        """Records capital expenditures (construction, recruitment, research)."""
        with self.lock:
            now = time.time()
            # Add to pending buffer for persistence (Negative for cost)
            self.pending_economic_transactions.append({
                "faction": faction,
                "category": category,
                "amount": -float(amount),
                "source_planet": source_planet,
                "timestamp": now
            })

    def record_stockpile_snapshot(self, faction: str, stockpile_amount: float):
        with self.lock:
            if faction not in self.resource_stockpile_history:
                self.resource_stockpile_history[faction] = []
            self.resource_stockpile_history[faction].append((time.time(), stockpile_amount))
            # Keep only last 10 entries (sliding window)
            if len(self.resource_stockpile_history[faction]) > 10:
                self.resource_stockpile_history[faction].pop(0)

    def calculate_net_profit(self, faction: str) -> Dict[str, float]:
        now = time.time()
        cutoff = now - self.window_seconds
        
        # Calculate gross income from categorized revenue
        gross_income = 0.0
        if faction in self.categorized_revenue:
            for category, transactions in self.categorized_revenue[faction].items():
                recent = [amt for ts, amt, src in transactions if ts > cutoff]
                gross_income += sum(recent)
        
        # Calculate total upkeep
        total_upkeep = 0.0
        if faction in self.upkeep_costs:
            recent_upkeep = [amt for ts, amt, _ in self.upkeep_costs[faction] if ts > cutoff]
            total_upkeep = sum(recent_upkeep)
        
        return {
            "gross_income": gross_income / self.window_seconds if self.window_seconds > 0 else 0,
            "total_upkeep": total_upkeep / self.window_seconds if self.window_seconds > 0 else 0,
            "net_profit": (gross_income - total_upkeep) / self.window_seconds if self.window_seconds > 0 else 0
        }

    def calculate_stockpile_velocity(self, faction: str, extended: bool = False) -> Any:
        if faction not in self.resource_stockpile_history:
            return 0.0 if not extended else {}
            
        history = self.resource_stockpile_history[faction]
        if len(history) < 2:
            return 0.0 if not extended else {}
        
        # Helper for velocity
        def calc_v(subset):
             if len(subset) < 2: return 0.0
             t1, a1 = subset[0]
             t2, a2 = subset[-1]
             dt = t2 - t1
             return (a2 - a1) / dt if dt > 0 else 0.0
             
        # Basic Velocity (Full Window)
        velocity = calc_v(history)
        
        if not extended:
            return velocity
            
        # Extended Metrics (Metric #5)
        # Use samples as proxy for turns (assuming 1 log/turn)
        current = history[-1][1]
        
        velocity_per_turn = velocity # Rename logic
        if len(history) >= 2:
             # Velocity = (New - Old) / (NewTurn - OldTurn)
             # Here we just take delta per sample
             velocity_per_turn = (history[-1][1] - history[-2][1])
             
        # Rolling Averages
        avg_10 = 0.0
        if len(history) >= 2:
             deltas = [history[i][1] - history[i-1][1] for i in range(1, len(history))]
             avg_10 = sum(deltas) / len(deltas)
             
        avg_50 = avg_10 # History limit is small currently
        
        v_trend = "stable"
        if len(history) >= 4:
            recent_v = (history[-1][1] - history[-2][1])
            old_v = (history[-3][1] - history[-4][1])
            if recent_v > old_v * 1.1: v_trend = "accelerating"
            elif recent_v < old_v * 0.9: v_trend = "decelerating"
        
        turns_until_depletion = None
        if velocity_per_turn < 0 and current > 0:
             turns_until_depletion = int(abs(current / velocity_per_turn))
             
        turns_until_target = None # Not implemented in plan details but required by structure
        
        return {
            "current_stockpile": current,
            "velocity_per_turn": velocity_per_turn,
            "avg_velocity_10_turns": avg_10,
            "avg_velocity_50_turns": avg_50,
            "velocity_trend": v_trend,
            "turns_until_depletion": turns_until_depletion,
            "turns_until_target": turns_until_target
        }

    def calculate_income_volatility(self, faction: str) -> float:
        """Calculates standard deviation of recent income transactions."""
        if faction not in self.resource_flow:
            return 0.0
            
        now = time.time()
        cutoff = now - self.window_seconds
        recent = [amt for ts, amt in self.resource_flow[faction] if ts > cutoff]
        
        if len(recent) < 2: return 0.0
        
        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        return (variance ** 0.5)

    def calculate_economic_volatility(self, faction: str) -> Dict[str, float]:
        """Aggregates multiple volatility metrics."""
        inc_vol = self.calculate_income_volatility(faction)
        
        # Expense Volatility
        exp_vol = 0.0
        if faction in self.upkeep_costs:
            now = time.time()
            cutoff = now - self.window_seconds
            recent = [amt for ts, amt, typ in self.upkeep_costs[faction] if ts > cutoff]
            if len(recent) >= 2:
                mean = sum(recent) / len(recent)
                var = sum((x - mean) ** 2 for x in recent) / len(recent)
                exp_vol = (var ** 0.5)
                
        combined = (inc_vol + exp_vol) / 2
        
        level = "low"
        if combined > 2000: level = "extreme"
        elif combined > 500: level = "high"
        elif combined > 100: level = "medium"
        
        trend = "stable" # Needs history to calc trend, placeholder
        anomaly = (level == "extreme")
        desc = "Extreme volatility detected" if anomaly else None
        
        return {
            "income_volatility": inc_vol,
            "expense_volatility": exp_vol,
            "combined_volatility": combined,
            "volatility_level": level,
            "volatility_trend": trend,
            "anomaly_detected": anomaly,
            "anomaly_description": desc
        }

    def correlate_combat_economy(self, faction: str) -> Dict[str, Any]:
        """
        Analyzes correlation between combat losses and economic performance.
        Metric #17.
        """
        # 1. Get recent resource losses from combat
        recent_losses = 0.0
        if faction in self.battle_performance:
            # Sum 'resources_lost' in last N battles
            recent_losses = sum(b.get("resources_lost", 0) for b in self.battle_performance[faction])
            
        # 2. Get Income Trend
        income_vol = self.calculate_income_volatility(faction)
        
        # 3. Simple Heuristic Correlation
        # If high losses AND high income volatility => High Correlation (War is destabilizing economy)
        correlation_score = 0.0
        details = "Stable"
        
        if recent_losses > 5000:
             if income_vol > 500:
                 correlation_score = 0.8
                 details = "Destabilizing War"
             elif income_vol > 100:
                 correlation_score = 0.4
                 details = "Managed Conflict"
             else:
                 correlation_score = 0.1
                 details = "Resilient Economy"
        
        return {
            "recent_combat_losses": recent_losses,
            "income_volatility": income_vol,
            "correlation_score": correlation_score,
            "impact_assessment": details
        }

    def record_battle_performance(self, battle_id: str, faction: str, damage_dealt: float, 
                                 resources_lost: float, force_composition: Dict[str, int], 
                                 attrition_rate: float):
        """Records granular battle performance metrics."""
        with self.lock:
            if faction not in self.battle_performance:
                self.battle_performance[faction] = []
            
            cer = damage_dealt / resources_lost if resources_lost > 0 else 0.0
            
            self.battle_performance[faction].append({
                "battle_id": battle_id,
                "cer": cer,
                "damage_dealt": damage_dealt,
                "resources_lost": resources_lost,
                "composition": force_composition,
                "attrition": attrition_rate,
                "timestamp": time.time()
            })
            
            if len(self.battle_performance[faction]) > 20:
                self.battle_performance[faction].pop(0)

    def record_construction_activity(self, faction: str, building_type: str, 
                                     idle_slots: int, queue_efficiency: float):
        """Records construction activity metrics including idle time and building types."""
        with self.lock:
            if not hasattr(self, 'construction_activity'):
                self.construction_activity = {}
            
            if faction not in self.construction_activity:
                self.construction_activity[faction] = []
            
            self.construction_activity[faction].append({
                "building_type": building_type,
                "idle_slots": idle_slots,
                "queue_efficiency": queue_efficiency,
                "timestamp": time.time()
            })
            
            # Keep last 50 entries per faction
            if len(self.construction_activity[faction]) > 50:
                self.construction_activity[faction].pop(0)

    def record_research_impact(self, faction: str, tech_id: str, 
                              pre_unlock_metrics: Dict[str, float], 
                              post_unlock_metrics: Dict[str, float]):
        """Records research ROI by comparing pre/post unlock metrics."""
        with self.lock:
            if not hasattr(self, 'research_impacts'):
                self.research_impacts = {}
            
            if faction not in self.research_impacts:
                self.research_impacts[faction] = []
            
            # Calculate deltas
            deltas = {}
            for key in pre_unlock_metrics:
                if key in post_unlock_metrics:
                    deltas[key] = post_unlock_metrics[key] - pre_unlock_metrics[key]
            
            self.research_impacts[faction].append({
                "tech_id": tech_id,
                "pre_metrics": pre_unlock_metrics,
                "post_metrics": post_unlock_metrics,
                "deltas": deltas,
                "timestamp": time.time()
            })
            
            # Keep last 30 research events per faction
            if len(self.research_impacts[faction]) > 30:
                self.research_impacts[faction].pop(0)

    def get_live_metrics(self) -> Dict[str, Any]:
        """Returns aggregated stats for the current window (per second rates) plus totals."""
        now = time.time()
        cutoff = now - self.window_seconds
        
        with self.lock:
            # Prune old events
            self.battles = [t for t in self.battles if t > cutoff]
            
            # Prune and Count Units Spawned
            spawn_rates = {}
            for f in list(self.units_spawned.keys()):
                # Prune
                self.units_spawned[f]["navy"] = [t for t in self.units_spawned[f]["navy"] if t > cutoff]
                self.units_spawned[f]["army"] = [t for t in self.units_spawned[f]["army"] if t > cutoff]
                
                # Calc Rates
                spawn_rates[f] = {
                    "navy": len(self.units_spawned[f]["navy"]) / self.window_seconds,
                    "army": len(self.units_spawned[f]["army"]) / self.window_seconds
                }

            # Prune and Count Units Lost
            loss_rates = {}
            for f in list(self.units_lost.keys()):
                self.units_lost[f]["navy"] = [t for t in self.units_lost[f]["navy"] if t > cutoff]
                self.units_lost[f]["army"] = [t for t in self.units_lost[f]["army"] if t > cutoff]
                
                loss_rates[f] = {
                    "navy": len(self.units_lost[f]["navy"]) / self.window_seconds,
                    "army": len(self.units_lost[f]["army"]) / self.window_seconds
                }
            
            # Prune Construction
            const_rates = {}
            for f in list(self.construction.keys()):
                self.construction[f] = [t for t in self.construction[f] if t > cutoff]
                const_rates[f] = len(self.construction[f]) / self.window_seconds

            # Prune and Sum Resources
            resource_rates = {}
            revenue_by_category = {}
            for f in list(self.resource_flow.keys()):
                self.resource_flow[f] = [x for x in self.resource_flow[f] if x[0] > cutoff]
                if not self.resource_flow[f]:
                    del self.resource_flow[f]
                else:
                    total = sum(x[1] for x in self.resource_flow[f])
                    resource_rates[f] = total / self.window_seconds

                # Category Breakdown
                if f in self.categorized_revenue:
                    revenue_by_category[f] = {}
                    # Thread-safe iteration
                    for cat, entries in self.categorized_revenue[f].copy().items():
                        self.categorized_revenue[f][cat] = [e for e in entries if e[0] > cutoff]
                        if not self.categorized_revenue[f][cat]:
                            del self.categorized_revenue[f][cat]
                        else:
                            cat_total = sum(e[1] for e in self.categorized_revenue[f][cat])
                            revenue_by_category[f][cat] = cat_total / self.window_seconds

            # Prune Upkeep
            upkeep_breakdown = {}
            for f in list(self.upkeep_costs.keys()):
                # Thread-safe iteration
                self.upkeep_costs[f] = [e for e in list(self.upkeep_costs[f]) if e[0] > cutoff]
                if not self.upkeep_costs[f]:
                    del self.upkeep_costs[f]
                else:
                    mil = sum(e[1] for e in self.upkeep_costs[f] if e[2] == "military")
                    infra = sum(e[1] for e in self.upkeep_costs[f] if e[2] == "infrastructure")
                    upkeep_breakdown[f] = {
                        "military": mil / self.window_seconds,
                        "infrastructure": infra / self.window_seconds
                    }

            # Economic Health Section
            economic_health = {}
            for f in resource_rates.keys():
                profit_data = self.calculate_net_profit(f)
                velocity = self.calculate_stockpile_velocity(f)
                economic_health[f] = {
                    "net_profit": profit_data["net_profit"],
                    "gross_income": profit_data["gross_income"],
                    "total_upkeep": profit_data["total_upkeep"],
                    "stockpile_velocity": velocity,
                    "revenue_breakdown": revenue_by_category.get(f, {})
                }

            # Battle Performance Summary
            performance_summary = {}
            for f, battles in self.battle_performance.items():
                recent_battles = [b for b in battles if b["timestamp"] > cutoff]
                if recent_battles:
                    avg_cer = sum(b["cer"] for b in recent_battles) / len(recent_battles)
                    latest = recent_battles[-1]
                    performance_summary[f] = {
                        "avg_cer": avg_cer,
                        "latest_composition": latest["composition"],
                        "latest_attrition": latest["attrition"],
                        "recent_battle_count": len(recent_battles)
                    }

            battles_per_sec = len(self.battles) / self.window_seconds
            
            # Add construction activity summary
            construction_summary = {}
            if hasattr(self, 'construction_activity'):
                for f, activities in self.construction_activity.items():
                    recent = [a for a in activities if a["timestamp"] > cutoff]
                    if recent:
                        type_counts = {}
                        for a in recent:
                            bt = a["building_type"]
                            type_counts[bt] = type_counts.get(bt, 0) + 1
                        
                        avg_idle = sum(a["idle_slots"] for a in recent) / len(recent)
                        avg_efficiency = sum(a["queue_efficiency"] for a in recent) / len(recent)
                        
                        construction_summary[f] = {
                            "building_types": type_counts,
                            "avg_idle_slots": avg_idle,
                            "avg_queue_efficiency": avg_efficiency
                        }

            # Add research impact summary
            research_summary = {}
            if hasattr(self, 'research_impacts'):
                for f, impacts in self.research_impacts.items():
                    recent = [i for i in impacts if i["timestamp"] > cutoff]
                    if recent:
                        latest = recent[-1]
                        research_summary[f] = {
                            "latest_tech": latest["tech_id"],
                            "latest_deltas": latest["deltas"],
                            "recent_count": len(recent)
                        }
            
            return {
                "battles": {
                    "rate": round(battles_per_sec, 4),
                    "total": self.total_battles
                },
                "units": {
                    "spawn_rate": spawn_rates,
                    "loss_rate": loss_rates,
                    "total_spawned": self.total_units_spawned,
                    "total_lost": self.total_units_lost
                },
                "construction": {
                    "rate": const_rates,
                    "total": self.total_construction
                },
                "economy": {
                    "flow_rate": resource_rates,
                    "total_revenue": self.total_income,
                    "upkeep_breakdown": upkeep_breakdown
                },
                "economic_health": economic_health,
                "battle_performance": performance_summary,
                "construction_activity": construction_summary,
                "research_impact": research_summary
            }

    def reset(self):
        """Clears all aggregated metrics."""
        with self.lock:
            self.battles = []
            self.total_battles = 0
            self.units_spawned = {}
            self.total_units_spawned = 0
            self.units_lost = {}
            self.total_units_lost = 0
            self.construction = {}
            self.total_construction = 0
            self.resource_flow = {}
            self.total_income = 0.0
            self.upkeep_costs = {}
            self.total_upkeep = 0.0
            self.resource_stockpile_history = {}
            self.categorized_revenue = {}
            self.pending_economic_transactions = []
            self.battle_performance = {}
    def calculate_economic_health(self, faction: str, faction_obj) -> float:
        """
        Calculates a normalized economic health score (0.0 - 100.0) based on multiple factors.
        Implements the logic defined in logging_and_telemetry_improvements.md.
        """
        if not faction_obj:
            return 0.0
            
        # 1. Resource Stability (0-30)
        # Based on stockpile depth relative to upkeep
        upkeep = getattr(faction_obj, 'upkeep', 0)
        stockpile = getattr(faction_obj, 'requisition', 0)
        
        # Need at least 5 turns of upkeep for max score, or massive wealth
        turns_of_cover = stockpile / upkeep if upkeep > 0 else (10 if stockpile > 1000 else 0)
        score_stability = min(30.0, (turns_of_cover / 5.0) * 30.0)
        if stockpile > 10000: score_stability = 30.0
        
        # 2. Income Diversity (0-20)
        # Based on revenue_breakdown (Tax, Trade, Mining, Loot)
        breakdown = {}
        if faction in self.categorized_revenue:
            recent_rev = self.categorized_revenue[faction]
            # Sum recent amounts
            for cat, entries in recent_rev.items():
                 # Check last window
                 amt = sum(e[1] for e in entries if e[0] > (time.time() - self.window_seconds))
                 if amt > 0: breakdown[cat] = amt
        
        diversity_count = len(breakdown)
        score_diversity = min(20.0, diversity_count * 5.0) # 4 sources = max score
        
        # 3. Income Trend (0-20)
        # Positive Net Income = Good
        profit_data = self.calculate_net_profit(faction)
        net_inc = profit_data.get("net_profit", 0)
        gross = profit_data.get("gross_income", 1)
        
        margin = net_inc / gross if gross > 0 else 0
        if margin > 0.2: score_trend = 20.0
        elif margin > 0: score_trend = 15.0
        elif margin > -0.1: score_trend = 10.0 # Slight deficit
        elif margin > -0.5: score_trend = 5.0  # Heavy deficit
        else: score_trend = 0.0 # Collapse
        
        # 4. Debt Ratio (0-30)
        # Penalize if Requistion is negative or low compared to upkeep
        score_debt = 30.0
        if stockpile < 0:
             score_debt = 0.0
        elif stockpile < upkeep * 2:
             score_debt = 15.0
             
        total_score = score_stability + score_diversity + score_trend + score_debt
        return round(min(100.0, max(0.0, total_score)), 1)
        
    def log_economic_health_event(self, faction: str, faction_obj, telemetry_engine):
        """Calculates and logs the monthly health score."""
        score = self.calculate_economic_health(faction, faction_obj)
        
        # Advanced Metrics
        vol_data = self.calculate_economic_volatility(faction)
        velocity_data = self.calculate_stockpile_velocity(faction, extended=True)
        
        details = {
            "score": score,
            "stockpile": getattr(faction_obj, 'requisition', 0),
            "upkeep_load": getattr(faction_obj, 'upkeep', 0),
            "net_income": getattr(faction_obj, 'income', 0) - getattr(faction_obj, 'upkeep', 0),
            "volatility": vol_data.get("combined_volatility", 0.0),
            "volatility_details": vol_data,
            "stockpile_velocity": velocity_data
        }
        
        telemetry_engine.log_event(
            EventCategory.ECONOMY,
            "economic_health_score",
            details,
            faction=faction
        )
        return score

class TelemetryCollector:
    """
    Structured telemetry system for capturing granular campaign events.
    Supports buffering, batch writing, output verbosity, and real-time streaming.
    """
    def __init__(self, log_dir: str, verbosity: str = 'summary', batch_size: int = 10, universe_name: str = "unknown", logger: Optional[Any] = None):
        self.log_dir = log_dir
        self.verbosity = VerbosityLevel.from_str(verbosity)
        self.batch_size = batch_size
        self.universe_name = universe_name
        self.logger = logger
        self.buffer: List[Dict[str, Any]] = []
        
        # Streaming support
        self.streaming_enabled = False
        self.stream_buffer = queue.Queue()
        self.stream_subscribers: List[Callable[[Dict], None]] = []
        self.subscribers_lock = threading.Lock()
        
        # Live Metrics
        self.metrics = MetricsAggregator()
        self.metrics_window = 60
        self.current_turn = 0
        self.latest_faction_status = {}
        self.latest_planet_status = []
        
        # Performance Tracking
        self.performance_bottlenecks: Dict[str, List[Dict[str, Any]]] = {}
        self.operation_timings: Dict[str, List[float]] = {}
        self.bottleneck_threshold = 1.0  # seconds
        
        # Memory Tracking
        self.memory_history: List[Dict[str, Any]] = []
        self.memory_baseline = 0
        self.memory_alert_threshold = 500 * 1024 * 1024  # 500 MB
        
        # Initialize memory baseline
        self._initialize_memory_baseline()
        
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
        # Standardized Telemetry File (Redesign Phase 2)
        # Uses NDJSON format (handled by flush method)
        self.log_file = os.path.join(self.log_dir, "events.json")
        
        # Memory baseline tracking
        self._initialize_memory_baseline()

        # 4. Integrate with AlertManager
        try:
            from src.reporting.alert_manager import AlertManager
            am = AlertManager()
            self.subscribe(am.process_telemetry_event)
        except (ImportError, Exception):
            pass

        # Remote Streaming
        self.remote_url = None
        self.remote_queue = None
        self.batch_id = "unknown"

        # [R1] Background Batcher
        self.event_queue = queue.Queue()
        self.batcher = EventBatcher(self)
        self.batcher.queue = self.event_queue  # Link queues
        self.batcher.batch_id = self.batch_id # initial
        self.batcher.start()

    def set_indexer(self, indexer):
        """Attaches an indexer for background DB writes."""
        if hasattr(self, 'batcher'):
            self.batcher.indexer = indexer

    def _initialize_memory_baseline(self):
        """Initialize memory usage baseline for comparison."""
        try:
            process = psutil.Process()
            self.memory_baseline = process.memory_info().rss
        except:
            self.memory_baseline = 0
    
    def track_operation_time(self, operation_name: str, duration: float, context: Dict[str, Any] = None):
        """
        Track operation execution time for bottleneck detection.
        
        Args:
            operation_name: Name of the operation being tracked
            duration: Execution time in seconds
            context: Additional context about the operation
        """
        if operation_name not in self.operation_timings:
            self.operation_timings[operation_name] = []
        
        self.operation_timings[operation_name].append(duration)
        
        # Keep only last 100 measurements
        if len(self.operation_timings[operation_name]) > 100:
            self.operation_timings[operation_name] = self.operation_timings[operation_name][-100:]
        
        # Check for bottleneck
        if duration > self.bottleneck_threshold:
            if operation_name not in self.performance_bottlenecks:
                self.performance_bottlenecks[operation_name] = []
            
            bottleneck_data = {
                'timestamp': time.time(),
                'turn': self.current_turn,
                'duration': duration,
                'threshold': self.bottleneck_threshold,
                'context': context or {}
            }
            
            self.performance_bottlenecks[operation_name].append(bottleneck_data)
            
            # Keep only last 50 bottlenecks per operation
            if len(self.performance_bottlenecks[operation_name]) > 50:
                self.performance_bottlenecks[operation_name] = self.performance_bottlenecks[operation_name][-50:]
            
            # Log bottleneck event
            self.log_event(
                EventCategory.SYSTEM,
                'performance_bottleneck',
                {
                    'operation': operation_name,
                    'duration': duration,
                    'threshold': self.bottleneck_threshold,
                    'context': context or {},
                    'avg_duration': sum(self.operation_timings[operation_name]) / len(self.operation_timings[operation_name])
                },
                turn=self.current_turn
            )
    
    def log_memory_usage(self, context: Dict[str, Any] = None):
        """
        Log current memory usage for tracking and alerting.
        
        Args:
            context: Additional context about memory state
        """
        try:
            process = psutil.Process()
            mem_info = process.memory_info()
            
            # Get garbage collection stats
            gc_stats = gc.get_stats()
            gc_count = gc.get_count()
            
            memory_data = {
                'timestamp': time.time(),
                'turn': self.current_turn,
                'rss': mem_info.rss,  # Resident Set Size
                'vms': mem_info.vms,  # Virtual Memory Size
                'rss_mb': mem_info.rss / (1024 * 1024),
                'vms_mb': mem_info.vms / (1024 * 1024),
                'rss_delta': mem_info.rss - self.memory_baseline,
                'rss_delta_mb': (mem_info.rss - self.memory_baseline) / (1024 * 1024),
                'gc_count': gc_count,
                'gc_stats': gc_stats,
                'context': context or {}
            }
            
            self.memory_history.append(memory_data)
            
            # Keep only last 100 memory snapshots
            if len(self.memory_history) > 100:
                self.memory_history = self.memory_history[-100:]
            
            # Phase 13: Memory Leak Detection (Refinement)
            leak_detected = False
            leak_rate = 0.0
            if len(self.memory_history) >= 5:
                # Check for consistent growth over last 5 snapshots
                recent = self.memory_history[-5:]
                growth = [recent[i]['rss_mb'] - recent[i-1]['rss_mb'] for i in range(1, len(recent))]
                if all(g > 0.05 for g in growth): # > 0.05MB growth per step consistently
                    leak_detected = True
                    leak_rate = sum(growth) / len(growth)
            
            # Check for memory alert
            if mem_info.rss > self.memory_alert_threshold or leak_detected:
                self.log_event(
                    EventCategory.SYSTEM,
                    'memory_alert',
                    {
                        'rss_mb': mem_info.rss / (1024 * 1024),
                        'vms_mb': mem_info.vms / (1024 * 1024),
                        'threshold_mb': self.memory_alert_threshold / (1024 * 1024),
                        'leak_detected': leak_detected,
                        'leak_rate_mb_per_turn': leak_rate,
                        'context': context or {}
                    },
                    turn=self.current_turn
                )
            
            # Log regular memory usage
            self.log_event(
                EventCategory.SYSTEM,
                'memory_usage',
                {
                    'rss_mb': mem_info.rss / (1024 * 1024),
                    'vms_mb': mem_info.vms / (1024 * 1024),
                    'rss_delta_mb': (mem_info.rss - self.memory_baseline) / (1024 * 1024),
                    'leak_detected': leak_detected,
                    'leak_rate': leak_rate,
                    'gc_count': gc_count,
                    'context': context or {}
                },
                turn=self.current_turn,
                level=VerbosityLevel.SUMMARY
            )
        except Exception as e:
            if self.logger:
                self.logger.warning(f"Failed to log memory usage: {e}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get summary of performance metrics including bottlenecks and memory usage.
        
        Returns:
            Dictionary with performance statistics
        """
        summary = {
            'operation_timings': {},
            'bottlenecks': {},
            'memory_summary': {}
        }
        
        # Summarize operation timings
        for op_name, timings in self.operation_timings.items():
            if timings:
                summary['operation_timings'][op_name] = {
                    'count': len(timings),
                    'avg': sum(timings) / len(timings),
                    'min': min(timings),
                    'max': max(timings),
                    'last': timings[-1]
                }
        
        # Summarize bottlenecks
        for op_name, bottlenecks in self.performance_bottlenecks.items():
            if bottlenecks:
                summary['bottlenecks'][op_name] = {
                    'count': len(bottlenecks),
                    'avg_duration': sum(b['duration'] for b in bottlenecks) / len(bottlenecks),
                    'max_duration': max(b['duration'] for b in bottlenecks),
                    'last_turn': bottlenecks[-1]['turn']
                }
        
        # Summarize memory usage
        if self.memory_history:
            latest = self.memory_history[-1]
            summary['memory_summary'] = {
                'current_rss_mb': latest['rss_mb'],
                'current_vms_mb': latest['vms_mb'],
                'delta_mb': latest['rss_delta_mb'],
                'baseline_mb': self.memory_baseline / (1024 * 1024),
                'gc_count': latest['gc_count']
            }
        
        return summary

    def set_batch_id(self, batch_id: str):
        self.batch_id = batch_id
        if hasattr(self, 'batcher'):
            self.batcher.batch_id = batch_id

    def set_run_id(self, run_id: str):
        if hasattr(self, 'batcher'):
            self.batcher.run_id = run_id

    def enable_remote_streaming(self, url: str):
        """Enables forwarding events to a remote dashboard via HTTP."""
        self.remote_url = url
        self.remote_queue = queue.Queue()
        # Start background sender
        t = threading.Thread(target=self._remote_sender_loop, daemon=True)
        t.start()
        print(f"[TELEMETRY] Remote streaming enabled to {url}")

    def _remote_sender_loop(self):
        import requests
        batch = []
        last_send = time.time()
        while True:
            try:
                try:
                    event = self.remote_queue.get(timeout=0.5)
                    batch.append(event)
                except queue.Empty:
                    pass
                
                now = time.time()
                if batch and (len(batch) >= 10 or now - last_send > 1.0):
                    try:
                        requests.post(self.remote_url, json={
                            "events": batch, 
                            "batch_id": self.batch_id
                        }, timeout=2)
                    except Exception as req_err:
                        # Silently fail or log sparingly?
                        pass 
                    batch = []
                    last_send = now
            except Exception as e:
                # print(f"Remote Send Error: {e}")
                time.sleep(1)

    def process_remote_event(self, event: Dict):
        """Ingest event from remote source (Dashboard Receiver)."""
        try:
            cat_str = event.get('category')
            # Handle Enum conversion
            try:
                cat = EventCategory(cat_str)
            except ValueError:
                # Check match by value
                cat = next((e for e in EventCategory if e.value == cat_str), None)
            
            if not cat: return

            etype = event.get('event_type')
            faction = event.get('faction')
            data = event.get('data', {})
            turn = event.get('turn')
            
            if turn is not None: self.current_turn = turn

            # 1. Update Metrics
            self._update_metrics(cat, etype, faction, data)
            
            # 2. Update Status Caches
            if cat == EventCategory.CAMPAIGN and etype == "turn_status":
                 self.latest_faction_status = data
            elif cat == EventCategory.SYSTEM and etype == "planet_update":
                 self.latest_planet_status = data.get("planets", [])

            # 3. Stream Broadcast (for Websocket & Indexer)
            if self.streaming_enabled:
                self.stream_buffer.put(event)
                self.broadcast_event(event)
                
        except Exception as e:
            print(f"Error processing remote event: {e}")

    def enable_streaming(self):
        self.streaming_enabled = True

    def disable_streaming(self):
        self.streaming_enabled = False

    def subscribe(self, callback: Callable[[Dict], None]):
        with self.subscribers_lock:
            if callback not in self.stream_subscribers:
                self.stream_subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Dict], None]):
        with self.subscribers_lock:
            if callback in self.stream_subscribers:
                self.stream_subscribers.remove(callback)

    def get_stream_buffer(self) -> List[Dict]:
        """Polls current stream buffer for polling-based clients."""
        items = []
        try:
            while True:
                items.append(self.stream_buffer.get_nowait())
        except queue.Empty:
            pass
        return items
        
    def get_live_metrics(self) -> Dict[str, Any]:
        data = self.metrics.get_live_metrics()
        data["turn"] = self.current_turn
        data["faction_status"] = self.latest_faction_status
        data["planet_status"] = self.latest_planet_status
        return data

    def record_economic_snapshot(self, faction: str, gross_income: int, upkeep: int, stockpile: int):
        """Helper to record point-in-time economic health markers."""
        self.metrics.record_stockpile_snapshot(faction, float(stockpile))

    def record_resource_spend(self, faction: str, amount: float, category: str, source_planet: str = None):
        """Proxy for recording capital expenditures."""
        self.metrics.record_resource_spend(faction, amount, category, source_planet)
        
        self.log_event(
            category=EventCategory.ECONOMY,
            event_type="resource_transaction",
            faction=faction,
            data={
                "category": category,
                "amount": -float(amount),
                "planet": source_planet
            }
        )

    def set_verbosity(self, level: str):
        self.verbosity = VerbosityLevel.from_str(level)
        
    def reset(self):
        """Reset internal metrics and state for a new run."""
        self.current_turn = 0
        self.latest_faction_status = {}
        self.latest_planet_status = []
        self.metrics.reset()
        # Clear buffer? Maybe flush first?
        # Ideally we start fresh.
        self.buffer = []

    def log_event(self, category: EventCategory, event_type: str, data: Dict[str, Any], 
                  turn: Optional[int] = None, faction: Optional[str] = None, 
                  level: VerbosityLevel = VerbosityLevel.SUMMARY):
        """
        Logs an event if its level is within the current verbosity settings.
        Also broadcasts to stream if enabled.
        """
        if level.value > self.verbosity.value:
            return

        if turn is not None:
             self.current_turn = turn
        
        # Use current_turn fallback if turn not explicitly provided
        effective_turn = turn if turn is not None else self.current_turn

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "universe": self.universe_name,
            "category": category.value,
            "event_type": event_type,
            "turn": effective_turn,
            "faction": faction,
            "data": data
        }
        
        # 1. Update Live Metrics
        self._update_metrics(category, event_type, faction, data)
        
        # Special Handler for Turn Status
        if category == EventCategory.CAMPAIGN and event_type == "turn_status":
             self.latest_faction_status = data
        elif category == EventCategory.SYSTEM and event_type == "planet_update":
             self.latest_planet_status = data.get("planets", [])
        
        # 2. Add to background queue
        self.event_queue.put(event)
        
        # 3. Stream Broadcast
        if self.streaming_enabled:
            self.stream_buffer.put(event)
            self.broadcast_event(event)

        if self.remote_queue:
            self.remote_queue.put(event)

        if self.logger:
            try:
                self.logger.info(f"Event: {event_type}", 
                    event_type=event_type, 
                    event_category=category.value, 
                    data=data,
                    faction=faction,
                    turn=turn,
                    timestamp=event["timestamp"],
                    universe=self.universe_name
                )
            except:
                pass
            
    def _update_metrics(self, category: EventCategory, event_type: str, faction: Optional[str], data: Dict):
        if category == EventCategory.COMBAT and event_type == "battle_start":
            self.metrics.record_battle()
        elif category == EventCategory.CONSTRUCTION and event_type == "unit_built" and faction:
            u_type = data.get("type", "army")
            self.metrics.record_unit_spawn(faction, u_type)
        elif category == EventCategory.CONSTRUCTION and event_type == "unit_destroyed" and faction:
            self.metrics.record_unit_loss(faction)
        elif category == EventCategory.CONSTRUCTION and event_type == "unit_losses_report" and faction:
            count = data.get("count", 1)
            navy = data.get("navy", 0)
            army = data.get("army", 0)
            self.metrics.record_unit_loss(faction, count, navy_count=navy, army_count=army)
        elif category == EventCategory.CONSTRUCTION and event_type == "construction_complete" and faction:
            self.metrics.record_construction(faction)
        elif category == EventCategory.ECONOMY and event_type == "income_collected" and faction:
            amount = data.get("amount", 0)
            self.metrics.record_resource_gain(faction, amount)

    def broadcast_event(self, event: Dict):
        """Push event to all active subscribers directly."""
        with self.subscribers_lock:
            # Copy list to avoid issues if subscriber removes self during callback
            # treating subscribers as direct callbacks implies same thread or fast execution
            # Ideally this is purely for internal signaling or queue pushing
            for callback in list(self.stream_subscribers):
                try:
                    callback(event)
                except Exception as e:
                    # Log error? remove subscriber?
                    pass

    def log_performance_summary(self, metrics: Dict[str, Any], turn: int):
        """Logs aggregated performance metrics for the turn."""
        self.log_event(EventCategory.SYSTEM, "performance_summary", metrics, turn=turn, level=VerbosityLevel.SUMMARY)

    def flush(self):
        """
        Writes buffered events to the JSON log file.
        """
        if not self.buffer:
            return
            
        try:
            self._write_to_disk(self.buffer)
            self.buffer = []
        except Exception as e:
            pass

    def _write_to_disk(self, batch: List[Dict]):
        """Internal helper for writing to the NDJSON file."""
        if not batch: return
        try:
            with _open(self.log_file, "a") as f:
                for event in batch:
                    f.write(json.dumps(event) + "\n")
        except Exception as e:
            try:
                print(f"Failed to write telemetry: {e}")
            except:
                pass

    def flush_economic_data(self, indexer, batch_id: str, run_id: str, universe: str, turn: int):
        """Flushes categorized economic transactions to the persistent indexer."""
        transactions = []
        with self.metrics.lock:
            # Consume pending transactions from buffer
            for tx in self.metrics.pending_economic_transactions:
                transactions.append({
                    "batch_id": batch_id,
                    "run_id": run_id,
                    "turn": turn,
                    "faction": tx["faction"],
                    "category": tx["category"],
                    "amount": int(tx["amount"]),
                    "source_planet": tx["source_planet"],
                    "timestamp": datetime.fromtimestamp(tx["timestamp"]).isoformat()
                })
            # Clear buffer after processing
            self.metrics.pending_economic_transactions.clear()
        
        if transactions and indexer:
            indexer.index_realtime_resource_transactions(batch_id, run_id, transactions, universe)

    def flush_battle_performance_data(self, indexer, batch_id: str, run_id: str, universe: str, turn: int):
        """Flushes battle performance metrics to the persistent indexer."""
        performances = []
        with self.metrics.lock:
            for faction, battles in self.metrics.battle_performance.items():
                for battle in battles:
                    performances.append({
                        "batch_id": batch_id,
                        "run_id": run_id,
                        "battle_id": battle["battle_id"],
                        "faction": faction,
                        "damage_dealt": battle["damage_dealt"],
                        "resources_lost": battle["resources_lost"],
                        "force_composition": battle["composition"],
                        "cer": battle["cer"],
                        "attrition_rate": battle.get("attrition", 0.0),
                        "turn": turn,
                        "timestamp": datetime.fromtimestamp(battle["timestamp"]).isoformat()
                    })
            self.metrics.battle_performance.clear()
            
        if performances and indexer:
            indexer.index_realtime_battle_performance(batch_id, run_id, performances, universe)

    def generate_index(self) -> None:
        """
        [REPORTING] Scans the events.json file and generates an index.json.
        Maps events to turns and categories for efficient lookups.
        """
        if not self.log_file or not os.path.exists(self.log_file):
            return

        index_data = {
            "total_events": 0,
            "turns": {},
            "categories": {}
        }
        
        try:
            with open(self.log_file, 'r') as f:
                for line_no, line in enumerate(f):
                    if not line.strip(): continue
                    try:
                        event = json.loads(line)
                        cat = event.get("category", "unknown")
                        turn = event.get("turn", -1)
                        
                        # Update Stats
                        index_data["total_events"] += 1
                        
                        # Turn Index
                        if turn not in index_data["turns"]:
                            index_data["turns"][turn] = {"count": 0, "categories": {}}
                        index_data["turns"][turn]["count"] += 1
                        index_data["turns"][turn]["categories"][cat] = index_data["turns"][turn]["categories"].get(cat, 0) + 1
                        
                        # Category Index
                        if cat not in index_data["categories"]:
                            index_data["categories"][cat] = 0
                        index_data["categories"][cat] += 1
                        
                    except json.JSONDecodeError:
                        continue
                        
            # Write Index
            index_path = os.path.join(os.path.dirname(self.log_file), "index.json")
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
                
            print(f"[TELEMETRY] Index generated: {index_path} ({index_data['total_events']} events)")
            
        except Exception as e:
            print(f"[TELEMETRY] Failed to generate index: {e}")

    def shutdown(self):
        """Cleanly shuts down the background batcher."""
        if hasattr(self, 'batcher'):
            self.batcher.stop()

    def __del__(self):
        self.shutdown()
        self.flush()

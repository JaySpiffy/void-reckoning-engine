
import json
from void_reckoning_bridge import RustEconomyEngine

class RustEconomyWrapper:
    def __init__(self):
        self.engine = RustEconomyEngine()
        self.SCALE_FACTOR = 1_000_000
        # Enable Event Logging
        try:
            self._event_log = self.engine.enable_event_logging()
        except Exception as e:
            print(f"Warning: Failed to enable economy event logging: {e}")
            self._event_log = None

    def flush_logs(self, telemetry_logger):
        """
        Retrieves events from Rust and flushes them to the Python telemetry logger.
        """
        if not hasattr(self, '_event_log') or not self._event_log:
            return

        try:
            events = self._event_log.get_all()
            if not events: return
            
            from src.reporting.telemetry import EventCategory
            
            for evt in events:
                # evt.severity: "Info", "Warning", "Error"
                
                cat = EventCategory.ECONOMY
                if evt.category: # Rust category string
                    pass # mapped automatically?
                
                telemetry_logger.log_event(
                    cat, 
                    "economy_event", 
                    {
                        "severity": evt.severity,
                        "category": evt.category,
                        "message": evt.message,
                        "context": evt.context.trace_id if evt.context else None
                    }
                )
            
            # Clear log 
            self._event_log.clear()
            
        except Exception as e:
            print(f"Failed to flush economy logs: {e}")

    def to_fixed(self, value):
        return int(value * self.SCALE_FACTOR)

    def from_fixed(self, value):
        return float(value) / self.SCALE_FACTOR

    def set_rules(self, 
                  orbit_discount=0.5, 
                  garrison_discount=0.25, 
                  navy_penalty_ratio=4, 
                  navy_penalty_rate=0.05, 
                  vassal_tribute_rate=0.2,
                  fleet_upkeep_scalar=1.0):
        """Sets global economic rules for the engine."""
        rules = {
            "orbit_discount_scaled": self.to_fixed(orbit_discount),
            "garrison_discount_scaled": self.to_fixed(garrison_discount),
            "navy_penalty_ratio": int(navy_penalty_ratio),
            "navy_penalty_rate_scaled": self.to_fixed(navy_penalty_rate),
            "vassal_tribute_rate_scaled": self.to_fixed(vassal_tribute_rate),
            "fleet_upkeep_scalar_scaled": self.to_fixed(fleet_upkeep_scalar)
        }
        self.engine.set_rules(json.dumps(rules))

    def add_node(self, node_id, owner_faction, node_type, base_income, base_upkeep, efficiency=1.0, modifiers=None):
        """
        Adds an economic node to the engine.
        base_income: dict of {resource: value}
        base_upkeep: dict of {resource: value}
        """
        keys = ["credits", "minerals", "energy", "research"]
        
        income_fixed = {k: self.to_fixed(base_income.get(k, 0)) for k in keys}
        upkeep_fixed = {k: self.to_fixed(base_upkeep.get(k, 0)) for k in keys}
        
        node_data = {
            "id": node_id,
            "owner_faction": owner_faction,
            "node_type": node_type,
            "base_income": income_fixed,
            "base_upkeep": upkeep_fixed,
            "efficiency_scaled": self.to_fixed(efficiency),
            "modifiers": []
        }
        
        if modifiers:
            for mod in modifiers:
                node_data["modifiers"].append({
                    "name": mod.get("name", "Unknown"),
                    "multiplier_scaled": self.to_fixed(mod.get("multiplier", 1.0)),
                    "flat_bonus": {k: self.to_fixed(mod.get("flat", {}).get(k, 0)) for k in keys}
                })
        
        self.engine.add_node(json.dumps(node_data))

    def add_trade_route(self, from_sys, to_sys, base_value):
        """
        Add a trade route between two systems.
        base_value: {"credits": x, ...}
        """
        route_data = {
            "from": from_sys,
            "to": to_sys,
            "base_value": {k: self.to_fixed(v) for k, v in base_value.items()},
            "efficiency_scaled": self.SCALE_FACTOR
        }
        self.engine.add_trade_route(json.dumps(route_data))

    def calculate_trade(self, rust_pathfinder):
        """
        rust_pathfinder: Instance of RustPathfinder from bridge.
        """
        res_json = self.engine.calculate_trade(rust_pathfinder)
        raw_data = json.loads(res_json)
        
        processed = {}
        for sys_id, resources in raw_data.items():
            processed[sys_id] = {k: self.from_fixed(v) for k, v in resources.items()}
        return processed

    def get_faction_report(self, faction_name):
        res_json = self.engine.process_faction(faction_name)
        report = json.loads(res_json)
        
        for key in ["total_income", "total_upkeep", "net_profit"]:
            report[key] = {k: self.from_fixed(v) for k, v in report[key].items()}
            
        if "income_by_category" in report:
            for cat, resources in report["income_by_category"].items():
                report["income_by_category"][cat] = {k: self.from_fixed(v) for k, v in resources.items()}
                
        return report

    def get_all_reports(self):
        res_json = self.engine.process_all()
        reports = json.loads(res_json)
        
        for faction, report in reports.items():
            for key in ["total_income", "total_upkeep", "net_profit"]:
                report[key] = {k: self.from_fixed(v) for k, v in report[key].items()}
            
            if "income_by_category" in report:
                for cat, resources in report["income_by_category"].items():
                    report["income_by_category"][cat] = {k: self.from_fixed(v) for k, v in resources.items()}
        return reports
    
    def reset(self):
        """Re-initializes the engine to clear all nodes and routes."""
        self.engine = RustEconomyEngine()

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'engine' in state: del state['engine']
        if '_event_log' in state: del state['_event_log']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        # Re-initialize Rust backend
        self.engine = RustEconomyEngine()
        try:
            self._event_log = self.engine.enable_event_logging()
        except:
            self._event_log = None

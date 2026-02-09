
import os
import json
import logging
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class EventIndexerMixin:
    """Handles the ingestion of simulation events, stats, and logs into the database."""

    def index_batch(self, batch_path: str):
        """Crawler for entire batch directory."""
        if not os.path.exists(batch_path):
            logger.error(f"Batch path {batch_path} does not exist.")
            return
        
        # Identify universe from path if possible
        universe = os.path.basename(os.path.dirname(batch_path)) or "unknown"
        
        for run_name in os.listdir(batch_path):
            run_path = os.path.join(batch_path, run_name)
            if os.path.isdir(run_path) and run_name.startswith("run_"):
                self.index_run(run_path, universe)

    def index_run(self, run_path: str, universe: str = "unknown"):
        """Index a single simulation run safely with incremental updates."""
        run_name = os.path.basename(run_path)
        batch_id = os.path.basename(os.path.dirname(run_path))
        
        if self._is_indexed(batch_id, run_name, universe):
            logger.info(f"Run {run_name} in {batch_id} already indexed. Skipping.")
            return

        logger.info(f"Indexing Run: {run_name} (Universe: {universe})")
        
        # 1. Basic Metadata
        self._insert_run_metadata(batch_id, run_name, run_path, universe)
        
        # 2. Iterate Turns
        max_turn = 0
        winner = None
        
        # Sort turns numerically
        turns = sorted([d for d in os.listdir(run_path) if d.startswith("turn_")])
        for turn_dir in turns:
            turn_path = os.path.join(run_path, turn_dir)
            try:
                turn_num = int(turn_dir.split("_")[1])
                max_turn = max(max_turn, turn_num)
            except: turn_num = 0
            
            # A. Process Telemetry Events
            telemetry_path = os.path.join(turn_path, "telemetry.json")
            if os.path.exists(telemetry_path):
                events = self._parse_telemetry_file(telemetry_path)
                self._insert_events(batch_id, run_name, events, universe)
            
            # B. Process Faction Summaries
            faction_dir = os.path.join(turn_path, "factions")
            if os.path.exists(faction_dir):
                for f_file in os.listdir(faction_dir):
                    if f_file.endswith(".json") and f_file != "manifest.json":
                        f_data = self._parse_faction_summary(os.path.join(faction_dir, f_file))
                        if f_data:
                            self._insert_faction_stats(batch_id, run_name, turn_num, f_data, universe)
            
            # C. Process Battles
            combat_dir = os.path.join(turn_path, "battles")
            if os.path.exists(combat_dir):
                for b_file in os.listdir(combat_dir):
                    if b_file.endswith(".json") and b_file != "manifest.json":
                        b_data = self._parse_combat_log(os.path.join(combat_dir, b_file))
                        if b_data:
                            self._insert_battle(batch_id, run_name, turn_num, b_data, universe)
                            # Update winner if it's the final turn
                            if b_data.get("is_final"):
                                winner = b_data.get("summary", {}).get("winner")

        # 3. Finalize Run Info
        self._insert_run_info(batch_id, run_name, run_path, max_turn, winner=winner, universe=universe)
        self.conn.commit()

    def _is_indexed(self, batch_id: str, run_id: str, universe: str) -> bool:
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM runs WHERE universe=? AND run_id=? AND batch_id=?", (universe, run_id, batch_id))
        return cursor.fetchone() is not None

    def _parse_telemetry_file(self, path: str) -> List[Dict[str, Any]]:
        events = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try: events.append(json.loads(line))
                        except: continue
        except Exception as e:
            logger.error(f"Error parsing telemetry {path}: {e}")
        return events

    def _parse_faction_summary(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception as e:
            logger.error(f"Error parsing faction summary {path}: {e}")
            return None

    def _parse_combat_log(self, path: str) -> Optional[Dict[str, Any]]:
        try:
            with open(path, "r", encoding="utf-8") as f: return json.load(f)
        except Exception as e:
            logger.error(f"Error parsing combat log {path}: {e}")
            return None

    def index_realtime_events(self, batch_id: str, run_id: str, events: List[Dict[str, Any]], universe: str):
        if not events: return
        try:
            with self._lock:
                self._insert_events(batch_id, run_id, events, universe)
                self.conn.commit()
        except Exception as e: logger.error(f"Error indexing realtime events: {e}")

    def index_realtime_resource_transactions(self, batch_id: str, run_id: str, 
                                              transactions: List[Dict[str, Any]], universe: str):
        if not transactions: return
        try:
            with self._lock:
                self._bulk_insert_resource_transactions(transactions, universe)
                self.conn.commit()
        except Exception as e: logger.error(f"Error indexing realtime transactions: {e}")

    def index_realtime_battle_performance(self, batch_id: str, run_id: str,
                                             performances: List[Dict[str, Any]], universe: str):
        if not performances: return
        try:
            with self._lock:
                self._bulk_insert_battle_performance(performances, universe)
                self.conn.commit()
        except Exception as e: logger.error(f"Error indexing realtime performances: {e}")

    def _insert_events(self, batch_id: str, run_id: str, events: List[Dict[str, Any]], universe: str):
        cursor = self.conn.cursor()
        batch_data = []
        resource_transactions = []
        
        for e in events:
            data = e.get("data", {})
            if not isinstance(data, dict): data = {"raw": data}
            
            # Extract Trace IDs
            details = e.get("details", {})
            context = e.get("context", {})
            
            trace_id = e.get("trace_id") or data.get("trace_id") or details.get("trace_id") or context.get("trace_id")
            parent_trace_id = e.get("parent_trace_id") or data.get("parent_trace_id") or details.get("parent_trace_id") or context.get("parent_id")

            batch_data.append((
                batch_id, universe, run_id, e.get("turn"), e.get("timestamp"),
                e.get("category"), e.get("event_type"), e.get("faction"),
                data.get("location") or data.get("planet") or data.get("system"),
                data.get("entity_type"),
                data.get("entity_name") or data.get("unit") or data.get("fleet"),
                json.dumps(data),
                self._extract_keywords(e),
                trace_id,
                parent_trace_id
            ))
            
            # Map economic events
            event_type = e.get("event_type")
            if event_type in ["income_collected", "construction_started", "construction_complete", "research_complete", "unit_recruited"]:
                self._handle_economic_event(batch_id, run_id, e, data, universe, resource_transactions)
            elif event_type == "resource_transaction":
                resource_transactions.append({
                    "batch_id": batch_id, "universe": universe, "run_id": run_id,
                    "turn": e.get("turn"), "faction": e.get("faction"),
                    "category": str(data.get("category", "Other")).title(),
                    "amount": data.get("amount"),
                    "source_planet": data.get("planet") or data.get("location"),
                    "timestamp": e.get("timestamp")
                })

        cursor.executemany("""
            INSERT INTO events (
                batch_id, universe, run_id, turn, timestamp, category, event_type, 
                faction, location, entity_type, entity_name, data_json, keywords,
                trace_id, parent_trace_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)
        
        if resource_transactions:
            self._bulk_insert_resource_transactions(resource_transactions, universe)

    def _handle_economic_event(self, batch_id, run_id, e, data, universe, transactions):
        event_type = e.get("event_type")
        if event_type == "income_collected":
            breakdown = data.get("breakdown", {})
            if breakdown:
                for cat, amt in breakdown.items():
                    if amt > 0:
                        transactions.append({
                            "batch_id": batch_id, "universe": universe, "run_id": run_id,
                            "turn": e.get("turn"), "faction": e.get("faction"),
                            "category": str(cat).title(), "amount": amt,
                            "source_planet": data.get("planet") or data.get("location"),
                            "timestamp": e.get("timestamp")
                        })
                return # Don't add base income
            amount = data.get("net", 0)
            cat = "Income"
        elif event_type in ["construction_started", "construction_complete"]:
            amount = -data.get("cost", 0)
            cat = "Construction"
        elif event_type == "research_complete":
            amount = -data.get("cost", 0)
            cat = "Research"
        elif event_type == "unit_recruited":
            amount = -data.get("cost", 0)
            cat = "Recruitment"
        else: return

        if amount != 0:
            transactions.append({
                "batch_id": batch_id, "universe": universe, "run_id": run_id,
                "turn": e.get("turn"), "faction": e.get("faction"),
                "category": cat, "amount": amount,
                "source_planet": data.get("planet") or data.get("location"),
                "timestamp": e.get("timestamp")
            })

    def _insert_faction_stats(self, batch_id, run_id, turn, data, universe):
        cursor = self.conn.cursor()
        econ = data.get("economy", {})
        mil = data.get("military", {})
        terr = data.get("territory", {})
        deltas = data.get("deltas", {})
        const = data.get("construction_activity", {})
        res = data.get("research_impact", {})
        tech = data.get("tech_depth", {})
        
        b_types = const.get("building_types", {})
        
        cursor.execute("""
            INSERT INTO factions (
                batch_id, universe, run_id, turn, faction, requisition, promethium,
                upkeep_total, gross_income, net_profit, research_points,
                idle_construction_slots, idle_research_slots,
                planets_controlled, fleets_count, units_recruited, units_lost,
                battles_fought, battles_won, damage_dealt, 
                construction_efficiency, military_building_count, 
                economy_building_count, research_building_count, 
                research_delta_requisition, data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, universe, run_id, turn, data.get("faction"),
            deltas.get("requisition", 0), econ.get("promethium", 0),
            econ.get("upkeep_total", 0), econ.get("gross_income", 0),
            econ.get("net_profit", 0), tech.get("unlocked_count", 0) if tech else econ.get("research_points", 0),
            int(const.get("avg_idle_slots", 0)), econ.get("idle_research_slots", 0),
            terr.get("total_controlled", 0), deltas.get("fleets_count", 0),
            mil.get("units_recruited", 0), mil.get("units_lost", 0),
            mil.get("battles_fought", 0), mil.get("battles_won", 0),
            mil.get("damage_dealt", 0), const.get("avg_queue_efficiency", 0.0),
            b_types.get("Military", 0), b_types.get("Economy", 0), b_types.get("Research", 0),
            res.get("latest_deltas", {}).get("requisition", 0), json.dumps(data)
        ))

    def _insert_battle(self, batch_id, run_id, turn, data, universe):
        cursor = self.conn.cursor()
        summary = data.get("summary", {})
        factions_involved = summary.get("factions", {})
        total_dmg = sum(f.get("damage", 0) for f in factions_involved.values())
        
        cursor.execute("""
            INSERT INTO battles (
                batch_id, universe, run_id, turn, location, factions_involved,
                winner, duration_rounds, total_damage, units_destroyed, data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, universe, run_id, turn, data.get("location") or data.get("planet"),
            ",".join(factions_involved.keys()), summary.get("winner"),
            summary.get("total_rounds"), total_dmg, summary.get("total_kills"),
            json.dumps(data)
        ))

        battle_id = data.get("id", f"BATTLE_{turn}_{run_id[-4:]}")
        for f_name, f_stats in factions_involved.items():
            try:
                dmg = f_stats.get("damage", 0.0)
                losses = f_stats.get("losses", 0.0)
                comp = f_stats.get("force", {})
                total_f = sum(comp.values()) if comp else 1
                attr = losses / total_f if total_f > 0 else 0.0
                
                self._insert_battle_performance(
                    batch_id, run_id, turn, battle_id, f_name, dmg, losses, comp, attr, universe
                )
            except Exception as e: logger.error(f"Failed to insert performance for {f_name}: {e}")

    def _insert_battle_performance(self, batch_id, run_id, turn, battle_id, faction, damage_dealt, resources_lost, force_composition, attrition_rate=0.0, universe="unknown"):
        cursor = self.conn.cursor()
        cer = damage_dealt / resources_lost if resources_lost > 0 else 0.0
        cursor.execute("""
            INSERT INTO battle_performance (
                batch_id, universe, run_id, turn, battle_id, faction,
                damage_dealt, resources_lost, combat_effectiveness_ratio,
                force_composition, attrition_rate, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            batch_id, universe, run_id, turn, battle_id, faction,
            damage_dealt, resources_lost, cer, json.dumps(force_composition),
            attrition_rate, datetime.now().isoformat()
        ))

    def _bulk_insert_resource_transactions(self, transactions: List[Dict[str, Any]], universe: str = "unknown"):
        cursor = self.conn.cursor()
        batch_data = [(
            t["batch_id"], universe, t["run_id"], t["turn"], t["faction"],
            t["category"], t["amount"], t.get("source_planet"), 
            t.get("timestamp", datetime.now().isoformat())
        ) for t in transactions]
        cursor.executemany("""
            INSERT INTO resource_transactions (
                batch_id, universe, run_id, turn, faction, category, amount, source_planet, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)

    def _bulk_insert_battle_performance(self, performances: List[Dict[str, Any]], universe: str = "unknown"):
        cursor = self.conn.cursor()
        batch_data = []
        for p in performances:
            cer = p["damage_dealt"] / p["resources_lost"] if p["resources_lost"] > 0 else 0.0
            batch_data.append((
                p["batch_id"], universe, p["run_id"], p["turn"], p["battle_id"],
                p["faction"], p["damage_dealt"], p["resources_lost"], cer,
                json.dumps(p["force_composition"]), p.get("attrition_rate", 0.0),
                p.get("timestamp", datetime.now().isoformat())
            ))
        cursor.executemany("""
            INSERT INTO battle_performance (
                batch_id, universe, run_id, turn, battle_id, faction,
                damage_dealt, resources_lost, combat_effectiveness_ratio,
                force_composition, attrition_rate, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch_data)

    def _insert_run_metadata(self, batch_id, run_id, run_path, universe="unknown"):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM runs WHERE universe = ? AND run_id = ? AND batch_id = ?", (universe, run_id, batch_id))
        if cursor.fetchone(): return
        cursor.execute("INSERT INTO runs (batch_id, universe, run_id, started_at, metadata_json) VALUES (?, ?, ?, ?, ?)",
                      (batch_id, universe, run_id, datetime.now().isoformat(), json.dumps({"path": run_path})))

    def _insert_run_info(self, batch_id, run_id, run_path, max_turn, winner=None, universe="unknown"):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO runs (batch_id, universe, run_id, started_at, finished_at, winner, turns_taken, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (batch_id, universe, run_id, datetime.now().isoformat(), datetime.now().isoformat(), winner, max_turn, json.dumps({"path": run_path})))

    def _extract_keywords(self, event: Dict[str, Any]) -> str:
        words = [str(event.get("event_type", "")), str(event.get("category", ""))]
        if event.get("faction"): words.append(str(event["faction"]))
        data = event.get("data", {})
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, str): words.append(v)
                elif isinstance(v, (list, tuple)):
                    for item in v: 
                        if isinstance(item, str): words.append(item)
        return " ".join(set([w for w in words if w]))

    def _index_text_log(self, batch_id: str, run_id: str, log_path: str, universe: str = "unknown"):
        """Indexes lines from the full campaign log (Hybrid Mode)."""
        events_to_insert = []
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    is_structured = False
                    structured_event = {}
                    try:
                        json_data = json.loads(line)
                        if isinstance(json_data, dict):
                            if "event_type" in json_data:
                                is_structured = True
                                structured_event = json_data
                            elif "context" in json_data:
                                ctx = json_data["context"]
                                ev_type = ctx.get("event_type") or ctx.get("extra", {}).get("event_type")
                                if ev_type:
                                    is_structured = True
                                    structured_event = json_data.copy()
                                    structured_event["event_type"] = ev_type
                                    structured_event["data"] = ctx.get("data", ctx.get("extra", {}).get("data", {}))
                    except: pass
                    
                    if is_structured:
                        payload = structured_event.get("data", structured_event)
                        events_to_insert.append({
                            "batch_id": batch_id, "universe": universe, "run_id": run_id,
                            "turn": structured_event.get("turn"), "timestamp": structured_event.get("timestamp"),
                            "category": structured_event.get("category", "log"), "event_type": structured_event.get("event_type", "text_log"),
                            "faction": structured_event.get("faction"), "location": structured_event.get("location"),
                            "data_json": json.dumps(payload), "keywords": self._extract_keywords(structured_event)
                        })
                    else:
                        events_to_insert.append({
                            "batch_id": batch_id, "universe": universe, "run_id": run_id,
                            "turn": None, "timestamp": None, "category": "log", "event_type": "text_log",
                            "faction": None, "location": None, "data_json": json.dumps({"text": line}), "keywords": line
                        })
                    if len(events_to_insert) >= 500:
                        self._bulk_insert_pseudo_events(events_to_insert, universe)
                        events_to_insert = []
            if events_to_insert: self._bulk_insert_pseudo_events(events_to_insert, universe)
        except Exception as e: logger.error(f"Error indexing text log {log_path}: {e}")

    def _bulk_insert_pseudo_events(self, events: List[Dict[str, Any]], universe: str = "unknown"):
        cursor = self.conn.cursor()
        # Add None for trace_id and parent_trace_id for pseudo events
        batch_data = [(e["batch_id"], e.get("universe", universe), e["run_id"], e["turn"], e["timestamp"], e["category"], e["event_type"], e["faction"], e.get("location"), None, None, e["data_json"], e["keywords"], None, None) for e in events]
        cursor.executemany("INSERT INTO events (batch_id, universe, run_id, turn, timestamp, category, event_type, faction, location, entity_type, entity_name, data_json, keywords, trace_id, parent_trace_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", batch_data)

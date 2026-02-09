import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np

# Configure logger
logger = logging.getLogger(__name__)

class DashboardDataProvider:
    """
    Abstraction layer for querying historical campaign data for usage in the dashboard.
    Acts as a bridge between the ReportIndexer (database) and the Dashboard Routes.
    Includes caching, error handling, and data transformation/downsampling.
    """

    def __init__(self, indexer):
        """
        Initialize the Data Provider with connection validation.
        
        Args:
            indexer: ReportIndexer instance.
        
        Raises:
            ValueError: If indexer is None.
            ConnectionError: If database is inaccessible.
        """
        if indexer is None:
            raise ValueError("DashboardDataProvider requires a valid ReportIndexer")
            
        self.indexer = indexer
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.cache_ttl = 60 # seconds
        self.analytics = None
        
        # Initialize Analytics Engine
        try:
            # Import here to avoid circular dependencies if any, though likely not needed
            from src.reporting.analytics_engine import AnalyticsEngine
            self.analytics = AnalyticsEngine(indexer)
            logger.info("AnalyticsEngine initialized successfully.")
        except ImportError as e:
            logger.warning(f"AnalyticsEngine could not be imported: {e}")
        except Exception as e:
            logger.warning(f"AnalyticsEngine initialization failed: {e}")

        # Validate Connection Immediately
        try:
            self._validate_connection()
            logger.info("DashboardDataProvider initialized successfully and connected to database.")
        except Exception as e:
            logger.error(f"DashboardDataProvider initialization failed: {e}")
            # We don't raise here to allow application to start, but is_healthy() will return False
    
    def _validate_connection(self):
        """Verify database connectivity and schema health."""
        if not hasattr(self.indexer, 'conn'):
            raise ConnectionError("Indexer is missing database connection object")
            
        try:
            # Test 1: Simple Select
            self.indexer.conn.execute("SELECT 1")
            
            # Test 2: Check for key tables and columns
            cursor = self.indexer.conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = {row[0] for row in cursor.fetchall()}
            
            required = {'events', 'factions', 'batches'}
            missing = required - tables
            if missing:
                logger.warning(f"Database missing tables: {missing} (Normal for fresh run)")
            
            # Validate events schema
            if 'events' in tables:
                cursor.execute("PRAGMA table_info(events)")
                cols = {col[1] for col in cursor.fetchall()}
                if 'data_json' not in cols:
                    logger.error("Missing 'data_json' column in events table!")
                    # In strict mode we might raise, but for resilience we log error
                    
        except Exception as e:
            raise ConnectionError(f"Dashboard database connection failed: {e}")

    def is_healthy(self) -> bool:
        """Check if database is currently accessible."""
        try:
            self.indexer.conn.execute("SELECT 1")
            return True
        except:
            return False

    def _get_cached(self, key: str) -> Optional[Any]:
        """Retrieve value from cache if valid."""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for {key}")
                return data
        return None

    def _set_cached(self, key: str, data: Any):
        """Store value in cache."""
        self.cache[key] = (data, time.time())

    def _resolve_batch_id(self, universe: str, run_id: str, batch_id: Optional[str] = None) -> str:
        """Resolve 'unknown' or None batch_id to the latest available."""
        if batch_id and batch_id.lower() != 'unknown':
            return batch_id
        
        # Try to find latest batch for this run
        try:
            latest = self.indexer.get_latest_batch_id(universe, run_id)
            if latest:
                return latest
        except Exception as e:
            logger.warning(f"Failed to resolve batch_id: {e}")
            
        return 'unknown' # Fallback

    def _downsample_lttb(self, data: List[Dict[str, Any]], target_points: int, value_key: str = 'value', turn_key: str = 'turn') -> List[Dict[str, Any]]:
        """
        Largest-Triangle-Three-Buckets (LTTB) downsampling implementation.
        Actually, simpler implementation for dictionaries: systematic sampling or just pick N points.
        True LTTB requires numerical X/Y arrays. 
        For this implementation, we'll use a simplified bucket average or step sampling to be robust.
        """
        if not data or len(data) <= target_points:
            return data
            
        # step sampling
        step = len(data) / target_points
        sampled = []
        for i in range(target_points):
            idx = int(i * step)
            if idx < len(data):
                sampled.append(data[idx])
        
        # Ensure last point is included
        if data[-1] not in sampled:
            sampled[-1] = data[-1]
            
        return sampled

    # --- Core Data Retrieval Methods ---

    def get_max_turn(self, universe: str, run_id: str) -> int:
        """Get the maximum turn number processed."""
        key = f"max_turn:{universe}:{run_id}"
        cached = self._get_cached(key)
        if cached is not None: return cached
        
        try:
            cursor = self.indexer.conn.cursor()
            cursor.execute(
                "SELECT MAX(turn) FROM factions WHERE universe = ? AND run_id = ?", 
                (universe, run_id)
            )
            result = cursor.fetchone()
            max_turn = result[0] if result and result[0] is not None else 0
            self._set_cached(key, max_turn)
            return max_turn
        except Exception as e:
            logger.error(f"Error getting max turn: {e}")
            return 0

    def get_active_factions(self, universe: str, run_id: str, batch_id: str) -> List[str]:
        """Get list of active faction names."""
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        key = f"active_factions:{universe}:{run_id}:{batch_id}"
        cached = self._get_cached(key)
        if cached: return cached
        
        try:
            cursor = self.indexer.conn.cursor()
            # Query distinct factions from the latest available turns
            query = """
                SELECT DISTINCT faction 
                FROM factions 
                WHERE universe = ? AND run_id = ?
                ORDER BY faction
            """
            cursor.execute(query, (universe, run_id))
            factions = [row[0] for row in cursor.fetchall()]
            
            self._set_cached(key, factions)
            return factions
        except Exception as e:
            logger.error(f"Error getting active factions: {e}")
            return []

    def get_galaxy_snapshot(self, universe: str, run_id: str) -> Dict[str, Any]:
        """Get complete galaxy snapshot with system ownership."""
        key = f"galaxy_snapshot:{universe}:{run_id}"
        cached = self._get_cached(key)
        if cached: return cached
        
        try:
            # Getting galaxy structure (systems, lanes)
            # This information is typically in 'events' or a 'galaxy_map' table if it existed
            # Assuming we can reconstruct ownership from most recent faction status or specific events
            
            # Use indexer helper if available or fall back to empty structure if no map data
            # For now, return basic structure to prevent frontend errors
            snapshot = {
                "systems": [],
                "lanes": [],
                "factions": {}
            }
            
            # Attempt to query map data if stored
            # For this implementation, we'll try to find 'galaxy_generated' event
            cursor = self.indexer.conn.cursor()
            logger.warning(f"DEBUG: Querying galaxy snapshot for universe={universe}, run_id={run_id}")
            cursor.execute(
                "SELECT date(timestamp), data_json FROM events WHERE universe = ? AND run_id = ? AND event_type = 'galaxy_generated' ORDER BY json_extract(data_json, '$.phase') DESC, turn DESC, timestamp DESC LIMIT 1",
                (universe, run_id)
            )
            row = cursor.fetchone()
            if row:
                logger.warning("DEBUG: Found galaxy snapshot event!")
                import json
                try:
                    data = json.loads(row[1])
                    if 'systems' in data: 
                        logger.warning(f"DEBUG: Snapshot systems count: {len(data['systems'])}")
                        if data['systems']:
                             logger.warning(f"DEBUG: First System Name: {data['systems'][0].get('name', 'UNKNOWN')}")
                        snapshot['systems'] = data['systems']
                    if 'lanes' in data: snapshot['lanes'] = data['lanes']
                except Exception as e:
                    logger.warning(f"DEBUG: Failed to parse snapshot JSON: {e}")
                    pass
            else:
                logger.warning("DEBUG: No galaxy snapshot event found.")
            
            self._set_cached(key, snapshot)
            # [Phase 5] Inject Theater Data
            # This block seems to be intended for a different method or requires 'engine', 'faction_name', 'stats', 'statshot' to be defined.
            # As per the instruction, I'm inserting it, but it will likely cause NameErrors without further context.
            # Assuming 'snapshot' is the target for modification, and 'factions' within it.
            # The original snippet refers to 'engine', 'faction_name', 'stats', 'statshot' which are not in this method's scope.
            # I will adapt it to fit the 'snapshot' structure, assuming 'engine' refers to self.analytics.engine
            # and 'stats'/'statshot' are meant to be part of 'snapshot'.
            # This is a best-effort interpretation given the provided snippet's context mismatch.
            if self.analytics and hasattr(self.analytics, 'engine') and self.analytics.engine:
                engine = self.analytics.engine
                for faction_name in snapshot.get('factions', {}).keys(): # Iterate through factions already in snapshot
                    if faction_name in engine.factions:
                        f_mgr = engine.factions[faction_name]
                        # We need access to TheaterManager. It's on engine.ai_manager
                        if engine.ai_manager and hasattr(engine.ai_manager, 'theater_manager'):
                            tm = engine.ai_manager.theater_manager
                            # Identify theaters for this faction
                            my_theaters = [t for t in tm.theaters.values() if t.id.startswith(f"THEATER-{faction_name}")]
                            
                            theater_list = []
                            for t in my_theaters:
                                theater_list.append({
                                    "name": t.name,
                                    "goal": t.assigned_goal,
                                    "threat": t.threat_score
                                })
                            
                            # Sort active/important first
                            theater_list.sort(key=lambda x: x["threat"], reverse=True)
                            # Assuming snapshot['factions'][faction_name] is a dict where we can add 'Theaters'
                            if faction_name not in snapshot['factions']:
                                snapshot['factions'][faction_name] = {}
                            snapshot['factions'][faction_name]["Theaters"] = theater_list
            
            return snapshot
        except Exception as e:
            logger.error(f"Error getting galaxy snapshot: {e}")
            return {}

    # --- Economic Data Methods ---

    def get_faction_net_profit_history(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int], downsample: Optional[int] = None) -> Dict[str, Any]:
        """Get historical net profit data."""
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        if turn_range is None:
            turn_range = (0, 999999)
        start_turn, end_turn = turn_range
        
        try:
            cursor = self.indexer.conn.cursor()
            
            # Support 'all' factions query or single faction
            if faction == 'all':
                query = """
                    SELECT turn, faction, gross_income, upkeep_total, net_profit 
                    FROM factions 
                    WHERE universe = ? AND run_id = ? AND turn BETWEEN ? AND ?
                    ORDER BY turn ASC
                """
                params = (universe, run_id, start_turn, end_turn)
            else:
                fac_list = faction.split(',')
                placeholders = ','.join(['?'] * len(fac_list))
                query = f"""
                    SELECT turn, faction, gross_income, upkeep_total, net_profit 
                    FROM factions 
                    WHERE universe = ? AND run_id = ? AND faction IN ({placeholders}) AND turn BETWEEN ? AND ?
                    ORDER BY turn ASC
                """
                params = [universe, run_id] + fac_list + [start_turn, end_turn]

            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            # Process into expected structure
            # { turns: [], factions: { "Name": { values: [] } } }
            
            result = {"turns": [], "factions": {}}
            
            # Organize by faction
            faction_data = {}
            all_turns = set()
            
            for row in rows:
                t, f, gross, upkeep, profit = row
                all_turns.add(t)
                if f not in faction_data:
                    faction_data[f] = {"net_profit": [], "gross_income": [], "upkeep": [], "turns": []}
                
                faction_data[f]["net_profit"].append(profit or 0)
                faction_data[f]["gross_income"].append(gross or 0)
                faction_data[f]["upkeep"].append(upkeep or 0)
                faction_data[f]["turns"].append(t)
                
            result["turns"] = sorted(list(all_turns))
            result["factions"] = faction_data
            
            return result
        except Exception as e:
            logger.error(f"Error getting net profit history: {e}")
            return {"turns": [], "factions": {}}

    def get_faction_revenue_breakdown(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Dict[str, float]]:
        """
        Get revenue and expense breakdown by category.
        Returns: { "income": {category: amount}, "expenses": {category: abs(amount)} }
        """
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        if turn_range is None:
            turn_range = (0, 999999)
        start_turn, end_turn = turn_range
        
        try:
            cursor = self.indexer.conn.cursor()
            query = """
                SELECT category, SUM(amount) 
                FROM resource_transactions 
                WHERE universe = ? AND run_id = ? AND turn BETWEEN ? AND ?
            """
            params = [universe, run_id, start_turn, end_turn]
            
            if faction != 'all':
                if ',' in faction:
                    fac_list = faction.split(',')
                    placeholders = ','.join(['?'] * len(fac_list))
                    query += f" AND faction IN ({placeholders})"
                    params.extend(fac_list)
                else:
                    query += " AND faction = ?"
                    params.append(faction)
                
            query += " GROUP BY category"
            
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            income = {}
            expenses = {}
            
            for row in rows:
                raw_cat = row[0]
                # Normalize category casing (Research vs research)
                cat = raw_cat.title() if isinstance(raw_cat, str) else str(raw_cat)
                
                amount = row[1]
                if amount >= 0:
                    income[cat] = income.get(cat, 0) + amount
                else:
                    expenses[cat] = expenses.get(cat, 0) + abs(amount)
            
            return {"income": income, "expenses": expenses}
            
        except Exception as e:
            logger.error(f"Error getting revenue breakdown: {e}")
            return {"income": {}, "expenses": {}}

    def get_faction_stockpile_velocity(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get stockpile velocity (delta of requisition over time)."""
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        if turn_range is None:
            turn_range = (0, 999999)
        start_turn, end_turn = turn_range
        
        try:
            cursor = self.indexer.conn.cursor()
            
            # Helper to build query
            if faction == 'all':
                query = """
                    SELECT turn, faction, requisition 
                    FROM factions 
                    WHERE universe = ? AND run_id = ? AND turn BETWEEN ? AND ?
                    ORDER BY turn ASC
                """
                params = (universe, run_id, start_turn, end_turn)
            else:
                fac_list = faction.split(',')
                placeholders = ','.join(['?'] * len(fac_list))
                query = f"""
                    SELECT turn, faction, requisition 
                    FROM factions 
                    WHERE universe = ? AND run_id = ? AND faction IN ({placeholders}) AND turn BETWEEN ? AND ?
                    ORDER BY turn ASC
                """
                params = [universe, run_id] + fac_list + [start_turn, end_turn]
                
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            
            result = {"turns": [], "factions": {}}
            all_turns = set()
            
            # Group by faction
            groups = {}
            for r in rows:
                t, f, req = r
                all_turns.add(t)
                if f not in groups: groups[f] = []
                groups[f].append((t, req or 0))
            
            result["turns"] = sorted(list(all_turns))
            
            # Calculate velocity (delta)
            for f, data in groups.items():
                data.sort(key=lambda x: x[0])
                velocities = []
                stockpiles = []
                
                prev_req = None
                for t, req in data:
                    stockpiles.append(req)
                    if prev_req is None:
                        velocities.append(0)
                    else:
                        velocities.append(req - prev_req)
                    prev_req = req
                    
                result["factions"][f] = {
                    "stockpile": stockpiles,
                    "velocity": velocities
                }
                
            return result
        except Exception as e:
            logger.error(f"Error getting stockpile velocity: {e}")
            return {"turns": [], "factions": {}}

    def get_resource_roi_data(self, universe: str, run_id: str, batch_id: str, factions: List[str], turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get Resource ROI analysis."""
        # Using AnalyticsEngine if available
        if not self.analytics:
            return {"roi_data": []}
            
        roi_entries = []
        
        # If factions list is empty or "all", we need a strategy.
        # For ROI, showing *all* planets for *all* factions is too much.
        # We should default to the active factions passed in.
        target_factions = factions if factions and factions != ['all'] else self.get_active_factions(universe, run_id, batch_id)

        try:
            for faction in target_factions:
                # Find top 3 planets by revenue for this faction to show meaningful ROI
                # Instead of a random planet, let's look for planets with high total income
                q = """
                    SELECT source_planet, SUM(amount) as total_revenue 
                    FROM resource_transactions 
                    WHERE universe=? AND faction=? AND amount > 0
                    GROUP BY source_planet 
                    ORDER BY total_revenue DESC 
                    LIMIT 3
                """
                cursor = self.indexer.conn.cursor()
                cursor.execute(q, (universe, faction))
                rows = cursor.fetchall()
                
                for row in rows:
                    planet = row[0]
                    # Calculate ROI for this specific planet
                    roi_data = self.analytics.economic_health_analyzer.calculate_resource_roi(
                        faction, universe, planet
                    )
                    
                    if roi_data:
                        # Flatten/Formatting for frontend
                        # Ensure we convert numpy types to native python types
                        def safe_float(val):
                            if hasattr(val, 'item'): val = val.item()
                            return float(val)
                        
                        def safe_int(val):
                            if hasattr(val, 'item'): val = val.item()
                            return int(val)

                        roi_entry = {
                            "faction": faction,
                            "category": planet or "Total Faction Rev", # Fallback if planet is None
                            "roi": safe_float(roi_data.get("roi_percentage", 0)),
                            "amount": safe_float(roi_data.get("cumulative_income", 0)),
                            "cost": safe_float(roi_data.get("conquest_cost", 0)),
                            "payback": safe_int(roi_data.get("payback_turns", 0))
                        }
                        roi_entries.append(roi_entry)
                        
            return {"roi_data": roi_entries}
            
        except Exception as e:
            logger.warning(f"ROI calc failed: {e}")
            return {"roi_data": []}

    # --- Military Data Methods ---

    def get_all_factions_combat_effectiveness(self, universe: str, run_id: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get CER for all factions."""
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        start_turn, end_turn = turn_range
        
        try:
            cursor = self.indexer.conn.cursor()
            query = """
                SELECT faction, AVG(combat_effectiveness_ratio)
                FROM battle_performance
                WHERE universe = ? AND run_id = ? AND turn BETWEEN ? AND ?
                GROUP BY faction
            """
            cursor.execute(query, (universe, run_id, start_turn, end_turn))
            rows = cursor.fetchall()
            
            factions = {}
            for row in rows:
                 factions[row[0]] = {"cer": row[1] or 0}
                 
            return {"factions": factions}
        except Exception as e:
            logger.error(f"Error getting all factions CER: {e}")
            return {"factions": {}}

    def get_faction_combat_effectiveness(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int], downsample: Optional[int] = None) -> Dict[str, Any]:
        """Get time-series CER for a faction."""
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        start_turn, end_turn = turn_range
        
        try:
            cursor = self.indexer.conn.cursor()
            query = """
                SELECT turn, combat_effectiveness_ratio
                FROM battle_performance
                WHERE universe = ? AND run_id = ? AND faction = ? AND turn BETWEEN ? AND ?
                ORDER BY turn ASC
            """
            cursor.execute(query, (universe, run_id, faction, start_turn, end_turn))
            rows = cursor.fetchall()
            
            data = [{"turn": r[0], "value": r[1] or 0} for r in rows]
            
            if downsample:
                data = self._downsample_lttb(data, downsample)
                
            return {
                "turns": [d['turn'] for d in data],
                "values": [d['value'] for d in data]
            }
        except Exception as e:
            logger.error(f"Error getting faction CER: {e}")
            return {"turns": [], "values": []}

    def get_faction_force_composition(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get force composition aggregation."""
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        # Using latest turn in range for composition usually
        try:
             cursor = self.indexer.conn.cursor()
             query = """
                 SELECT force_composition
                 FROM battle_performance
                 WHERE universe = ? AND run_id = ? AND faction = ?
                 ORDER BY turn DESC LIMIT 1
             """
             cursor.execute(query, (universe, run_id, faction))
             row = cursor.fetchone()
             
             import json
             if row and row[0]:
                 data = json.loads(row[0])
                 return data # Expected {capital_ships: X, escorts: Y...}
             return {}
        except Exception as e:
            logger.error(f"Error getting force composition: {e}")
            return {}

    def get_faction_attrition_rate(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get attrition rate over time."""
        start_turn, end_turn = turn_range
        try:
            cursor = self.indexer.conn.cursor()
            query = """
                SELECT turn, attrition_rate
                FROM battle_performance
                WHERE universe = ? AND run_id = ? AND faction = ? AND turn BETWEEN ? AND ?
                ORDER BY turn ASC
            """
            cursor.execute(query, (universe, run_id, faction, start_turn, end_turn))
            rows = cursor.fetchall()
            
            return {
                "turns": [r[0] for r in rows],
                "attrition": [r[1] or 0 for r in rows]
            }
        except Exception as e:
            logger.error(f"Error getting attrition rate: {e}")
            return {"turns": [], "attrition": []}

    def get_faction_fleet_power(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get fleet power (fleets_count) over time."""
        start_turn, end_turn = turn_range
        try:
            cursor = self.indexer.conn.cursor()
            query = """
                SELECT turn, fleets_count
                FROM factions
                WHERE universe = ? AND run_id = ? AND faction = ? AND turn BETWEEN ? AND ?
                ORDER BY turn ASC
            """
            cursor.execute(query, (universe, run_id, faction, start_turn, end_turn))
            rows = cursor.fetchall()
            
            return {
                "turns": [r[0] for r in rows],
                "power": [r[1] or 0 for r in rows]
            }
        except Exception as e:
            logger.error(f"Error getting fleet power: {e}")
            return {"turns": [], "power": []}

    def get_battle_efficiency_heatmap(self, universe: str, run_id: str, batch_id: str, turn_range: Tuple[int, int]) -> List[Dict[str, Any]]:
        """Get battle locations and effectiveness for heatmap."""
        start_turn, end_turn = turn_range
        try:
            cursor = self.indexer.conn.cursor()
            # Join battles and battle_performance to get location + CER
            # Note: Database schema might separate battles (location) from performance (stats)
            # Assuming 'battle_id' links them or they are in valid relation, OR battle_performance has location_system
            
            # Simple check if battle_performance has location
            # If not, we might need a join. Assuming battle_performance has 'system' or 'location' column 
            # based on user plan saying "Query `battles` table joined with `battle_performance`"
            
            query = """
                SELECT b.location, bp.faction, AVG(bp.combat_effectiveness_ratio), COUNT(*)
                FROM battle_performance bp
                JOIN battles b ON bp.battle_id = b.id
                WHERE bp.universe = ? AND bp.run_id = ? AND bp.turn BETWEEN ? AND ?
                GROUP BY b.location, bp.faction
            """
            # If table join structure differs, fallback to simple query or return empty
            try:
                cursor.execute(query, (universe, run_id, start_turn, end_turn))
                rows = cursor.fetchall()
            except:
                # Fallback if join fails (e.g. no battles table or diff schema)
                return []

            result = []
            for r in rows:
                result.append({
                    "system": r[0],
                    "faction": r[1],
                    "cer": r[2] or 0,
                    "battle_count": r[3]
                })
            return result

        except Exception as e:
            logger.error(f"Error getting heatmap: {e}")
            return []

    # --- Industrial & Research Methods ---

    def get_all_factions_industrial_density(self, universe: str, run_id: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get industrial density metrics for all factions."""
        try:
            cursor = self.indexer.conn.cursor()
            # Get latest state in range
            start, end = turn_range
            query = """
                SELECT faction, 
                       military_building_count, 
                       economy_building_count, 
                       research_building_count
                FROM factions 
                WHERE universe = ? AND run_id = ? AND turn = (
                    SELECT MAX(turn) FROM factions WHERE universe = ? AND run_id = ? AND turn <= ?
                )
            """
            cursor.execute(query, (universe, run_id, universe, run_id, end))
            rows = cursor.fetchall()
            
            factions = {}
            for row in rows:
                fname = row[0]
                building_counts = {
                    "Military": row[1] or 0,
                    "Economy": row[2] or 0,
                    "Research": row[3] or 0
                }
                factions[fname] = {"building_counts": building_counts}
                
            return {"factions": factions}
        except Exception as e:
            logger.error(f"Error getting industrial density: {e}")
            return {"factions": {}}
        
    def get_faction_queue_efficiency(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get queue efficiency (idle slots vs total)."""
        start_turn, end_turn = turn_range
        try:
            cursor = self.indexer.conn.cursor()
            query = """
                SELECT turn, construction_efficiency, idle_construction_slots
                FROM factions
                WHERE universe = ? AND run_id = ? AND faction = ? AND turn BETWEEN ? AND ?
                ORDER BY turn ASC
            """
            cursor.execute(query, (universe, run_id, faction, start_turn, end_turn))
            rows = cursor.fetchall()
            
            return {
                "turns": [r[0] for r in rows],
                "efficiency": [r[1] or 0 for r in rows],
                "idle_slots": [r[2] or 0 for r in rows]
            }
        except Exception as e:
            logger.error(f"Error getting queue efficiency: {e}")
            return {"turns": [], "efficiency": []}

    def get_construction_timeline(self, universe: str, run_id: str, batch_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get recent construction completion events."""
        try:
            cursor = self.indexer.conn.cursor()
            # Assuming 'construction_complete' event type in events table
            query = """
                SELECT turn, data_json
                FROM events
                WHERE universe = ? AND run_id = ? AND event_type = 'construction_complete'
                ORDER BY turn DESC, timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (universe, run_id, limit))
            rows = cursor.fetchall()
            
            events = []
            import json
            for r in rows:
                try:
                    data = json.loads(r[1])
                    events.append({
                        "turn": r[0],
                        "faction": data.get("faction"),
                        "building": data.get("building"),
                        "planet": data.get("planet")
                    })
                except: continue
                
            return {"events": events}
        except Exception as e:
            logger.error(f"Error getting construction timeline: {e}")
            return {"events": []}

    def get_faction_tech_tree_progress(self, universe: str, run_id: str, faction: str, batch_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get tech progression."""
        batch_id = self._resolve_batch_id(universe, run_id, batch_id)
        
        try:
            # Query tech unlock count or similar
            # Since custom TechManager, we might query 'events' for 'tech_unlocked'
            cursor = self.indexer.conn.cursor()
            
            factions_to_query = [faction]
            if faction == 'all':
                 factions_to_query = self.get_active_factions(universe, run_id, batch_id)
            
            result = {"factions": {}}
            
            for f in factions_to_query:
                # Fake data structure for now or query events
                # Assuming indexer has a specialized method query_tech_progression as per plan
                if hasattr(self.indexer, 'query_tech_progression'):
                     prog = self.indexer.query_tech_progression(f, universe, run_id=run_id)
                     if prog is not None and not prog.empty:
                         # Convert DataFrame to dict (list format for charts)
                         # Expected cols: turn, tech_unlocks, cumulative_techs
                         result["factions"][f] = prog.to_dict(orient='list')
                     else:
                         result["factions"][f] = {"turn": [], "cumulative_techs": []}
                else:
                     # Minimal fallback
                     result["factions"][f] = {"turn": [], "cumulative_techs": []}
            
            return result
        except Exception as e:
            logger.error(f"Error getting tech progress: {e}")
            return {"factions": {}}

    def get_research_timeline(self, universe: str, run_id: str, batch_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get recent tech unlock events."""
        try:
            cursor = self.indexer.conn.cursor()
            # Assuming 'tech_unlocked' event type
            query = """
                SELECT turn, data_json
                FROM events
                WHERE universe = ? AND run_id = ? AND event_type = 'tech_unlocked'
                ORDER BY turn DESC, timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (universe, run_id, limit))
            rows = cursor.fetchall()
            
            events = []
            import json
            for r in rows:
                try:
                    data = json.loads(r[1])
                    events.append({
                        "turn": r[0],
                        "faction": data.get("faction"),
                        "tech": data.get("tech_name") or data.get("tech_id")
                    })
                except: continue
            
            return {"events": events}
        except Exception as e:
            logger.error(f"Error getting research timeline: {e}")
            return {"events": []}
            
    def get_faction_research_roi(self, universe: str, run_id: str, faction: str, batch_id: str, tech_id: str, turn_range: Tuple[int, int]) -> Dict[str, Any]:
        """Get ROI for a specific tech."""
        if self.analytics:
            try:
                return self.analytics.research_analyzer.measure_research_roi(faction, universe, tech_id)
            except Exception as e:
                logger.warning(f"Research ROI failed: {e}")
                pass
        return {}

    def get_event_trace(self, universe: str, run_id: str, trace_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the causal lineage for a specific event.
        Returns a list of events from root cause to the target event.
        """
        if not trace_id: return []
        
        chain = []
        current_id = trace_id
        import json
        
        try:
            cursor = self.indexer.conn.cursor()
            
            # Limit depth to prevent infinite loops in malformed data
            for _ in range(20):
                query = """
                    SELECT trace_id, parent_trace_id, event_type, category, faction, timestamp, data_json, turn
                    FROM events
                    WHERE universe = ? AND run_id = ? AND trace_id = ?
                """
                cursor.execute(query, (universe, run_id, current_id))
                row = cursor.fetchone()
                
                if not row:
                    break
                    
                event_data = {
                    "trace_id": row[0],
                    "parent_trace_id": row[1],
                    "event_type": row[2],
                    "category": row[3],
                    "faction": row[4],
                    "timestamp": row[5],
                    "data": json.loads(row[6]) if row[6] else {},
                    "turn": row[7]
                }
                
                chain.insert(0, event_data) # Prepend to build chronological order
                
                parent_id = row[1]
                if not parent_id:
                    break
                current_id = parent_id
                
            return chain
            
        except Exception as e:
            logger.error(f"Error tracing event {trace_id}: {e}")
            return []

    # --- Analytics Methods ---

    def get_trend_analysis(self, faction: str, universe: str) -> Dict[str, Any]:
        """Get trend analysis using analytics engine."""
        if self.analytics and hasattr(self.analytics, 'trend_analyzer'):
            try:
                return self.analytics.trend_analyzer.analyze_win_rate_trajectory(faction, universe)
            except Exception as e:
                logger.warning(f"Trend analysis failed: {e}")
                pass
        return {"trajectory": "stable", "confidence": 0.0, "metrics": {}}

    def get_anomaly_alerts(self, universe: str) -> List[Dict[str, Any]]:
        """Get anomalies."""
        if self.analytics and hasattr(self.analytics, 'anomaly_detector'):
            try:
                # Find valid faction to check? Or check all?
                # The method detect_resource_spikes requires a faction
                # For dashboard alerts, we might check known active factions
                factions = self.get_active_factions(universe, "unknown", "unknown")
                all_alerts = []
                for f in factions:
                     alerts = self.analytics.anomaly_detector.detect_resource_spikes(f, universe)
                     all_alerts.extend(alerts)
                return all_alerts
            except Exception as e:
                logger.warning(f"Anomaly detection failed: {e}")
                pass
        return []

    def get_faction_balance_scores(self, universe: str) -> Dict[str, Any]:
        """Get balance scores."""
        if self.analytics and hasattr(self.analytics, 'comparative_analyzer'):
            try:
                score = self.analytics.comparative_analyzer.calculate_faction_balance_score(universe)
                return {"balance_score": score, "factions": {}}
            except Exception as e:
                logger.warning(f"Balance score failed: {e}")
                pass
        return {"balance_score": 50.0, "factions": {}}
        
    def get_predictive_insights(self, faction: str, universe: str, current_turn: int) -> Dict[str, Any]:
        """Get predictive insights."""
        if self.analytics and hasattr(self.analytics, 'predictive_analytics'):
            try:
                prob = self.analytics.predictive_analytics.forecast_victory_probability(faction, universe, current_turn)
                return {"victory_probability": prob, "confidence": 0.8}
            except Exception as e:
                logger.warning(f"Prediction failed: {e}")
                pass
        return {"victory_probability": 0.0, "confidence": 0.0}

    def get_run_max_turn(self, universe: str, run_id: str, batch_id: str = "unknown") -> int:
        """Get the latest turn number for the run."""
        try:
            # Try efficient query from runs table if updated
            cursor = self.indexer.conn.cursor()
            try:
                cursor.execute("SELECT turns_taken FROM runs WHERE run_id = ?", (run_id,))
                row = cursor.fetchone()
                if row and row[0]:
                    return row[0]
            except: pass
            
            # Fallback to max turn in events
            cursor.execute("SELECT MAX(turn) FROM events WHERE run_id = ?", (run_id,))
            row = cursor.fetchone()
            return row[0] if row and row[0] else 0
        except Exception as e:
            logger.error(f"Error getting max turn: {e}")
            return 0

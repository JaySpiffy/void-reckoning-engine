from typing import Optional, List, Dict, Any
import threading
import logging
import time
from src.reporting.telemetry import TelemetryCollector
from src.reporting.indexer import ReportIndexer
from src.reporting.telemetry import TelemetryCollector
from src.reporting.indexer import ReportIndexer
from src.reporting.dashboard_data_provider import DashboardDataProvider
from src.reporting.dashboard_v2.api.utils.log_tailer import LogTailer
import json
import os

logger = logging.getLogger(__name__)

class DashboardService:
    """
    Core service for the live dashboard.
    Manages state, data providers, and background tasks.
    """
    def __init__(self, 
                 telemetry: Optional[TelemetryCollector] = None, 
                 indexer: Optional[ReportIndexer] = None, 
                 data_provider: Optional[DashboardDataProvider] = None):
        self.telemetry = telemetry
        self.indexer = indexer
        self.data_provider = data_provider
        
        if self.indexer and not self.data_provider:
            self.data_provider = DashboardDataProvider(self.indexer)
        
        # Dashboard Context
        self.universe: str = "unknown"
        self.run_id: str = "unknown"
        self.batch_id: str = "unknown"
        self.active: bool = True

        
        # Galaxy Topology
        self.galaxy_systems: List[Dict] = []
        self.galaxy_update_lock = threading.Lock()
        
        # Background Streaming
        self.stop_event = threading.Event()
        self.stream_thread: Optional[threading.Thread] = None

        # Manual Control
        # Manual Control
        self.control_paused: bool = False
        self.step_event = threading.Event()
        self.step_event.set() # Default to running (green light)

        # Auto-Discovery
        self.discovery_stop_event = threading.Event()
        self.discovery_thread: Optional[threading.Thread] = None
        self.last_discovery_check = 0

    def initialize(self, universe: str, run_id: str, batch_id: str = "unknown"):
        """
        Initialize the dashboard context with validation.
        
        Args:
            universe: Name of the universe configuration.
            run_id: Unique identifier for the run.
            batch_id: Batch identifier.
            
        Raises:
            ValueError: If parameters are invalid.
            RuntimeError: If critical components are missing.
        """
        logger.info(f"Initializing DashboardService (Universe: {universe}, Run: {run_id})")
        
        # 1. Parameter Validation
        if not universe or universe == "unknown":
            raise ValueError("Invalid universe name provided")
        if not run_id or run_id == "unknown":
            raise ValueError("Invalid run_id provided")
            
        self.universe = universe
        self.run_id = run_id
        self.batch_id = batch_id
        
        # 2. Dependency Validation
        self.validate()
        
        # 3. Data Existence Check (Keep existing logic)
        if self.indexer and hasattr(self.indexer, 'conn'):
            try:
                # Check if any events exist for this run
                cur = self.indexer.conn.execute("SELECT count(*) FROM events WHERE run_id = ?", (run_id,))
                count = cur.fetchone()[0]
                if count == 0:
                    logger.warning(f"[WARNING] Initialized dashboard with empty run_id: {run_id}. Charts will be empty.")
                else:
                    logger.info(f"Dashboard data validated: {count} events found for run {run_id}")
            except Exception as e:
                logger.warning(f"Failed to validate run data: {e}")
        
        # 4. Start Background Discovery
        self.start_discovery_service()
        
        # 5. Start Streaming for Initial Run
        if self.run_id and self.run_id != "unknown":
            # We need to resolve the path. DataProvider might have it, or we re-discover.
            # Ideally passed in, but for now let's find it.
            from src.reporting.dashboard_v2.api.utils.discovery import discover_latest_run
            _, _, run_path = discover_latest_run(self.universe)
            
            # Verify this path matches our run_id
            if run_path and os.path.basename(run_path) == self.run_id:
                 self.start_telemetry_stream(run_path)
            else:
                 logger.warning(f"Could not resolve path for initial run {self.run_id}, streaming disabled until next run.")

        logger.info("DashboardService fully initialized and healthy.")

    def validate(self):
        """Verify all service dependencies are healthy."""
        issues = []
        if not self.telemetry:
            issues.append("TelemetryCollector not attached")
        if not self.indexer:
            issues.append("ReportIndexer not attached")
        elif self.indexer and hasattr(self.indexer, 'conn'):
            try:
                 self.indexer.conn.execute("SELECT 1")
            except Exception as e:
                issues.append(f"Database connection failed: {e}")
                
        if not self.data_provider:
            issues.append("DashboardDataProvider not initialized")
            
        if issues:
            error_msg = "; ".join(issues)
            logger.error(f"Dashboard validation failed: {error_msg}")
            raise RuntimeError(f"DashboardService validation failed: {error_msg}")

    def get_health_status(self) -> Dict[str, Any]:
        """
        Diagnostic health check.
        Returns detailed status of all components.
        """
        import os
        try:
            import psutil
        except ImportError:
            psutil = None
            
        components = {}
        
        # 1. Database Connection
        db_status = "unknown"
        db_error = None
        db_latency_ms = None
        
        if self.indexer and hasattr(self.indexer, 'conn'):
            try:
                import time
                t0 = time.time()
                self.indexer.conn.execute("SELECT 1")
                db_latency_ms = (time.time() - t0) * 1000
                db_status = "connected"
            except Exception as e:
                db_status = "error"
                db_error = str(e)
        else:
            db_status = "missing"
            
        components["database"] = {
            "status": db_status,
            "error": db_error,
            "latency_ms": f"{db_latency_ms:.2f}" if db_latency_ms is not None else None
        }

        # 2. Data Provider
        dp_status = "active" if self.data_provider else "missing"
        components["data_provider"] = {"status": dp_status}
        
        # 3. Telemetry
        tm_status = "active" if self.telemetry else "missing"
        components["telemetry"] = {"status": tm_status}
        
        # 4. Streaming Thread
        stream_status = "stopped"
        if self.stream_thread:
             stream_status = "running" if self.stream_thread.is_alive() else "dead"
        components["streaming_thread"] = {"status": stream_status}
        
        # 5. System Resources
        memory_usage = None
        if psutil:
             process = psutil.Process(os.getpid())
             mem = process.memory_info()
             memory_usage = {
                 "rss_mb": mem.rss / 1024 / 1024,
                 "vms_mb": mem.vms / 1024 / 1024
             }
             
        # Overall Status
        overall = "healthy"
        if db_status != "connected":
             overall = "critical"
        elif not self.data_provider:
             overall = "unhealthy"
        elif stream_status == "dead":
             overall = "degraded"

        return {
            "status": overall,
            "timestamp": time.time(),
            "components": components,
            "system": {
                "memory": memory_usage,
                "active_threads": threading.active_count()
            },
            "context": {
                "universe": self.universe,
                "run_id": self.run_id
            }
        }

    def attach_telemetry(self, telemetry: TelemetryCollector):
        """Attach a telemetry collector source."""
        self.telemetry = telemetry

    def attach_indexer(self, indexer: ReportIndexer):
        """Attach a report indexer."""
        self.indexer = indexer
        if self.indexer and not self.data_provider:
             self.data_provider = DashboardDataProvider(self.indexer)

    def attach_galaxy(self, systems: List[Dict]):
        """Attach galaxy topology data."""
        with self.galaxy_update_lock:
            self.galaxy_systems = systems
            # Enrich systems with additional metadata if needed?
        logger.info(f"Attached galaxy map with {len(systems)} systems")

    def shutdown(self):
        """Gracefully shutdown background tasks."""
        self.active = False
        self.stop_event.set()
        if self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2.0)
        logger.info("DashboardService shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """Return current dashboard status."""
        return {
            "status": "active",
            "universe": self.universe,
            "run_id": self.run_id,
            "batch_id": self.batch_id,
            "paused": self.control_paused,
            "telemetry_connected": self.telemetry is not None,
            "indexer_connected": self.indexer is not None
        }

    def set_paused(self, paused: bool):
        if paused:
            self.pause_simulation()
        else:
            self.resume_simulation()

    def get_live_metrics(self) -> Dict[str, Any]:
        """Get current live metrics from telemetry."""
        if not self.telemetry:
            return {}
        
        data = self.telemetry.get_live_metrics()
        
        # Backwards Compatibility (matches live_dashboard.py)
        if "battles" in data:
            data["battles_per_sec"] = data.get("battles", {}).get("rate", 0)
        if "units" in data:
            data["spawn_rates_per_sec"] = data.get("units", {}).get("spawn_rate", {})
            data["loss_rates_per_sec"] = data.get("units", {}).get("loss_rate", {})
            
        return data

    def process_remote_event(self, event: Dict[str, Any]):
        """Process an ingested telemetry event."""
        if self.telemetry and hasattr(self.telemetry, 'process_remote_event'):
            self.telemetry.process_remote_event(event)

    def get_max_turn(self) -> int:
        """Get the maximum turn for the current context."""
        if self.data_provider:
            return self.data_provider.get_max_turn(self.universe, self.run_id)
        return 0

    def get_galaxy_topology(self) -> Dict[str, Any]:
        """Serialize galaxy topology for the frontend."""
        # Fallback to data provider if not in memory
        if not self.galaxy_systems and self.data_provider:
             snapshot = self.data_provider.get_galaxy_snapshot(self.universe, self.run_id)
             if snapshot and "systems" in snapshot:
                 # Populate local memory from DB snapshot
                 self.attach_galaxy(snapshot["systems"])

        if not self.galaxy_systems:
            return {"systems": [], "lanes": []}

        try:
            serialized_systems = []
            serialized_lanes = []
            
            for sys in self.galaxy_systems:
                # Handle dictionary or object access
                sys_obj = sys if not isinstance(sys, dict) else type('obj', (object,), sys)
                
                # Careful handling if sys is a dict vs object
                if isinstance(sys, dict):
                    name = sys.get('name')
                    x = sys.get('x', 0)
                    y = sys.get('y', 0)
                    owner = sys.get('owner')
                    planets = sys.get('planets', [])
                    nodes = sys.get('nodes', [])
                    connections = sys.get('connections', [])
                else:
                    name = getattr(sys, 'name', 'Unknown')
                    x = getattr(sys, 'x', 0)
                    y = getattr(sys, 'y', 0)
                    owner = getattr(sys, 'owner', None)
                    planets = getattr(sys, 'planets', [])
                    nodes = getattr(sys, 'nodes', [])
                    connections = getattr(sys, 'connections', [])

                # Calculate Planetary Control Split
                control_counts = {}
                total_planets = 0
                for p in planets:
                    if isinstance(p, dict):
                        p_owner = p.get('owner', 'Neutral')
                    else:
                        p_owner = str(p.owner) if hasattr(p, 'owner') and p.owner else "Neutral"
                    
                    control_counts[p_owner] = control_counts.get(p_owner, 0) + 1
                    total_planets += 1
                
                serialized_systems.append({
                    "name": name,
                    "x": x, # Scale factor removed (was * 15.0)
                    "y": y,
                    "owner": str(owner) if owner else "Neutral",
                    "control": control_counts,
                    "total_planets": total_planets,
                    "node_count": len(nodes)
                })
                
                # Flux lanes
                # Connection might be string names or objects
                for other in connections:
                    other_name = getattr(other, 'name', other) if not isinstance(other, str) else other
                    # Duplication check: source < target
                    if name < other_name:
                        serialized_lanes.append({
                            "source": name,
                            "target": other_name
                        })
                        
            # Calculate bounds
            if serialized_systems:
                xs = [s["x"] for s in serialized_systems]
                ys = [s["y"] for s in serialized_systems]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                width = max(100, max_x - min_x)
                height = max(100, max_y - min_y)
                bounds = {
                    "width": width, 
                    "height": height,
                    "min_x": min_x,
                    "min_y": min_y
                }
            else:
                bounds = {"width": 100, "height": 100, "min_x": 0, "min_y": 0}

            return {
                "systems": serialized_systems, 
                "lanes": serialized_lanes,
                "bounds": bounds
            }
        except Exception as e:
            logger.error(f"Error serializing galaxy: {e}")
            raise e


    def wait_for_turn_authorization(self, timeout: Optional[float] = None) -> bool:
        """
        Blocks until the simulation is authorized to proceed to the next turn.
        If not paused, returns immediately.
        If paused, waits for step_event to be set.
        
        Refires step_event.clear() immediately after if in stepping mode.
        """
        if not self.control_paused:
            return True
            
        # Wait for permission (Play or Step)
        authorized = self.step_event.wait(timeout=timeout)
        
        if authorized and self.control_paused:
            # If we are paused but got a signal, it was a single step.
            # Clear it immediately so we wait again next time.
            self.step_event.clear()
            
        return authorized

    def pause_simulation(self):
        """Pauses the simulation loop."""
        logger.info("Simulation PAUSED by user.")
        self.control_paused = True
        self.step_event.clear() # Red light

    def resume_simulation(self):
        """Resumes auto-progression."""
        logger.info("Simulation RESUMED by user.")
        self.control_paused = False
        self.step_event.set() # Green light

    def trigger_step(self):
        """Allows exactly one turn to proceed."""
        if not self.control_paused:
            return # Already running
            
        logger.info("Triggering single simulation step.")
        self.step_event.set() # Green light (will be cleared by wait_for_turn_authorization)

    def launch_simulation(self, universe: str, config_file: str):
        """
        Launch a new simulation process.
        
        Args:
            universe: Name of the universe (e.g., 'void_reckoning')
            config_file: Relative path to config (e.g., 'config/void_reckoning_config.json')
        """
        import subprocess
        import sys
        import os
        
        logger.info(f"Launching new simulation: Universe={universe}, Config={config_file}")
        
        # Determine command args
        # We run in 'campaign' mode with 'quick' settings for dashboard usage
        # Also ensure --dashboard flag is NOT passed if we are already running the dashboard?
        # Actually, passing --dashboard to run.py usually TRIES to launch a new dashboard process.
        # We DO NOT want that. We just want the simulation to run and log to the DB.
        
        cmd = [
            sys.executable,
            "run.py",
            "campaign",
            "--universe", universe,
            "--config", config_file,
            "--delay", "1.5" # Slow down specifically for dashboard viewing
            # Intentionally omitting --dashboard so we don't spawn a second server
        ]
        
        try:
            # FIX: Redirect stdout/stderr to a file to prevent pipe buffer deadlock
            # (If we use PIPE and don't read it, the process hangs after ~64KB)
            log_file = open("simulation.log", "w")
            
            # shell=False is safer, but we need CWD to be correct
            # "c:/Users/whitt/OneDrive/Desktop/New folder (4)" is our root
            proc = subprocess.Popen(
                cmd,
                cwd=os.getcwd(), # Ensure we run from project root
                stdout=log_file,
                stderr=subprocess.STDOUT
                # We don't join/wait here, let it run in background
            )
            logger.info(f"Simulation process started with PID: {proc.pid}")
            return proc.pid
        except Exception as e:
            logger.error(f"Failed to launch simulation: {e}")
            raise RuntimeError(f"Failed to launch simulation: {e}")


    def start_discovery_service(self):
        """Start the background auto-discovery thread."""
        if self.discovery_thread and self.discovery_thread.is_alive():
            return

        self.discovery_stop_event.clear()
        self.discovery_thread = threading.Thread(target=self._discovery_loop, daemon=True)
        self.discovery_thread.start()
        logger.info("Auto-Discovery service started.")

    def switch_run(self, run_id: str, batch_id: str = "unknown"):
        """
        Switch the active dashboard context to a specific run.
        Stops current streams, resets state, and starts new stream if available.
        """
        logger.info(f"Switching Dashboard Context to Run: {run_id}")
        
        # 1. Stop current stream
        if self.stream_thread and self.stream_thread.is_alive():
            self.stop_event.set()
            self.stream_thread.join(timeout=2.0)
            
        # 2. Update State
        self.run_id = run_id
        if batch_id != "unknown":
            self.batch_id = batch_id
        else:
            # Try to resolve batch_id if unknown
            # For now keep as is, discovery usually provides it
            pass

        # 3. Reset Caches & Telemetry
        self.control_paused = False # specific logic: new run starts unpaused? or paused? 
        # Actually, if we switch to an old run, we probably want it static/paused effectively?
        # But if it's the live run, we want it active. 
        # For now, safe default.
        
        self.galaxy_systems = [] # Force refresh
        
        # KEY FIX: Prevent bleed-through
        if self.telemetry:
            self.telemetry.reset()
            
        # 4. Resolve Path & Index
        from src.reporting.dashboard_v2.api.utils.discovery import discover_latest_run
        # We need a way to find path for specific run_id, not just latest.
        # But for valid context switching we assume the run exists.
        # Let's try to find it via the reports dir.
        # TODO: Add a helper `resolve_run_path(run_id)`.
        # For now, we will assume standard path structure if not provided.
        
        run_path = self._resolve_run_path(run_id)
        
        if run_path:
            # 5. Re-Initialize Database Connection for New Run
            # This is critical for the "Single Run Mode" architecture
            db_path = os.path.join(run_path, "campaign_data.db")
            logger.info(f"Switching Database to: {db_path}")
            
            # Close old indexer if exists
            if self.indexer and hasattr(self.indexer, 'conn'):
                 try:
                     self.indexer.conn.close()
                 except: pass
            
            # Create new indexer
            # We import here to avoid circulars if any, but it's already at top
            try:
                self.indexer = ReportIndexer(db_path=db_path)
                
                # Re-index if needed (sync)
                self.indexer.index_run(run_path, universe=self.universe)
                
                # Re-bind Data Provider
                self.data_provider = DashboardDataProvider(self.indexer)
                logger.info("Database and DataProvider re-initialized successfully.")
                
            except Exception as e:
                logger.error(f"Failed to re-initialize database for switched run: {e}")
            
            # Start Stream
            self.start_telemetry_stream(run_path)
        else:
            logger.warning(f"Could not resolve path for run {run_id}, streaming disabled.")
            
        logger.info(f"Switched to Run: {self.run_id}")
        return True

    def _resolve_run_path(self, run_id: str) -> Optional[str]:
        """Helper to find the directory for a given run_id."""
        import glob
        # Search in reports/universe/batch_*/run_id
        # This is expensive? Maybe use DataProvider or Indexer?
        # Simple glob for now.
        base = f"reports/{self.universe}"
        # Matches reports/void_reckoning/batch_*/run_ID
        pattern = os.path.join(base, "batch_*", run_id)
        matches = glob.glob(pattern)
        if matches:
             return matches[0]
        return None

    def _discovery_loop(self):
        """Periodically check for new runs."""
        import time
        from src.reporting.dashboard_v2.api.utils.discovery import discover_latest_run

        logger.info("Auto-Discovery loop running...")
        
        while not self.discovery_stop_event.is_set():
            try:
                time.sleep(5)
                
                batch_id, latest_run_id, latest_run_path = discover_latest_run(self.universe)
                
                if latest_run_id and latest_run_id != self.run_id:
                    logger.info(f"Auto-Discovery: New run detected! Switching from {self.run_id} to {latest_run_id}")
                    self.switch_run(latest_run_id, batch_id)
                    
            except Exception as e:
                logger.error(f"Error in auto-discovery loop: {e}")
                time.sleep(5)

    def get_available_runs(self, universe: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all available runs across all batches for the given universe.
        Scans disk to ensure all runs are found, even with scoped DBs.
        """
        from src.reporting.dashboard_v2.api.utils.discovery import discover_all_runs
        # Use our new disk-scanning utility
        return discover_all_runs(universe or self.universe)


    def start_telemetry_stream(self, run_path: str):
        """
        Start streaming events from campaign.json in real-time.
        """
        if self.stream_thread and self.stream_thread.is_alive():
            self.stop_event.set()
            self.stream_thread.join(timeout=2.0)
            
        self.stop_event.clear()
        self.stream_thread = threading.Thread(
            target=self._stream_telemetry,
            args=(run_path,),
            daemon=True
        )
        self.stream_thread.start()
        logger.info(f"Started telemetry stream for {run_path}")

    def _stream_telemetry(self, run_path: str):
        """
        Background loop to tail the latest telemetry file and broadcast events.
        """
        import glob
        
        # FIX: Find the latest telemetry file instead of hardcoding campaign.json
        # The engine writes to telemetry_TIMESTAMP.json
        pattern = os.path.join(run_path, "telemetry_*.json")
        telemetry_files = glob.glob(pattern)
        
        # Fallback to campaign.json if no telemetry files found
        if not telemetry_files:
            log_path = os.path.join(run_path, "campaign.json")
        else:
            # Sort by modification time to get the newest active log
            log_path = max(telemetry_files, key=os.path.getmtime)

        logger.info(f"Streaming from active log: {log_path}")
        
        tailer = LogTailer(log_path)
        
        # Initial open - seek to end to avoid re-pumping old history?
        # Ideally, history is handled by Indexer.index_run() or data_provider.
        # We only want *new* events.
        if not tailer.open(seek_end=False):
            logger.warning(f"Could not open {log_path} for streaming")
            return

        logger.info(f"Tailing {log_path}...")
        
        while not self.stop_event.is_set():
            try:
                # 1. Read available lines
                for line in tailer.read_lines():
                    try:
                        event = json.loads(line)
                        
                        # A. Broadcast to WebSocket
                        self.process_remote_event(event)
                        
                        # B. Persist to Database (Real-time Indexing)
                        if self.indexer:
                             self.indexer.index_event(
                                 event, 
                                 batch_id=self.batch_id, 
                                 run_id=self.run_id, 
                                 universe=self.universe
                             )
                             
                    except json.JSONDecodeError:
                        pass # partial line or noise
                    except Exception as ev_err:
                        logger.error(f"Error processing stream event: {ev_err}")

                # 2. Check for rotation/file changes
                if tailer.check_rotation():
                    logger.info("Log rotation detected, reopening...")
                
                # 3. Sleep briefly
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"Critical error in telemetry stream: {e}")
                # Don't break, try to continue or let it loop? 
                # If we break, the thread dies. better to sleep and retry.
                time.sleep(1.0)
                
        logger.warning(f"Telemetry stream thread for {log_path} EXITED.")
        
        tailer.close()
        logger.info("Telemetry stream stopped.")

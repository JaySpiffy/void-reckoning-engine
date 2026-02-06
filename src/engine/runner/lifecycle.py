import os
import sys
import time
import queue
import logging
import traceback
import datetime
import multiprocessing
import multiprocessing.pool
from multiprocessing import Queue, Manager
from typing import List, Dict, Any, Optional

# Core Imports
from src.core.config import set_active_universe
from src.engine.runner.simulation_worker import run_single_campaign_wrapped, worker_init
from src.managers.fleet_queue_manager import FleetQueueManager

logger = logging.getLogger(__name__)

# --- Custom Pool for Nested Multiprocessing ---
# Standard multiprocessing.Pool workers are daemon processes and cannot spawn children.
# We need to subclass Process to make it non-daemon to allow _run_universe_batch to spawn its own Pool.

class NoDaemonProcess(multiprocessing.Process):
    @property
    def daemon(self):
        return False

    @daemon.setter
    def daemon(self, value):
        pass

class NoDaemonContext(type(multiprocessing.get_context())):
    def Process(self, *args, **kwds):
        proc = NoDaemonProcess(*args, **kwds)
        # Ensure it's not daemon
        proc._config['daemon'] = False 
        return proc

class NoDaemonPool(multiprocessing.pool.Pool):
    def __init__(self, *args, **kwargs):
        kwargs['context'] = NoDaemonContext()
        super().__init__(*args, **kwargs)

# ----------------------------------------------

# Module-level initializer to ensure picklability on Windows
def pool_worker_init(q, u_name, in_q=None, out_q=None):
    """
    Initializer for simulation worker pools.
    Sets the active universe context and initializes FleetQueueManager.
    """
    # 1. Standard Init (Queue)
    worker_init(q)
    
    # 2. Set Universe
    try:
        from src.core.config import set_active_universe
        set_active_universe(u_name)
    except ImportError:
         pass

    # 3. Set Fleet Queues
    if in_q and out_q:
        FleetQueueManager.initialize(in_q, out_q, progress_q=q)

def set_cpu_affinity(affinity_list: List[int]):
    """
    Sets the CPU affinity for the current process.
    Supported on Linux and Windows (via psutil).
    """
    if not affinity_list:
        return

    try:
        if sys.platform.startswith('linux'):
            os.sched_setaffinity(0, affinity_list)
        elif sys.platform == 'win32':
            try:
                import psutil
                p = psutil.Process()
                p.cpu_affinity(affinity_list)
            except ImportError:
                logger.warning("Warning: 'psutil' module required for CPU affinity on Windows.")
            except Exception as e:
                logger.warning(f"Warning: CPU affinity not supported on {sys.platform}: {e}")
        else:
            logger.warning(f"Warning: CPU affinity not supported on {sys.platform}")
    except Exception as e:
        logger.error(f"Failed to set CPU affinity to {affinity_list}: {e}")

def run_universe_batch(universe_name: str, game_config: Dict, num_runs: int, 
                       output_dir: str, progress_queue: Queue, 
                       processor_affinity: Optional[List[int]] = None,
                       incoming_fleet_q: Optional[Queue] = None,
                       outgoing_fleet_q: Optional[Queue] = None) -> List[Dict]:
    """
    Worker function that runs a batch of simulations for a single universe.
    This runs in a child process of MultiUniverseRunner.
    """
    # 1. Set Affinity
    if processor_affinity:
        set_cpu_affinity(processor_affinity)
    
    # 2. Set Universe Context
    set_active_universe(universe_name)
    
    # 3. Setup Directories
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = os.path.join(output_dir, universe_name, f"batch_{timestamp}")
    os.makedirs(batch_dir, exist_ok=True)
    
    # 4. Prepare Simulation Params
    camp_conf = game_config.get("campaign", {})
    eco_conf = game_config.get("economy", {})
    
    turns = camp_conf.get("turns", 100)
    num_systems = camp_conf.get("num_systems", 20)
    
    # Hardware utilization for THIS universe batch
    workers = 1
    if processor_affinity:
        workers = len(processor_affinity)
    else:
        workers = max(1, multiprocessing.cpu_count() // 2)
        
    tasks = []
    for i in range(num_runs):
        run_id = i + 1
        task = (
            run_id,
            turns,
            num_systems,
            batch_dir,
            camp_conf.get("min_planets", 1),
            camp_conf.get("max_planets", 5),
            camp_conf.get("combat_rounds", 500),
            game_config.get("units", {}).get("max_fleet_size", 50),
            game_config.get("units", {}).get("max_land_army_size", 20),
            eco_conf.get("base_income_req", 1000),
            dict(game_config, universe=universe_name)
        )
        tasks.append(task)
        
    # 5. Execute Runs
    # If num_runs is 1, run sequentially in this process to avoid nested pool overhead/deadlocks on Windows
    if num_runs == 1:
        try:
            # Inline initialization since there is no pool
            from src.engine.runner.simulation_worker import worker_init
            worker_init(progress_queue)
            
            set_active_universe(universe_name)
            if incoming_fleet_q and outgoing_fleet_q:
                FleetQueueManager.initialize(incoming_fleet_q, outgoing_fleet_q, progress_q=progress_queue)
            
            results = [run_single_campaign_wrapped(tasks[0])]
            return results
        except Exception as e:
            logger.error(f"Sequential run failed: {e}")
            return []

    # Standard pool for multiple runs
    pool = multiprocessing.Pool(
        processes=workers, 
        initializer=pool_worker_init, 
        initargs=(progress_queue, universe_name, incoming_fleet_q, outgoing_fleet_q)
    )
        
    try:
        results_async = pool.map_async(run_single_campaign_wrapped, tasks)
        results = results_async.get()
        
        pool.close()
        pool.join()
        
        return results
        
    except Exception as e:
        tb = traceback.format_exc()
        crash_file = os.path.join(output_dir, universe_name, "crash_log.txt")
        try:
            os.makedirs(os.path.dirname(crash_file), exist_ok=True)
            with open(crash_file, "w") as f:
                f.write(f"CRASH AT {datetime.datetime.now()}\n")
                f.write(tb)
        except:
            pass
            
        progress_queue.put((0, 0, f"Error: {str(e)[:50]}...", {"full_error": str(e), "traceback": tb}))
        traceback.print_exc()
        pool.terminate()
        return []

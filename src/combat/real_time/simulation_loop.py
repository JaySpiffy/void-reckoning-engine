import time
from typing import Callable, Optional

class SimulationLoop:
    """
    Handles the high-frequency tick loop for real-time combat simulation.
    """
    def __init__(self, tick_rate: int = 20):
        self.tick_rate = tick_rate
        self.dt = 1.0 / tick_rate
        self.is_running = False
        self.on_update: Optional[Callable[[float], None]] = None
        
    def start(self, duration_seconds: Optional[float] = None):
        """
        Starts the simulation loop.
        If duration_seconds is provided, it runs for that long and stops.
        """
        self.is_running = True
        accumulated_time = 0.0
        
        while self.is_running:
            start_time = time.time()
            
            if self.on_update:
                self.on_update(self.dt)
            
            # Progress tracking
            accumulated_time += self.dt
            if duration_seconds and accumulated_time >= duration_seconds:
                self.is_running = False
                break
                
            # Sleep to maintain tick rate
            elapsed = time.time() - start_time
            sleep_time = max(0, self.dt - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
                
    def stop(self):
        self.is_running = False

    def pause(self):
        # In a more complex implementation, this would freeze the accumulators
        self.is_running = False

    def resume(self):
        self.is_running = True

from typing import Optional, Any
from multiprocessing import Queue
import logging
import queue

logger = logging.getLogger(__name__)

class FleetQueueManager:
    """
    Singleton-style manager for fleet transfer queues.
    Encapsulates raw Queue operations and provides typed access.
    Shared across the process via a class-level instance.
    """
    _instance: Optional['FleetQueueManager'] = None

    def __init__(self, incoming_q: Optional[Queue] = None, outgoing_q: Optional[Queue] = None, progress_q: Optional[Queue] = None):
        self.incoming_q = incoming_q
        self.outgoing_q = outgoing_q
        self.progress_q = progress_q
        
    @classmethod
    def initialize(cls, incoming_q: Queue, outgoing_q: Queue, progress_q: Optional[Queue] = None) -> None:
        """Initializes the singleton instance for this process."""
        cls._instance = cls(incoming_q, outgoing_q, progress_q)
        # logger.debug("FleetQueueManager initialized for process.")

    @classmethod
    def get_instance(cls) -> 'FleetQueueManager':
        """Returns the singleton instance. Warns if not initialized."""
        if cls._instance is None:
            # logger.warning("FleetQueueManager accessed before initialization! (This is expected in single-universe or test modes)")
            return cls(None, None, None) # Return dummy to prevent crash
        return cls._instance

    def push_progress(self, message: Any) -> bool:
        """
        Pushes a progress/event message to the aggregation queue.
        """
        if not self.progress_q:
            return False
        try:
            self.progress_q.put(message, block=False)
            return True
        except Exception as e:
            logger.error(f"Error pushing to progress queue: {e}")
            return False

    def push_outgoing(self, fleet_package: Any) -> bool:
        """
        Pushes a fleet package to the outgoing queue (to Portal/Hub).
        Returns True if successful, False if queue is missing or full.
        """
        if not self.outgoing_q:
            return False
        try:
            self.outgoing_q.put(fleet_package, block=False)
            return True
        except queue.Full:
            logger.error("Outgoing fleet queue is FULL. Fleet package lost/dropped.")
            return False
        except Exception as e:
            logger.error(f"Error pushing to outgoing fleet queue: {e}")
            return False

    def push_incoming(self, fleet_package: Any) -> bool:
        """
        Pushes to incoming queue (mainly for testing or manual injection).
        """
        if not self.incoming_q:
            return False
        try:
            self.incoming_q.put(fleet_package, block=False)
            return True
        except Exception:
            return False

    def pop_incoming(self, block: bool = False, timeout: Optional[float] = None) -> Optional[Any]:
        """
        Retrieves a fleet package from the incoming queue (from Portal/Hub).
        """
        if not self.incoming_q:
            return None
        try:
            return self.incoming_q.get(block=block, timeout=timeout)
        except queue.Empty:
            return None
        except Exception as e:
            logger.error(f"Error popping from incoming fleet queue: {e}")
            return None
    
    def qsize_incoming(self) -> int:
        if not self.incoming_q: return 0
        try: return self.incoming_q.qsize()  # Note: qsize is not implemented on all platforms (like MacOS) 
        except NotImplementedError: return 0

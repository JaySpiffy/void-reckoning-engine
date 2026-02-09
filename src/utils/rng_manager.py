import random
from typing import Dict, Optional, Any

class RNGManager:
    """
    Centralized manager for Random Number Generator streams.
    Ensures deterministic behavior by managing isolated RNG instances for different game systems.
    """
    _instance = None
    
    def __init__(self):
        self._streams: Dict[str, random.Random] = {}
        self._base_seed: Optional[int] = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = RNGManager()
        return cls._instance

    def get_rng(self, stream_name: str) -> random.Random:
        """
        Returns the RNG instance for the specified stream.
        Creates a new instance if it doesn't exist.
        """
        if stream_name not in self._streams:
            self._streams[stream_name] = random.Random()
            # If we have a base seed, we might want to auto-seed new streams?
            # Ideally, streams are seeded explicitly via reseed_all or set_seed.
            # But for safety, if base_seed exists, we could derive a seed.
            if self._base_seed is not None:
                # Deterministic derivation based on stream name
                derived = self._derive_seed(stream_name, self._base_seed)
                self._streams[stream_name].seed(derived)
                
        return self._streams[stream_name]

    def set_seed(self, stream_name: str, seed: int):
        """Sets the seed for a specific stream."""
        rng = self.get_rng(stream_name)
        rng.seed(seed)

    def reseed_all(self, base_seed: int):
        """
        Reseeds all active streams (and future ones) based on a master seed.
        """
        self._base_seed = base_seed
        for name in self._streams:
            derived = self._derive_seed(name, base_seed)
            self._streams[name].seed(derived)

    def _derive_seed(self, stream_name: str, base_seed: int) -> int:
        """Derives a deterministic seed for a stream from a base seed."""
        # Simple string hash combination
        import hashlib
        stream_hash = int(hashlib.md5(stream_name.encode()).hexdigest(), 16) & 0xFFFFFFFF
        return (base_seed + stream_hash) & 0xFFFFFFFF

    def get_all_states(self) -> Dict[str, Any]:
        """Captures the internal state of all managed RNG streams."""
        states = {}
        for name, rng in self._streams.items():
            states[name] = rng.getstate()
        return states

    def restore_states(self, states: Dict[str, Any]):
        """Restores RNG streams to a previous state."""
        for name, state in states.items():
            # If stream doesn't exist, create it
            if name not in self._streams:
                self.get_rng(name)
            self._streams[name].setstate(state)

# Global Accessor
def get_stream(name: str) -> random.Random:
    return RNGManager.get_instance().get_rng(name)

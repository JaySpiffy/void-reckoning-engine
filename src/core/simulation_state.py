
class SimulationState:
    """
    Singleton class to track global simulation state versions for caching.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SimulationState, cls).__new__(cls)
            cls._instance.topology_version = 0
            cls._instance.blockade_version = 0
        return cls._instance
    
    @classmethod
    def get_topology_version(cls):
        return cls().topology_version

    @classmethod
    def get_blockade_version(cls):
        return cls().blockade_version
        
    @classmethod
    def inc_topology_version(cls):
        cls().topology_version += 1
        
    @classmethod
    def inc_blockade_version(cls):
        cls().blockade_version += 1

    @classmethod
    def reset(cls):
        cls().topology_version = 0
        cls().blockade_version = 0

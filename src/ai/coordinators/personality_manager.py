from typing import Optional, Any
from src.core.config import get_universe_config, ACTIVE_UNIVERSE
from universes.base.personality_template import FactionPersonality

class PersonalityManager:
    """
    Manages loading, retrieval, and adaptation of faction personalities.
    Extracts personality logic from StrategicAI.
    """
    def __init__(self, engine):
        self.engine = engine
        self.personality_loader = None
        self.active_universe = None
    
    def load_personalities(self, universe_name: Optional[str] = "void_reckoning"):
        """Loads personality module for the specified universe."""
        self.active_universe = universe_name
        try:
            config = get_universe_config(universe_name)
            self.personality_loader = config.load_module("ai_personalities")
            print(f"  > [STRATEGY] Loaded personalities for universe: {universe_name}")
        except Exception as e:
            print(f"  > [WARNING] Failed to load personalities for {universe_name}: {e}")
            # Fallback to local import if possible or handle error
            try:
                from universes.void_reckoning import ai_personalities as fallback
                self.personality_loader = fallback
                print(f"  > [STRATEGY] Using fallback personalities (void_reckoning)")
            except ImportError:
                print(f"  > [ERROR] Could not load fallback personalities!")
                self.personality_loader = None

    def get_faction_personality(self, faction: str) -> FactionPersonality:
        """Helper to get current personality (learned or DB)."""
        # Ensure loader is ready
        if not self.personality_loader:
            self.load_personalities(self.active_universe or ACTIVE_UNIVERSE)

        f_mgr = self.engine.factions.get(faction)
        personality = None
        
        if f_mgr and f_mgr.learned_personality:
            if isinstance(f_mgr.learned_personality, dict):
                 personality = FactionPersonality.from_dict(f_mgr.learned_personality)
            else:
                 personality = f_mgr.learned_personality
        
        previous_doctrine = getattr(personality, 'tech_doctrine', None) if personality else None
        
        if not personality and self.personality_loader:
            personality = self.personality_loader.get_personality(faction)
            # CACHE IT to prevent repeated lookups and ensure persistence
            if personality and f_mgr:
                f_mgr.learned_personality = personality
                
                # Log Initial Doctrine Assignment (Metric #1)
                new_doctrine = getattr(personality, 'tech_doctrine', 'PRAGMATIC')
                if self.engine and hasattr(self.engine, 'telemetry'):
                    from src.reporting.telemetry import EventCategory
                    self.engine.telemetry.log_event(
                        EventCategory.DOCTRINE,
                        "doctrine_assignment",
                        {
                            "faction": faction,
                            "turn": self.engine.turn_counter,
                            "doctrine_type": new_doctrine,
                            "doctrine_source": "personality_init",
                            "previous_doctrine": previous_doctrine,
                            "assignment_reason": "initialization"
                        },
                        turn=self.engine.turn_counter,
                        faction=faction
                    )
            
        # Hard fallback to a basic profile if nothing else works
        if not personality:
            personality = FactionPersonality(faction)
            
        return personality

    def __getstate__(self):
        state = self.__dict__.copy()
        if 'engine' in state: del state['engine']
        if 'personality_loader' in state: del state['personality_loader']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.engine = None
        self.personality_loader = None

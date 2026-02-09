from typing import List, Dict, Any, Optional
import time
import math
from src.combat.tactical_engine import CombatState
from src.core.constants import TACTICAL_GRID_SIZE, ACTIVE_FACTION_UNIT_CAP

# Import the Rust module
try:
    from void_reckoning_bridge import RustCombatEngine
except ImportError:
    print("Warning: void_reckoning_bridge not found. Rust combat will be unavailable.")
    RustCombatEngine = None

class RustTacticalEngine:
    """
    Wrapper for the Rust-based High Performance Combat Engine.
    Delegates heavy calculation to the native module.
    Supports reinforcements (per-faction deployment caps).
    """
    def __init__(self, width=None, height=None):
        self.width = width or TACTICAL_GRID_SIZE
        self.height = height or TACTICAL_GRID_SIZE
        self.rust_engine = None
        self.reserves = {} # faction -> list of units
        self.faction_centers = {}
        self.faction_map = {}
        self.faction_lookup = []
        self.unit_id_counter = 1
        self.unit_cap = ACTIVE_FACTION_UNIT_CAP
        
        if RustCombatEngine:
            self.rust_engine = RustCombatEngine(self.width, self.height)
            try:
                self._event_log = self.rust_engine.enable_event_logging()
            except Exception as e:
                print(f"Warning: Failed to enable combat event logging: {e}")
                self._event_log = None
        else:
            self.rust_engine = None
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
                telemetry_logger.log_event(
                    EventCategory.COMBAT, 
                    "combat_event", 
                    {
                        "severity": evt.severity,
                        "category": evt.category,
                        "message": evt.message,
                        "context": evt.context.trace_id if evt.context else None
                    }
                )
            
            self._event_log.clear()
            
        except Exception as e:
            # print(f"Failed to flush combat logs: {e}") # Reduce noise
            pass
            
    def set_correlation_id(self, trace_id: str, span_id: str):
        """Sets trace context for Rust engine."""
        if not self.rust_engine: return
        try:
            from void_reckoning_bridge import CorrelationContext
            ctx = CorrelationContext()
            ctx.trace_id = trace_id
            ctx.span_id = span_id
            self.rust_engine.set_correlation_context(ctx)
        except: pass
            
    def initialize_battle(self, armies_dict: Dict[str, List[Any]]):
        """Initializes battle with first batch of active units and stores the rest as reserves."""
        if not self.rust_engine: return
        
        num_factions = len(armies_dict)
        self.faction_lookup = list(armies_dict.keys())
        self.faction_map = {f: i for i, f in enumerate(self.faction_lookup)}
        self.reserves = {f: [] for f in self.faction_lookup}
        self.id_to_faction = {} 
        self.unit_id_counter = 1
        
        # Calculate Deployment Centers
        center_x, center_y = self.width / 2.0, self.height / 2.0
        radius = min(self.width, self.height) * 0.4
        centers = []
        if num_factions <= 2:
            margin = self.width * 0.1
            centers = [(margin, center_y), (self.width - margin, center_y)]
        else:
            for i in range(num_factions):
                angle = (2 * math.pi * i) / num_factions
                centers.append((center_x + radius * math.cos(angle), center_y + radius * math.sin(angle)))

        for faction, units in armies_dict.items():
            f_idx = self.faction_map.get(faction, 0)
            self.faction_centers[faction] = centers[f_idx] if f_idx < len(centers) else (center_x, center_y)
            
            # Deployment Cap
            active_batch = units[:self.unit_cap]
            self.reserves[faction] = units[self.unit_cap:]
            
            for i, unit in enumerate(active_batch):
                self._add_to_rust(unit, faction, i)
                
    def _add_to_rust(self, unit, faction, index):
        """Adds a single unit to the active Rust battle state."""
        f_idx = self.faction_map.get(faction, 0)
        base_x, base_y = self.faction_centers.get(faction, (self.width/2, self.height/2))
        
        bid = self.unit_id_counter
        self.unit_id_counter += 1
        unit.battle_id = bid
        self.id_to_faction[bid] = faction
        
        weapons_data = []
        if hasattr(unit, 'weapon_comps'):
            for w in unit.weapon_comps:
                w_type = getattr(w, 'weapon_stats', {}).get("type", "Kinetic")
                acc = getattr(w, 'accuracy', 0.8)
                weapons_data.append((
                    w.name, w_type,
                    float(getattr(w, 'weapon_stats', {}).get("range", 20.0)),
                    float(getattr(w, 'weapon_stats', {}).get("damage", 10.0)),
                    acc,
                    float(getattr(w, 'weapon_stats', {}).get("cooldown", 1.0))
                ))
        if not weapons_data and hasattr(unit, 'damage'):
            weapons_data.append(("Generic Battery", "Kinetic", 20.0, float(unit.damage), 0.8, 1.0))

        # Jitter around center
        offset_x = (index % 20) * 2.0
        offset_y = (index // 20) * 2.0
        
        # Extract stats
        speed = float(getattr(unit, 'base_movement_points', 10.0))
        if speed <= 0: speed = 10.0 # Fallback for valid movement
        
        evasion = float(getattr(unit, 'agility', 10.0))
        
        shields = 0.0
        if unit.health_comp:
            shields = float(getattr(unit.health_comp, 'max_shield', 0.0))
        
        armor = float(getattr(unit, 'armor', 0.0))

        self.rust_engine.add_unit(
            bid, 
            unit.name or "Unknown", 
            f_idx, 
            float(unit.max_hp), 
            base_x + offset_x, 
            base_y + offset_y, 
            weapons_data,
            speed,
            evasion,
            shields,
            armor,
            None # Cover (Default)
        )

    def _process_reinforcements(self):
        """Warp-in new units if a faction is below their active cap and has reserves."""
        if not self.rust_engine: return
        
        # 1. Get current alive counts from Rust
        raw_state = self.rust_engine.get_state()
        alive_by_faction = {f: 0 for f in self.faction_lookup}
        for row in raw_state:
            # bid, x, y, hp, alive = row
            bid, alive = row[0], row[4]
            if alive:
                faction = self.id_to_faction.get(bid)
                if faction:
                    alive_by_faction[faction] += 1
                    
        # 2. Reinforce factions that are below cap
        for faction, count in alive_by_faction.items():
            if count < self.unit_cap and self.reserves.get(faction):
                # How many can we warp in?
                needed = self.unit_cap - count
                to_warp = self.reserves[faction][:needed]
                self.reserves[faction] = self.reserves[faction][needed:]
                
                for i, unit in enumerate(to_warp):
                    # Use index for jitter? Let's use current time or some offset to avoid stacking
                    self._add_to_rust(unit, faction, count + i)
                
                print(f"[REINFORCEMENT] {faction} warping in {len(to_warp)} units. (Remaining: {len(self.reserves[faction])})")

    def resolve_round(self) -> bool:
        """Steps the engine and processes reinforcements."""
        if not self.rust_engine: return False
        cont = self.rust_engine.step()
        
        # Check for reinforcements every tick?
        # Maybe every 5 ticks to avoid high overhead if needed, but Rust is fast.
        self._process_reinforcements()
        
        return cont

    def get_state(self):
        if not self.rust_engine: return []
        return self.rust_engine.get_state()

    def sync_back_to_python(self, armies_dict):
        if not self.rust_engine: return
        raw_state = self.rust_engine.get_state()
        state_map = {row[0]: row for row in raw_state}
        for units in armies_dict.values():
            for unit in units:
                bid = getattr(unit, 'battle_id', None)
                if bid and bid in state_map:
                    _, x, y, hp, is_alive = state_map[bid]
                    unit.current_hp = max(0.0, hp)
                    if not is_alive:
                        unit.is_destroyed = True
                        if hasattr(unit, 'health_comp') and unit.health_comp: 
                            unit.health_comp.current_hp = 0.0
                    unit.grid_x, unit.grid_y = x, y

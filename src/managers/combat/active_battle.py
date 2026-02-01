import random
import hashlib
from typing import Optional, Dict, TYPE_CHECKING
from src.managers.combat.utils import ensure_tactical_ships

if TYPE_CHECKING:
    from src.models.fleet import Fleet
    from src.models.army import ArmyGroup
    from src.combat.combat_context import CombatContext

class ActiveBattle:
    """
    Represents a persistent battle at a specific location.
    """
    def __init__(self, location, battle_state, turn_started, context: Optional['CombatContext'] = None):
        import time
        self.location = location
        self.state = battle_state  # Now a CombatStateManager
        self.turn_started = turn_started
        self.start_time = time.time() # Track real duration
        self.context = context
        self.is_finished = False
        self.log_file = None
        self.json_file = None
        self.participating_fleets = set() # Set of Fleet IDs
        self.participating_armies = set() # Set of ArmyGroup IDs (Phase 18)
        self.faction_doctrines = battle_state.faction_doctrines # Cache doctrines
        
        # Seeded RNG for deployments (Comment 3)
        self._battle_rng = random.Random()
        self._initialize_battle_rng()
        
        # Phase 42: Military Performance Tracking
        self.pre_battle_counts: Dict[str, int] = {}
        self.faction_damage: Dict[str, float] = {}
        self.faction_resources_lost: Dict[str, float] = {}
        
    def _initialize_battle_rng(self):
        """Derives a stable seed for deployments based on location and turn."""
        game_config = {}
        if self.state and self.state.faction_metadata:
             first_entry = next(iter(self.state.faction_metadata.values()), {})
             if isinstance(first_entry, dict):
                 game_config = first_entry.get("game_config", {})
        
        base_seed = game_config.get("seed")
        if base_seed is not None:
             loc_str = getattr(self.location, 'name', str(self.location))
             loc_seed_int = int(hashlib.md5(loc_str.encode()).hexdigest(), 16) & 0xFFFFFFFF
             combat_seed = base_seed + self.turn_started + loc_seed_int
             self._battle_rng.seed(combat_seed + 10) # Offset to avoid correlation with combat logic
        
        # [LEARNING] Track Initial Power for Casualty Calculation
        self.initial_power = {}
        for f, units in self.state.armies_dict.items():
            # Estimate power using cost or fallback
            self.initial_power[f] = sum(getattr(u, 'cost', 10) for u in units)
        
    def add_fleet(self, fleet: 'Fleet'):
        """Adds a new fleet's forces to the ongoing battle."""
        # Check overlap
        if fleet.id in self.participating_fleets: return

        # Tactical Conversion
        ships = [u for u in fleet.units if u.is_ship()]
        tactical_ships = ensure_tactical_ships(ships)
        
        # [QUIRK] Home Defense Bonus (replaces hardcoded Hegemony logic)
        is_home_turf = getattr(self.location, 'owner', '') == fleet.faction
        if is_home_turf:
            for u in tactical_ships:
                if u.home_defense_morale_bonus > 0:
                    u.current_morale = min(100, getattr(u, 'current_morale', 50) + u.home_defense_morale_bonus)
                if u.home_defense_toughness_bonus > 0:
                    u.toughness = getattr(u, 'toughness', 0) + u.home_defense_toughness_bonus
        
        # Tag Units with Fleet ID for dynamic removal
        for u in tactical_ships:
            u._fleet_id = fleet.id

        # Add to armies_dict
        f_name = fleet.faction
        self.state.add_faction_units(f_name, tactical_ships)
        self.participating_fleets.add(fleet.id)
        
        # Track initial counts
        self.pre_battle_counts[f_name] = self.pre_battle_counts.get(f_name, 0) + len(tactical_ships)
        if f_name not in self.faction_damage:
            self.faction_damage[f_name] = 0.0
            self.faction_resources_lost[f_name] = 0.0
        
        if f_name not in self.faction_doctrines:
            # Comment 2: Fetch doctrine from TaskForce
            tf = self.context.strategic_ai.get_task_force_for_fleet(fleet)
            if tf:
                if not tf.combat_doctrine:
                    tf.determine_combat_doctrine()
                self.faction_doctrines[f_name] = tf.combat_doctrine
            else:
                self.faction_doctrines[f_name] = "CHARGE"
            
            # Sync to battle_state
            self.state.faction_doctrines[f_name] = self.faction_doctrines[f_name]
            
            # Feature 110: Faction Metadata for Doctrines
            if tf:
                self.state.faction_metadata[f_name] = {
                    "faction_doctrine": tf.faction_combat_doctrine,
                    "intensity": tf.doctrine_intensity
                }
            else:
                 self.state.faction_metadata[f_name] = {
                    "faction_doctrine": "STANDARD",
                    "intensity": 1.0
                }

        # Update Initial Power tracking
        added_power = sum(getattr(u, 'cost', 10) for u in tactical_ships)
        self.initial_power[f_name] = self.initial_power.get(f_name, 0) + added_power
        
        # Deploy them! (Grid Placement)
        grid = self.state.grid
        for u in tactical_ships:
            if not u.is_alive(): continue
            edge = self._battle_rng.choice(["top", "bottom", "left", "right"])
            if not grid.place_unit_near_edge(u, edge):
                    grid.place_unit_randomly(u)

    def add_army(self, army_group: 'ArmyGroup'):
        """Phase 18: Adds a new army's forces to the ongoing battle."""
        if army_group.id in self.participating_armies: return
        self.participating_armies.add(army_group.id)
        
        f_name = army_group.faction
        if f_name not in self.state.armies_dict:
            self.state.armies_dict[f_name] = []
            
        # Tag Units
        for u in army_group.units:
            u._fleet_id = army_group.id # Reusing tag
            
        self.state.add_faction_units(f_name, army_group.units)
            
        # Track initial counts
        self.pre_battle_counts[f_name] = self.pre_battle_counts.get(f_name, 0) + len(army_group.units)
        if f_name not in self.faction_damage:
            self.faction_damage[f_name] = 0.0
            self.faction_resources_lost[f_name] = 0.0
            
        # Update Initial Power tracking
        added_power = sum(getattr(u, 'cost', 10) for u in army_group.units)
        self.initial_power[f_name] = self.initial_power.get(f_name, 0) + added_power
        
        army_group.is_engaged = True
        
        # Deploy them!
        grid = self.state.grid
        for u in army_group.units:
            if not u.is_alive(): continue
            # [QUIRK] Home Defense Bonus
            if army_group.faction == getattr(self.location, 'owner', ''):
                 if u.home_defense_morale_bonus > 0:
                      u.current_morale = min(100, getattr(u, 'current_morale', 50) + u.home_defense_morale_bonus)
                 if u.home_defense_toughness_bonus > 0:
                      u.toughness = getattr(u, 'toughness', 0) + u.home_defense_toughness_bonus

            # Armies deploy on the other axis or randomly
            edge = self._battle_rng.choice(["left", "right", "top", "bottom"])
            if not grid.place_unit_near_edge(u, edge):
                grid.place_unit_randomly(u)
        
        print(f"      - Army {army_group.id} units added to tactical state.")

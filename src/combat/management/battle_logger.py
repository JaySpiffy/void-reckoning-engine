import time
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from src.reporting.telemetry import EventCategory

if TYPE_CHECKING:
    from src.managers.combat.active_battle import ActiveBattle
    from src.core.interfaces import IEngine

class BattleLogger:
    """
    Extracted component for handling combat telemetry, result logging, 
    and performance metrics.
    """
    def __init__(self, context: 'IEngine') -> None:
        self.context = context

    def log_battle_composition(self, battle: 'ActiveBattle', location: Any):
        """Log battle composition telemetry."""
        if not self.context.telemetry:
            return
            
        for f_name in battle.state.armies_dict:
            units = battle.state.armies_dict.get(f_name, [])
            composition = self._get_force_composition(units)
            veterancy_levels = self._get_veterancy_levels(units)
            
            self.context.telemetry.log_event(
                EventCategory.COMBAT,
                "battle_composition",
                {
                    "battle_id": getattr(battle, 'battle_id', ''),
                    "faction": f_name,
                    "turn": self.context.turn_counter,
                    "composition": composition,
                    "veterancy_levels": veterancy_levels
                },
                turn=self.context.turn_counter,
                faction=f_name
            )

    def log_battle_decisiveness(self, battle: 'ActiveBattle', winner: str, faction_costs: Dict[str, Dict[str, float]], total_lost_value: float, location: Any):
        """Calculates and logs battle decisiveness (Metric #3)."""
        if not self.context.telemetry:
            return

        winner_stats = faction_costs.get(winner, {"initial": 1, "lost": 0})
        winner_loss_pct = (winner_stats["lost"] / winner_stats["initial"]) if winner_stats["initial"] > 0 else 0.0
        
        loser_initial = 0
        loser_lost = 0
        for f, stats in faction_costs.items():
            if f != winner:
                loser_initial += stats["initial"]
                loser_lost += stats["lost"]
        
        loser_loss_pct = (loser_lost / loser_initial) if loser_initial > 0 else 0.0
        
        # Determine Label
        label = "marginal"
        if winner_loss_pct < 0.10 and loser_loss_pct > 0.50:
            label = "overwhelming"
        elif winner_loss_pct < 0.30 and loser_loss_pct > 0.50:
            label = "decisive"
        elif winner_loss_pct > 0.40:
            label = "pyrrhic"
            
        self.context.telemetry.log_event(
            EventCategory.COMBAT,
            "battle_decisiveness",
            {
                "battle_id": getattr(battle, 'battle_id', ''),
                "winner": winner,
                "decisiveness": label,
                "winner_loss_pct": winner_loss_pct,
                "loser_loss_pct": loser_loss_pct,
                "total_value_destroyed": total_lost_value,
                "location": getattr(location, 'name', str(location))
            },
            turn=self.context.turn_counter
        )

    def log_doctrine_performance(self, battle: 'ActiveBattle'):
        """Logs doctrine performance for each faction (Metric #4)."""
        if not self.context.telemetry:
            return

        rounds = battle.state.round_num
        doctrines = getattr(battle.state, 'faction_doctrines', {})
        
        for f_name, doctrine in doctrines.items():
            self.context.telemetry.log_event(
                EventCategory.COMBAT,
                "doctrine_combat_performance",
                {
                    "faction": f_name,
                    "doctrine": doctrine,
                    "rounds_lasted": rounds,
                },
                turn=self.context.turn_counter,
                faction=f_name
            )

    def _get_force_composition(self, units: List[Any]) -> Dict[str, Any]:
        """Categorize units into composition types."""
        comp = {
            "capital_ships": {"count": 0, "lost": 0, "tier_avg": 0.0},
            "escorts": {"count": 0, "lost": 0, "tier_avg": 0.0},
            "ground_infantry": {"count": 0, "lost": 0},
            "ground_armor": {"count": 0, "lost": 0},
            "ground_artillery": {"count": 0, "lost": 0},
            "special_units": {"count": 0, "lost": 0}
        }
        tier_sum = {"capital": 0, "escort": 0}
        
        for u in units:
            is_alive = u.is_alive()
            domain = getattr(u, 'domain', '')
            is_ground = (domain == 'ground' or u.__class__.__name__ == 'Regiment')
            
            category = "count" if is_alive else "lost"
            
            if is_ground:
                if hasattr(u, 'ship_class'): # Some units might be hybrid or mis-classed
                    s_class = getattr(u, 'ship_class', 'Escort')
                    self._update_ship_comp(u, comp, tier_sum, s_class, category)
                else:
                    u_type = getattr(u, 'unit_type', '')
                    if u_type == 'infantry': comp["ground_infantry"][category] += 1
                    elif u_type == 'armor': comp["ground_armor"][category] += 1
                    elif u_type == 'artillery': comp["ground_artillery"][category] += 1
                    else: comp["special_units"][category] += 1
            else:
                s_class = getattr(u, 'ship_class', 'Escort')
                self._update_ship_comp(u, comp, tier_sum, s_class, category)
        
        # Calculate average tiers
        alive_capitals = comp["capital_ships"]["count"]
        if alive_capitals > 0:
            comp["capital_ships"]["tier_avg"] = tier_sum["capital"] / alive_capitals
        
        alive_escorts = comp["escorts"]["count"]
        if alive_escorts > 0:
            comp["escorts"]["tier_avg"] = tier_sum["escort"] / alive_escorts
        
        return comp

    def _update_ship_comp(self, u, comp, tier_sum, s_class, category):
        tier = getattr(u, 'tier', 1)
        if not isinstance(tier, (int, float)):
            tier = 1

        if s_class == "Battleship" or tier >= 3:
            comp["capital_ships"][category] += 1
            if category == "count":
                tier_sum["capital"] += tier
        else:
            comp["escorts"][category] += 1
            if category == "count":
                tier_sum["escort"] += tier

    def _get_veterancy_levels(self, units: List[Any]) -> Dict[str, int]:
        """Count veterancy levels of units."""
        levels = {"rookie": 0, "veteran": 0, "elite": 0}
        for u in units:
            if u.is_alive():
                xp = getattr(u, 'xp', 0)
                if not isinstance(xp, (int, float)):
                    xp = 0
                if xp < 100: levels["rookie"] += 1
                elif xp < 300: levels["veteran"] += 1
                else: levels["elite"] += 1
        return levels

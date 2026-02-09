from typing import Dict, List, Optional, Any
from src.core.constants import VICTORY_PLANET_THRESHOLD

class MissionManager:
    """
    Manages campaign missions, objectives, and victory conditions.
    """
    def __init__(self, logger=None):
        self.logger = logger
        self.active_missions: Dict[str, Dict] = {}
        self.completed_missions = set()
        self.active_victory_conditions: List[Dict] = []

    # [PHASE 8] Serialization Support
    def __getstate__(self):
        """Custom serialization to handle logger."""
        state = self.__dict__.copy()
        if 'logger' in state: del state['logger']
        return state

    def __setstate__(self, state):
        """Custom deserialization."""
        self.__dict__.update(state)
        # Logger must be re-injected or lazily loaded
        self.logger = None 
        
    def register_victory_conditions(self, conditions: List[Dict]):
        """Registers custom victory conditions."""
        self.active_victory_conditions = conditions
        
    def load_mission_sequence(self, missions: List[Dict]):
        """Initializes mission tracking."""
        self.active_missions = {m["id"]: m for m in missions}
        self.completed_missions = set()
        if self.logger:
            self.logger.info(f"Loaded {len(missions)} missions.")

    def check_mission_objectives(self, turn: int, engine: Any):
        """Evaluates active missions."""
        if not self.active_missions: return
        
        # completed_this_turn = [] # Logic was incomplete in source
        # Placeholder for future implementation
        pass

    def check_victory_conditions(self, engine: Any) -> Optional[str]:
        """
        Checks if any faction has met the victory conditions.
        Returns the name of the winning faction, or None.
        """
        # 1. Custom Conditions
        if self.active_victory_conditions:
            for vc in self.active_victory_conditions:
                vtype = vc.get("type")
                if vtype == "conquest":
                    # Check % control
                    threshold = vc.get("conditions", {}).get("planets_controlled_percent", 0.75)
                    total = len(engine.all_planets)
                    if total == 0: continue
                    
                    for f_name, planets in engine.planets_by_faction.items():
                        if f_name == "Neutral": continue
                        if len(planets) / total >= threshold:
                            if self.logger:
                                self.logger.campaign(f"[VICTORY] {f_name} wins via Campaign Condition: {vc['description']}")
                            return f_name
                             
                elif vtype == "score":
                    # Check year
                    end_year = vc.get("conditions", {}).get("year", 2500)
                    # Turn to year conversion? Assume 1 turn = 1 month?
                    current_year = 2200 + (engine.turn_counter // 12)
                    if current_year >= end_year:
                        # Find highest score
                        # Placeholder
                        return "Federation" # Placeholder
                        
        # 2. Score Victory (Turn Limit)
        from src.core.constants import VICTORY_TURN_LIMIT
        # Use config limit if available, otherwise fallback to constant
        limit = engine.game_config.max_turns if hasattr(engine, 'game_config') and getattr(engine.game_config, 'max_turns', 0) > 0 else VICTORY_TURN_LIMIT
        
        if engine.turn_counter >= limit:
            scores = self._calculate_scores(engine)
            if scores:
                winner = max(scores.items(), key=lambda x: x[1])[0]
                if self.logger:
                    self.logger.campaign(f"[VICTORY] {winner} wins via SCORE VICTORY at Turn {engine.turn_counter}!")
                    self.logger.campaign(f"   Final Score: {scores[winner]}")
                    # Log all scores
                    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
                    for f, s in sorted_scores:
                        self.logger.campaign(f"   - {f}: {s}")
                return winner

        # 3. Default Conquest (Planet Threshold)
        total_planets = len(engine.all_planets)
        if total_planets == 0: return None
        
        threshold = int(total_planets * VICTORY_PLANET_THRESHOLD)
        tally: Dict[str, int] = {}
        for p in engine.all_planets:
            owner = getattr(p, 'owner', 'Neutral')
            tally[owner] = tally.get(owner, 0) + 1
            
        for faction, count in tally.items():
            if faction == "Neutral": continue
            if count >= threshold:
                if self.logger:
                    self.logger.campaign(f"[VICTORY] {faction} HAS WON THE CAMPAIGN! [Conquest Threshold]")
                return faction
        return None

    def _calculate_scores(self, engine: Any) -> Dict[str, int]:
        """Calculates current score for all factions (Formula matches Dashboard)."""
        from collections import defaultdict
        
        owners = defaultdict(int)
        systems_owned = defaultdict(set)
        buildings = defaultdict(int)
        armies = defaultdict(int)
        fleets = defaultdict(int)
        starbases = defaultdict(int)
        
        # 1. Aggregate Map Objects
        for p in engine.all_planets:
            if p.owner != "Neutral":
                owners[p.owner] += 1
                buildings[p.owner] += len(p.buildings)
                if hasattr(p, 'provinces'):
                    for n in p.provinces:
                        buildings[p.owner] += len(n.buildings)
                if hasattr(p, 'system') and p.system:
                    systems_owned[p.owner].add(p.system)

            # Armies
            p_armies = []
            if hasattr(p, 'armies'): p_armies.extend(p.armies)
            if hasattr(p, 'provinces'):
                for n in p.provinces:
                    if hasattr(n, 'armies'): p_armies.extend(n.armies)
            for ag in p_armies:
                if not ag.is_destroyed: armies[ag.faction] += 1
                
        # 2. Iterate Fleets
        for fl in engine.fleets:
            if not fl.is_destroyed: 
                fleets[fl.faction] += 1
                if hasattr(fl, 'cargo_armies'):
                    for ag in fl.cargo_armies:
                        if not ag.is_destroyed:
                            armies[ag.faction] += 1
                            
        # 3. Iterate Starbases
        if hasattr(engine, 'systems'):
            for s in engine.systems:
                if hasattr(s, 'starbases'):
                    for sb in s.starbases:
                        if sb.is_alive(): starbases[sb.faction] += 1

        # 4. Compute Final Scores
        scores = {}
        for f in engine.factions:
            if f == "Neutral": continue
            
            p_count = owners[f]
            s_count = len(systems_owned.get(f, set()))
            b_count = buildings[f]
            a_count = armies[f]
            f_count = fleets[f]
            sb_count = starbases[f]
            
            f_obj = engine.factions[f]
            req = int(f_obj.requisition)
            tech_count = len(f_obj.unlocked_techs)
            
            # Score Formula:
            # Planets(100) + Systems(500) + Buildings(50) + Fleets(20) + Armies(10) + Starbases(300) + Tech(1000) + Req(1/1000)
            score = (p_count * 100) + (s_count * 500) + (b_count * 50) + (f_count * 20) + (a_count * 10) + (sb_count * 300) + (tech_count * 1000) + int(req / 1000)
            scores[f] = score
            
        return scores

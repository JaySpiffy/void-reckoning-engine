
from typing import Dict, List, Optional, Any
from src.core.interfaces import IEngine
from src.reporting.telemetry import EventCategory
import random

class Coalition:
    """
    Represents a temporary alliance of factions with a specific shared goal.
    """
    def __init__(self, id: str, goal: str, target_faction: str, leader: str, formed_turn: int):
        self.id = id
        self.goal = goal # "CONTAIN", "DESTROY", "DEFEND"
        self.target_faction = target_faction
        self.leader = leader
        self.members: List[str] = [leader]
        self.formed_turn = formed_turn
        self.is_active = True
        
        # New Features
        self.resource_pool = 0
        self.coordinated_target = None # Planet Name

    def add_member(self, faction: str):
        if faction not in self.members:
            self.members.append(faction)

class CoalitionBuilder:
    """
    Manages the formation and coordination of Coalitions.
    """
    def __init__(self, ai_manager):
        self.ai = ai_manager
        self.engine = ai_manager.engine
        self.coalitions: Dict[str, Coalition] = {} # {coalition_id: Coalition}
        self.active_invites: Dict[str, List[str]] = {} # {faction: [coalition_id]}
        
    def process_turn(self, faction: str):
        """
        Evaluates opportunities to form or join coalitions.
        """
        # 1. Evaluate Existing Invites/Memberships
        self._manage_memberships(faction)
        
        # 2. Check for Coalition Opportunities (Leader Logic)
        self._evaluate_opportunities(faction)
        
        # 3. Manage Active Coalitions (Pooling & Coordination)
        for c in self.coalitions.values():
            if c.is_active and faction == c.leader:
                 self.pool_resources(c.id)

    def pool_resources(self, coalition_id: str):
        """
        Deducts requisition from members to fund the leader or shared objectives.
        """
        coalition = self.coalitions.get(coalition_id)
        if not coalition or not coalition.is_active: return
        
        total_collected = 0
        for member in coalition.members:
             # Basic logic: 5% of treasury contributed per turn
             f_obj = self.engine.get_faction(member)
             if f_obj and f_obj.requisition > 1000:
                  contribution = int(f_obj.requisition * 0.05)
                  f_obj.requisition -= contribution
                  total_collected += contribution
                  
        coalition.resource_pool += total_collected
        
        # Immediate payout to leader for war effort (Simulated Efficiency Loss 10%?)
        if total_collected > 0:
             leader_obj = self.engine.get_faction(coalition.leader)
             if leader_obj:
                  leader_obj.requisition += total_collected
                  if self.engine.logger and random.random() < 0.1:
                       self.engine.logger.diplomacy(f"[COALITION] {coalition_id} pooled {total_collected} requisition for Leader {coalition.leader}.")

    def set_coordinated_target(self, coalition_id: str, target: str):
        coalition = self.coalitions.get(coalition_id)
        if coalition:
            coalition.coordinated_target = target
            
    def _manage_memberships(self, faction: str):
        # Logic to leave coalition if goal is met or too costly
        pass
        
    def _evaluate_opportunities(self, faction: str):
        """
        Identifies if a faction should start a coalition.
        """
        # Only major powers or diplomatic factions start coalitions
        personality = self.ai.get_faction_personality(faction)
        if personality.diplomatic_tendency < 1.0: return
        
        # Check for Runaway Threats (The "Napoleon" check)
        # Find any faction with > 2x our power (and > 2x average power)
        my_power = self._get_faction_power(faction)
        
        threat = None
        for other in self.engine.factions:
            if other == faction or other == "Neutral": continue
            
            other_power = self._get_faction_power(other)
            
            # Threat Criteria:
            # 1. Significantly stronger (>2x)
            # 2. Aggressive (>1.5 aggression)
            # 3. Not already allied
            
            if other_power > my_power * 2.0:
                # Check relation/alignment
                rel = self.engine.diplomacy.get_relation(faction, other)
                if rel < -20:
                    threat = other
                    break
        
        if threat:
            # Check if coalition already exists against this threat
            existing = self._get_coalition_against(threat)
            if existing:
                # Join existing logic? (Simplification: Only leaders create for now)
                pass
            else:
                self._form_coalition(faction, threat, "CONTAIN")
                
    def _form_coalition(self, leader: str, target: str, goal: str):
        import uuid
        c_id = f"COALITION_{uuid.uuid4().hex[:8]}"
        
        coalition = Coalition(c_id, goal, target, leader, self.engine.turn_counter)
        self.coalitions[c_id] = coalition
        
        if self.engine.logger:
            self.engine.logger.diplomacy(f"[COALITION] {leader} is forming a COALITION against {target} (Goal: {goal})")
            
        # Invite neighbors/rivals of target
        potential_members = []
        for f in self.engine.factions:
            if f == leader or f == target or f == "Neutral": continue
            
            # Invite if:
            # 1. Also threatened (relation < 0 with target)
            # 2. Close to target (share border? simple dist check?)
            rel = self.engine.diplomacy.get_relation(f, target)
            if rel < 0:
                potential_members.append(f)
                
        # Send Invites (Instant acceptance for MVP)
        for member in potential_members:
            # Acceptance Chance
            acc_rel = self.engine.diplomacy.get_relation(member, leader)
            if acc_rel > 0:
                coalition.add_member(member)
                if self.engine.logger:
                    self.engine.logger.diplomacy(f"  > {member} joined our cause!")
                    
        # Log Telemetry
        if self.engine.telemetry:
             self.engine.telemetry.log_event(
                 EventCategory.DIPLOMACY, "coalition_formed",
                 {"leader": leader, "target": target, "members": coalition.members, "goal": goal},
                 turn=self.engine.turn_counter,
                 faction=leader
             )

    def _get_faction_power(self, faction: str) -> int:
        # Sum of fleet power + (owned planets * 100)
        f_mgr = self.engine.get_faction(faction)
        if not f_mgr: return 0
        
        fleet_power = sum(f.power for f in self.engine.fleets if f.faction == faction and not f.is_destroyed)
        planet_power = len(self.engine.planets_by_faction.get(faction, [])) * 100
        return fleet_power + planet_power

    def _get_coalition_against(self, target: str) -> Optional[Coalition]:
        for c in self.coalitions.values():
            if c.is_active and c.target_faction == target:
                return c
        return None
        
    def get_coalition_members(self, faction: str) -> List[str]:
        """Returns all allies from all coalitions this faction is in."""
        allies = set()
        for c in self.coalitions.values():
            if faction in c.members and c.is_active:
                for m in c.members:
                    if m != faction: allies.add(m)
        return list(allies)


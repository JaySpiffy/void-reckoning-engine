
from typing import Dict, List, Optional, Any
from src.core.interfaces import IEngine
import random

class ProactiveDiplomacy:
    """
    Manages proactive diplomatic initiatives based on strategic needs.
    Supplements the random checks in DiplomacyManager.
    """
    def __init__(self, ai_manager):
        self.ai = ai_manager
        self.engine = ai_manager.engine
        
    def process_turn(self, faction: str):
        """
        Evaluates strategic needs and initiates diplomatic actions.
        """
        f_mgr = self.engine.get_faction(faction)
        personality = self.ai.get_faction_personality(faction)
        
        if not f_mgr: return
        
        # 1. Evaluate Needs
        needs_money = False
        needs_security = False
        
        econ_report = self.engine.economy_manager.get_faction_economic_report(faction)
        if econ_report.get("margin", 1.0) < 1.2:
            needs_money = True
            
        threats = self.ai.predict_enemy_threats(faction)
        if threats:
            needs_security = True
            
        # 2. Take Action
        if needs_money:
            self._seek_trade_partners(faction)
            
        if needs_security:
            self._seek_defensive_pacts(faction, personality)
            
    def _seek_trade_partners(self, faction: str):
        # Find neighbors with neutral/positive relations who are not at war
        # And don't have a trade treaty yet
        for other in self.engine.factions:
            if other == faction or other == "Neutral": continue
            
            # Existing Treaty Check
            treaty = self.engine.diplomacy.get_treaty(faction, other)
            if treaty == "Trade" or treaty == "War": continue
            
            # Relation Check
            rel = self.engine.diplomacy.get_relation(faction, other)
            if rel >= 0:
                # Propose Trade
                self.engine.diplomacy.treaty_coordinator.set_treaty(faction, other, "Trade")
                if self.engine.logger:
                    self.engine.logger.diplomacy(f"[PROACTIVE] {faction} proposed TRADE with {other} to solve economic deficit.")
                return # One per turn

    def _seek_defensive_pacts(self, faction: str, personality):
        # If threatened, try to upgrade Peace -> Alliance or at least ensure Peace
        # Only if we aren't aggressive xenophobes
        if personality.diplomatic_tendency < 0.8: return
        
        for other in self.engine.factions:
            if other == faction or other == "Neutral": continue
            
            rel = self.engine.diplomacy.get_relation(faction, other)
            treaty = self.engine.diplomacy.get_treaty(faction, other)
            
            if rel > 50 and treaty != "Alliance" and treaty != "War":
                # Propose Alliance for security
                self.engine.diplomacy.treaty_coordinator.set_treaty(faction, other, "Alliance")
                if self.engine.logger:
                    self.engine.logger.diplomacy(f"[PROACTIVE] {faction} proposed ALLIANCE with {other} for mutual defense.")
                return

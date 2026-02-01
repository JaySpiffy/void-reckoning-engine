
import random
from typing import Dict, List, Optional, TYPE_CHECKING
from src.core.balance import ECON_RESERVE_MIN

if TYPE_CHECKING:
    from src.core.interfaces import IEngine
    from src.models.faction import Faction

class BankingManager:
    """
    The 'Iron Bank' of the Universe.
    - Issues loans to factions in need.
    - Collects interest every turn.
    - Enforces consequences for default (Funding enemies, mercenaries).
    """
    def __init__(self, engine: 'IEngine'):
        self.engine = engine
        self.loans = {}  # {faction_name: {"principal": 0, "interest_rate": 0.05, "turns_defaulted": 0}}
        self.bank_capital = 1000000 # The Bank starts with 1 Million Req (Theoretical)

    def process_banking_cycle(self):
        """Called every turn to collect interest and manage loans."""
        for f_name in self.engine.get_all_factions():
            faction = self.engine.get_faction(f_name.name)
            if not faction: continue
            
            # 1. Service Existing Loans
            self._service_loan(f_name.name, faction)
            
            # 2. Offer New Loans (If broke)
            if faction.requisition < 0:
                self._offer_loan(f_name.name, faction)

    def _service_loan(self, f_name: str, faction: 'Faction'):
        if f_name not in self.loans: return
        
        loan = self.loans[f_name]
        principal = loan["principal"]
        rate = loan["interest_rate"]
        
        # Calculate Interest Payment
        interest_payment = int(principal * rate)
        
        # Determine strictness: Bank always gets paid first?
        # Or do we add to debt?
        # "The Bank gets its due" -> Deduct directly, even if negative.
        faction.requisition -= interest_payment
        
        # Log transaction
        if self.engine.logger:
            self.engine.logger.economy(f"[BANK] {f_name} paid {interest_payment} interest. Remaining Principal: {principal}")

        # Try to pay down principal if rich
        if faction.requisition > 2000:
            payment = int(faction.requisition * 0.2) # Pay 20% of surplus
            faction.requisition -= payment
            loan["principal"] -= payment
            if self.engine.logger:
                 self.engine.logger.economy(f"[BANK] {f_name} paid down {payment} principal.")
            
            if loan["principal"] <= 0:
                del self.loans[f_name]
                if self.engine.logger: self.engine.logger.economy(f"[BANK] {f_name} has paid off their debt!")
                return

        # Default Check
        # If faction is broke and didn't pay principal? (Interest is auto-deducted so technical default is hard)
        # Real default is: "Requisition < -MaxCreditLimit"
        credit_limit = self._calculate_credit_limit(faction)
        if faction.requisition < -credit_limit:
            loan["turns_defaulted"] += 1
            self._enforce_consequences(f_name, faction, loan)
        else:
            loan["turns_defaulted"] = max(0, loan["turns_defaulted"] - 1)

    def _offer_loan(self, f_name: str, faction: 'Faction'):
        """AI Logic to take a loan."""
        if f_name in self.loans: return # Already have a loan (one at a time)
        
        deficit = abs(faction.requisition)
        limit = self._calculate_credit_limit(faction)
        
        if deficit > limit:
            # Bank refuses - too risky
            return
            
        # Bank offers to cover the deficit + buffer
        loan_amount = deficit + 5000
        interest_rate = 0.05 # 5% per turn
        
        # AI Logic: "Do I really need this?" -> Yes, I'm broke.
        faction.requisition += loan_amount
        self.loans[f_name] = {
            "principal": loan_amount,
            "interest_rate": interest_rate,
            "turns_defaulted": 0
        }
        
        if self.engine.logger:
            self.engine.logger.economy(f"[BANK] {f_name} took a LOAN of {loan_amount} @ 5% interest.")

    def _calculate_credit_limit(self, faction: 'Faction') -> int:
        """Limit is based on Income generation capability (Planets)."""
        # Rough estimate: 20 turns of Income
        # We need access to income stats.
        # Hack: Base limit + Planet Count * 1000
        planet_count = len([p for p in self.engine.get_all_planets() if p.owner == faction.name])
        return 10000 + (planet_count * 2000)

    def _enforce_consequences(self, f_name: str, faction: 'Faction', loan: dict):
        """The Iron Bank will have its due."""
        turns = loan["turns_defaulted"]
        
        if turns == 1:
            if self.engine.logger: self.engine.logger.warning(f"[BANK] {f_name} is in DEFAULT (Warning).")
        
        elif turns == 5:
            # Seize Assets (Remove a random unit/building?)
            # Or fund enemies.
            if self.engine.logger: self.engine.logger.warning(f"[BANK] {f_name} Default Level 2: Funding Enemies.")
            self._fund_enemies(f_name)
            
        elif turns > 10:
             # Total War: The Bank hires mercenaries (Nebula Drifters?) to attack.
             pass

    def _fund_enemies(self, target_faction: str):
        """Give money to whoever is at war with the defaulter."""
        enemies = [] # self.engine.diplomacy_manager.get_enemies(target_faction)
        # (Need access to diplomacy)
        pass 

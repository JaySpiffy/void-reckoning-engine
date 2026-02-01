from typing import List, Any, TYPE_CHECKING
from src.models.fleet import Fleet, TaskForce
from src.models.faction import Faction

if TYPE_CHECKING:
    from src.managers.ai_manager import StrategicAI
    from src.managers.ai_manager import FactionPersonality

class InterceptionStrategy:
    """
    Handles predictive interception of incoming enemy threats.
    """
    def __init__(self, ai_manager: 'StrategicAI'):
        self.ai = ai_manager

    def handle_predictive_interception(self, faction: str, available_fleets: List[Fleet], personality: 'FactionPersonality', econ_state: str, current_upkeep: int, income: int, zones: dict) -> List[Fleet]:
        """
        Detects incoming threats and dispatches interception task forces.
        """
        # --- PREDICTIVE INTERCEPTION (Phase 72) ---
        incoming_threats = self.ai.predict_enemy_threats(faction)
            
        if self.ai.engine.diplomacy:
                incoming_threats = [t for t in incoming_threats 
                                if self.ai.is_valid_target(faction, t['fleet'].faction)]
                                
        if not incoming_threats or len(available_fleets) < 1:
            return available_fleets
        
        # Sort threats by ETA (Urgency) and Value (Zone)
        # Prioritize: Capital Zone > Border Zone > Core Zone
        def threat_priority(t):
            zone = zones.get(t['target'].name, "CORE")
            score = 0
            if zone == "CAPITAL": score = 1000
            elif zone == "CAPITAL_ZONE": score = 800
            elif zone == "BORDER": score = 500
            else: score = 100
            
            # Urgency multiplier (Lower ETA = Higher priority)
            score += (100 - t['eta'])
            return score
        
        incoming_threats.sort(key=threat_priority, reverse=True)
        
        best_threat = incoming_threats[0]
        target_p = best_threat['target']
        
        # Check if static defense + existing fleets are enough
        existing_defense = self.ai.engine.intelligence_manager.get_theater_power(target_p.name, self.ai.engine.turn_counter).get(faction, 0)
        if existing_defense < best_threat['strength'] * 1.5:
                # INTERCEPT!
                self.ai.tf_counter += 1
                int_tf = TaskForce(f"INT-{self.ai.tf_counter}", faction)
                int_tf.target = target_p # Meet them there
                int_tf.rally_point = target_p
                
                # Feature 110: Assign Combat Doctrine
                int_tf.faction_combat_doctrine = personality.combat_doctrine
                int_tf.doctrine_intensity = personality.doctrine_intensity
                
                # Allocate fleets
                max_fleets = int(5 * personality.cohesiveness) + 1
                # If Capital, ALL HANDS ON DECK
                target_zone = zones.get(target_p.name, "CORE")
                if target_zone == "CAPITAL": max_fleets = 99
                
                count = min(len(available_fleets), max_fleets)
                
                chosen_interceptors = []
                for i in range(count):
                    f = available_fleets[i]
                    # Upkeep Check for Interception
                    if econ_state == "CRISIS" and target_zone != "CAPITAL":
                        if (current_upkeep + self.ai.calculate_fleet_upkeep(f)) > (income * 1.1):
                            break
                            
                    int_tf.add_fleet(f)
                    chosen_interceptors.append(f)
                    
                if int_tf.fleets:
                    self.ai.task_forces[faction].append(int_tf)
                    # print(f"  > [INTERCEPT] {faction} dispatching INT-{int_tf.id} to blocked {best_threat['fleet'].faction} at {target_p.name} (ETA: {best_threat['eta']})")
                    return [f for f in available_fleets if f not in chosen_interceptors]
        
        return available_fleets

import random
from typing import List, Any, TYPE_CHECKING
from src.models.fleet import Fleet, TaskForce
from src.models.faction import Faction

if TYPE_CHECKING:
    from src.managers.ai_manager import StrategicAI
    from src.managers.ai_manager import FactionPersonality

class DefensiveStrategy:
    """
    Handles defensive strategic decisions, including forming defensive task forces and managing reserves.
    """
    def __init__(self, ai_manager: 'StrategicAI'):
        self.ai = ai_manager

    def manage_strategic_reserves(self, faction: str, available_fleets: List[Fleet], threatened_planets: List[Any], is_bankrupt: bool) -> List[Fleet]:
        """
        Determines and isolates fleets for strategic reserve.
        """
        # --- PHASE 82: STRATEGIC RESERVES ---
        # Keep 20% of fleets in reserve unless threats exist
        reserve_count = int(len(available_fleets) * 0.2)
        has_critical_threat = False
        
        # Determine if we should release reserves
        # Critical Threat: Enemy on our territory or Capital threatened
        if threatened_planets:
            has_critical_threat = True
        elif any("Capital" in [n.type for n in p.provinces] for p in threatened_planets):
            has_critical_threat = True
        elif is_bankrupt:
            has_critical_threat = True # Desperation
            
        if not has_critical_threat and reserve_count > 0:
            # Let's sort by power - Strongest in reserve
            available_fleets.sort(key=lambda x: x.power, reverse=True)
            reserves = available_fleets[:reserve_count]
            # print(f"  > [STRATEGY] {faction} holding {len(reserves)} fleets in STRATEGIC RESERVE.")
            return available_fleets[reserve_count:]
        
        return available_fleets

    def handle_defensive_priority(self, faction: str, available_fleets: List[Fleet], threatened_planets: List[Any], personality: 'FactionPersonality', econ_health: dict, zones: dict = None) -> List[Fleet]:
        """
        Forms defensive task forces in response to threatened planets OR vulnerable construction sites.
        """
        # Phase 18: Identify construction sites that need escorts
        construction_targets = []
        for system in self.ai.engine.systems:
            for sb in system.starbases:
                if sb and sb.faction == faction and sb.is_under_construction:
                    # Match by identifying the fleet that contains this specific SB unit
                    sb_fleet = next((f for f in self.ai.engine.fleets if any(float_unit == sb for float_unit in f.units)), None)
                    
                    target_node = sb_fleet.location if sb_fleet else None
                    if not target_node: continue
                    
                    # ONLY escort if the construction node does NOT have an owned planet
                    p_obj = None
                    is_owned_planet_node = False
                    
                    if hasattr(target_node, 'metadata'):
                        p_obj = target_node.metadata.get("object")
                        if hasattr(target_node, 'type') and target_node.type == "Planet" and p_obj and p_obj.owner == faction:
                            is_owned_planet_node = True
                    elif hasattr(target_node, 'owner'):
                        # Planet object directly
                        p_obj = target_node
                        if target_node.owner == faction:
                            is_owned_planet_node = True
                    
                    if not is_owned_planet_node:
                        # Target the specific node (TaskForce handles Planets or Nodes)
                        construction_targets.append(target_node)
        
        # PROACTIVE: Identify "Strategic Gaps" (Choke points with no defense station)
        # If we have spare fleets, send them to vital chokes to build stations.
        if len(available_fleets) > 2:
            from src.services.construction_service import ConstructionService
            # We can't easily instantiate a new CS here, so we'll check the engine's one if it exists
            cs = getattr(self.ai.engine, 'construction_service', None)
            if cs:
                owned_planets = self.ai.engine.planets_by_faction.get(faction, [])
                if not owned_planets: return available_fleets
                
                # Identify systems to check: owned systems and their neighbors
                candidate_systems = set()
                for p in owned_planets:
                    candidate_systems.add(p.system)
                    if hasattr(p.system, 'connections'):
                        for neighbor in p.system.connections:
                            candidate_systems.add(neighbor)
                
                for system in candidate_systems:
                    # Is this system strategic?
                    if cs._is_strategic_system(system, self.ai.engine.factions[faction], owned_planets):
                        # Check for existing station at gateway nodes
                        for node in system.nodes:
                            if node.type in ["FluxPoint", "Portal"]:
                                has_station = any(any(u.unit_class == "Starbase" for u in f.units) for f in self.ai.engine.fleets if f.location == node)
                                if not has_station:
                                    # Choke point identified with no station!
                                    # Check if a Task Force is already heading there
                                    is_assigned = any(tf.target == node for tf in self.ai.task_forces[faction])
                                    if not is_assigned:
                                        construction_targets.append(node)
                                        if self.ai.engine.logger:
                                            self.ai.engine.logger.campaign(f"[DEFENSE] {faction} targeting Strategic Gap at {node.name} for Station Construction.")
        
        # Combine with threatened planets
        all_targets = list(threatened_planets)
        for ct in construction_targets:
            if ct not in all_targets:
                all_targets.append(ct)
                
        # --- NEW: ALLIED DEFENSE (MUTUAL AID) ---
        # Safeguard: Only help allies if home is secure and economy is stable
        econ_state = econ_health.get('state', 'HEALTHY')
        allied_threats = []
        if not threatened_planets and econ_state not in ["CRISIS", "BANKRUPT"]:
            allied_threats = self.handle_allied_defense(faction, available_fleets, personality)
            
        for at in allied_threats:
            if at not in all_targets:
                all_targets.append(at)

        if not available_fleets or not all_targets:
            return available_fleets
        
        # Determine priority target
        target = None
        # Capitals first
        for p in all_targets:
            if zones and zones.get(p.name) == "CAPITAL":
                target = p
                break
        
        # Then construction sites (Strategic Importance)
        if not target:
            for p in all_targets:
                if p in construction_targets:
                    target = p
                    break
                    
        # Then Direct Threats to Allies
        if not target:
            for p in all_targets:
                if p in allied_threats:
                    target = p
                    break
        
        # Fallback
        if not target:
            target = random.choice(all_targets)

        # Form a Defensive Response TF
        self.ai.tf_counter += 1
        is_allied_aid = target in allied_threats
        role = "DEFENSE" if not is_allied_aid else "ALLIED_AID"
        
        def_tf = TaskForce(f"{'AID' if is_allied_aid else 'DEF'}-{self.ai.tf_counter}", faction)
        def_tf.target = target
        def_tf.rally_point = def_tf.target
        def_tf.mission_role = "DEFENSE"
        
        # Set TF as an escort if it's for a construction site
        if target in construction_targets:
            def_tf.id = f"ESC-{self.ai.tf_counter}"
            def_tf.mission_role = "CONSTRUCTION" # Correct role for lifecycle management
            loc_name = target.name if not hasattr(target, 'system') else f"{target.system.name} ({target.name})"
            print(f"  > [STRATEGY] {faction} forming ESCORT for Starbase construction at {loc_name}")

        # Feature 110: Assign Combat Doctrine
        def_tf.faction_combat_doctrine = personality.combat_doctrine
        def_tf.doctrine_intensity = personality.doctrine_intensity
        
        # [QUIRK] Retreat Threshold & Upkeep
        threshold = personality.retreat_threshold
        if "honor_bound" in personality.quirks:
            threshold = 0.05
        def_tf.retreat_threshold = threshold
        
        recruitment_mult = personality.quirks.get("navy_recruitment_mult", 1.0)
        
        # Assign defenders
        max_defenders = int((10 * personality.cohesiveness * recruitment_mult) + 2)
        if target in construction_targets:
            # Escorts don't need the whole fleet usually, but at least 2
            max_defenders = max(2, int(max_defenders * 0.4))
        elif is_allied_aid:
            # Don't send EVERYTHING to help an ally unless we are rich
            max_defenders = max(1, int(max_defenders * 0.3))

        econ_state = econ_health['state']
        income = econ_health['income']
        current_upkeep = econ_health['upkeep']
        
        chosen_defenders = []
        for i in range(min(len(available_fleets), max_defenders)):
            f = available_fleets[i]
            if econ_state == "CRISIS" and len(chosen_defenders) >= 2:
                break
                
            if (current_upkeep + self.ai.calculate_fleet_upkeep(f)) > (income * 1.5):
                zone = zones.get(target.name, "CORE") if zones else "CORE"
                if zone != "CAPITAL" and target not in construction_targets:
                    break
            
            def_tf.add_fleet(f)
            chosen_defenders.append(f)
        
        if def_tf.fleets:
            self.ai.task_forces[faction].append(def_tf)
            if "ESC-" in def_tf.id:
                pass # Already printed
            elif is_allied_aid:
                print(f"  > [MUTUAL_DEFENSE] {faction} honoring alliance! Sending {def_tf.id} to help defend {target.name} (Owner: {target.owner})")
            else:
                print(f"  > [DEFENSE] {faction} ({personality.name}) forms DEF TASK FORCE {def_tf.id} -> Target: {def_tf.target.name}")
            return [f for f in available_fleets if f not in chosen_defenders]
        
        return available_fleets

    def handle_allied_defense(self, faction: str, available_fleets: List[Fleet], personality: Any) -> List[Any]:
        """Scans for allies needing assistance and returns threatened planet objects."""
        if not self.ai.engine.diplomacy: return []
        if len(available_fleets) < 4: return [] # Prioritize home defense if fleet is small
        
        allied_threats = []
        f_treaties = self.ai.engine.diplomacy.treaties.get(faction, {})
        
        for partner, state in f_treaties.items():
            if state != "Alliance": continue
            
            # Check partner's planets for combat or incoming threats
            partner_planets = self.ai.engine.planets_by_faction.get(partner, [])
            for p in partner_planets:
                # Is p threatened?
                # 1. Direct combat?
                has_combat = any(ag.faction != partner for ag in p.armies if not ag.is_destroyed)
                
                # 2. Predicted incoming?
                incoming = False
                if hasattr(self.ai, 'predict_enemy_threats'):
                     p_threats = self.ai.predict_enemy_threats(partner)
                     for th in p_threats:
                          if th['target'] == p:
                               incoming = True; break
                
                if has_combat or incoming:
                    # Check if ANY allied fleet (ours or partner's) is already there defending
                    defense_power_present = sum(f.power for f in self.ai.engine.fleets if f.location == p and (f.faction == faction or f.faction == partner))
                    
                    if defense_power_present < 2000: # Threshold for needing help
                         allied_threats.append(p)
                         if len(allied_threats) >= 2: break # Don't spread too thin
                         
        return allied_threats

import os
import json
from src.mechanics.resource_mechanics import ConvictionMechanic, BiomassMechanic, IndustrialMightMechanic
from src.mechanics.combat_mechanics import ReanimationProtocolsMechanic, AetherOverloadMechanic, InstabilityMechanic, EternalMechanic, FurorMechanic
from src.mechanics.economy_mechanics import RaidMechanic, SalvageMechanic, PlasmaOverchargeMechanic

class MechanicsLoader:
    def __init__(self, universe_name="void_reckoning"):
        self.universe_name = universe_name
        self.registry_path = os.path.join("universes", universe_name, "factions", "mechanics_registry.json")
        
    def load_registry(self):
        if not os.path.exists(self.registry_path):
            print(f"Warning: No mechanics registry found at {self.registry_path}")
            return {}
            
        with open(self.registry_path, 'r') as f:
            return json.load(f)
            
    def instantiate_mechanics(self, registry):
        mechanics_map = {} # {faction_name: [Mechanic objects]}
        
        # Format: {"mechanics": [list of defs], "assignments": {faction: [mech_ids]}}
        mech_defs = {m["id"]: m for m in registry.get("mechanics", [])}
        assignments = registry.get("assignments", {})
        
        for faction, mech_ids in assignments.items():
            if faction not in mechanics_map:
                mechanics_map[faction] = []
            
            for m_id in mech_ids:
                data = mech_defs.get(m_id)
                if not data: continue
                
                cls = self._get_class_for_id(m_id)
                if cls:
                    obj = cls(m_id, data)
                    mechanics_map[faction].append(obj)
                
        return mechanics_map

    def _get_class_for_id(self, mech_id):
        # Mapping
        # We could use `type` field if it exists, or ID string match
        if "Mech_Crusade" in mech_id: return ConvictionMechanic
        if "Mech_Biomass" in mech_id: return BiomassMechanic
        if "Mech_Industrial" in mech_id: return IndustrialMightMechanic
        if "Mech_Logic_Core" in mech_id: return ReanimationProtocolsMechanic
        if "Mech_Aether" in mech_id: return AetherOverloadMechanic
        if "Mech_Instability" in mech_id: return InstabilityMechanic
        if "Mech_Eternal" in mech_id: return EternalMechanic
        if "Mech_Furor" in mech_id: return FurorMechanic
        if "Mech_Raid" in mech_id: return RaidMechanic
        if "Mech_Salvage" in mech_id: return SalvageMechanic
        if "Mech_Plasma" in mech_id: return PlasmaOverchargeMechanic
        return None

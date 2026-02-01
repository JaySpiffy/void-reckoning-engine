from abc import ABC, abstractmethod

class BaseMechanic(ABC):
    def __init__(self, mechanic_id, data):
        self.mechanic_id = mechanic_id
        self.name = data.get("name", "Unknown Mechanic")
        self.description = data.get("description", "")
        self.modifiers = data.get("modifiers", {})
        self.config = data  # store full config

    def get_modifier(self, key, default=0.0):
        return self.modifiers.get(key, default)

    # Hooks - Default no-op implementation
    def on_turn_start(self, context):
        pass

    def on_turn_end(self, context):
        pass

    def on_economy_phase(self, context):
        pass

    def on_unit_recruited(self, context):
        pass

    def on_unit_death(self, context):
        pass

    def on_battle_end(self, context):
        pass

    def on_building_constructed(self, context):
        pass
        
    def on_ability_use(self, context):
        pass

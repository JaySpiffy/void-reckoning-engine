
import os
import sys
# Add current directory to path
sys.path.append(os.getcwd())

from src.managers.campaign_manager import CampaignEngine
from src.combat.combat_simulator import parse_unit_file

engine = CampaignEngine()
print(f"Total Unit Blueprints: {sum(len(v) for v in engine.unit_blueprints.values())}")
print(f"Total Navy Blueprints: {sum(len(v) for v in engine.navy_blueprints.values())}")

for faction in engine.navy_blueprints:
    print(f"Faction: {faction} - Navy Count: {len(engine.navy_blueprints[faction])}")
    if faction == "Imperium":
        for ship in engine.navy_blueprints[faction]:
            print(f"  > Ship: {ship.name}")

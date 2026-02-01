import pytest
from unittest.mock import MagicMock, PropertyMock, patch
from src.managers.ai_manager import StrategicAI
from universes.base.personality_template import FactionPersonality
from src.models.unit import Unit, Component
from src.managers.battle_manager import BattleManager, ActiveBattle
from src.combat.tactical_engine import calculate_movement_vector, TacticalGrid

@pytest.fixture
def ai_manager(eternal_crusade_universe):
    engine = MagicMock()
    engine.turn_counter = 50
    engine.factions = {}
    engine.all_planets = []
    engine.telemetry = MagicMock()

    def get_faction_side_effect(name):
        return engine.factions.get(name)
    engine.get_faction.side_effect = get_faction_side_effect
    
    engine.ai_manager = MagicMock()
    
    return StrategicAI(engine)

def test_rift_daemon_aggression(ai_manager):
    """
    Test that Rift Daemons (High Aggression > 1.5) ignore retreat thresholds ("Waaagh" equivalent).
    """
    p = FactionPersonality(name="Rift_Daemons", aggression=2.0, retreat_threshold=0.0)
    
    fleet = MagicMock()
    fleet.faction = "Rift_Daemons"
    fleet.units = [MagicMock(ship_class="Frigate", is_alive=MagicMock(return_value=True))]
    
    location = MagicMock(name="Battlefield")
    f_mgr = MagicMock(home_planet_name="Rift Core", learned_personality=p)
    
    ai_manager.engine.factions["Rift_Daemons"] = f_mgr
    ai_manager.assess_economic_health = MagicMock(return_value={"state": "HEALTHY"})
    
    threshold = ai_manager.calculate_dynamic_retreat_threshold(fleet, location, p, None)
    
    # Aggression > 1.5 overrides base calculation to 0.05
    assert threshold == 0.05

def test_hive_swarm_hunger(ai_manager):
    """
    Test that Hive Swarm (Biomass Hunger) values high-income planets significantly more.
    """
    planet = MagicMock()
    planet.name = "Prey World"
    planet.income_req = 1000
    planet.income_prom = 100
    planet.owner = "Zealot_Legions"
    planet.provinces = [] 
    planet.system = MagicMock()
    planet.system.x, planet.system.y = 0, 0
    planet.system.connections = [] 
    
    ai_manager.engine.all_planets = [planet]
    ai_manager.engine.get_planet.return_value = planet
    
    # Hive Swarm (Hungry)
    hive_mgr = MagicMock(intelligence_memory={})
    p_hive = MagicMock(spec=FactionPersonality)
    p_hive.biomass_hunger = 2.0
    p_hive.expansion_bias = 1.5
    p_hive.threat_affinity = 0.0
    hive_mgr.learned_personality = p_hive
    ai_manager.engine.factions["Hive_Swarm"] = hive_mgr
    
    # Zealots (Not Hungry)
    zealot_mgr = MagicMock(intelligence_memory={})
    p_zealot = MagicMock(spec=FactionPersonality)
    p_zealot.biomass_hunger = 0.0
    p_zealot.expansion_bias = 1.0
    p_zealot.threat_affinity = 0.0
    zealot_mgr.learned_personality = p_zealot
    ai_manager.engine.factions["Zealot_Legions"] = zealot_mgr
    
    ai_manager.get_cached_theater_power = MagicMock(return_value={})
    
    hive_score = ai_manager.calculate_expansion_target_score(
        "Prey World", "Hive_Swarm", 10, 10, "Hive_Swarm", "HEALTHY", 50
    )
    
    zealot_score = ai_manager.calculate_expansion_target_score(
        "Prey World", "Zealot_Legions", 10, 10, "Zealot_Legions", "HEALTHY", 50
    )
    
    assert hive_score > zealot_score * 1.5


def test_regeneration_trait():
    """Test generic regeneration trait (used by Cyber Synod / Iron Vanguard elites)."""
    # Using generic unit with trait
    unit = Unit("Cyber Construct", faction="Cyber_Synod", traits=["Regeneration"], hp=100, armor=30, damage=10, ma=30, md=30, regen=10)
    unit.current_hp = 50
    # The stats component will have calculated regen_hp_per_turn if it was in traits, 
    # but here we just want to ensure it works.
    
    # Unit init applies 'Regeneration' trait logic which sets regen
    # Let's verify init logic worked:
    assert unit.regen_hp_per_turn >= 10
    
    unit.invalidate_strength_cache = MagicMock()
    
    active, amount = unit.regenerate_infantry() 
    
    assert active is True
    assert amount >= 10
    assert unit.current_hp == 60

def test_scavenger_loot_quirk():
    """Test Scavenger Clans gain requisition from casualties."""
    bm = BattleManager()
    bm.context = MagicMock()
    bm.context.factions = {}
    
    scav_mgr = MagicMock(requisition=100, casualty_plunder_ratio=0.8)
    bm.context.factions["Scavenger_Clans"] = scav_mgr
    
    bm.context.get_faction.side_effect = lambda name: bm.context.factions.get(name)

    battle = MagicMock()
    battle.initial_power = {"Zealot_Legions": 1000, "Scavenger_Clans": 500}
    battle.participating_fleets = ["SF1", "ZF1"]
    battle.start_time = 0.0
    battle.end_time = 1.0
    
    u_dead = MagicMock(cost=500, is_alive=MagicMock(return_value=False), xp=0)
    u_alive = MagicMock(cost=500, is_alive=MagicMock(return_value=True), xp=0)
    
    battle.state.armies_dict = {"Zealot_Legions": [u_dead], "Scavenger_Clans": [u_alive]}
    
    planet = MagicMock(name="Scrap World")
    
    bm._finalize_battle(battle, planet, "Scavenger_Clans", 10)
    
    # Gain: 500 (Dead Cost) * 0.8 (Ratio) = 400. Total 500.
    assert scav_mgr.requisition == 500

def test_ranged_preference_quirk():
    """Test generic ranged preference trait (e.g. Solar Hegemony Snipers)."""
    grid = MagicMock(spec=TacticalGrid)
    grid.get_distance.return_value = 10 
    
    unit = Unit("Sniper", faction="Aurelian_Hegemony", hp=30, armor=30, damage=10, ma=10, md=10)
    unit.ranged_preference = True
    unit.grid_x, unit.grid_y = 50, 50
    
    target = MagicMock()
    target.grid_x, target.grid_y = 51, 50
    
    w = MagicMock(spec=Component)
    w.type = "Weapon"
    w.weapon_stats = {"Range": 50}
    w.is_destroyed = False
    unit.components = [w]
    
    dx, dy = calculate_movement_vector(unit, target, "CHARGE", grid)
    assert dx == -1 # Kites despite Charge order due to quirk

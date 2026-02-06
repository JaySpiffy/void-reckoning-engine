import pytest
from unittest.mock import MagicMock, patch, call
from src.managers.battle_manager import BattleManager

@pytest.fixture
def mock_context():
    ctx = MagicMock()
    ctx.turn_counter = 1
    ctx.fleets = []
    ctx.get_all_fleets.return_value = []
    ctx.get_all_planets.return_value = []
    
    # Mock faction for evasion rating checks
    mock_faction = MagicMock()
    mock_faction.evasion_rating = 0
    ctx.get_faction.return_value = mock_faction
    
    # Mock mechanics engine
    ctx.mechanics_engine = MagicMock()
    
    # Mock telemetry
    ctx.telemetry = MagicMock()
    
    # Mock logger
    ctx.logger = MagicMock()
    ctx.logger.combat = MagicMock()
    
    # Mock game_config
    ctx.game_config = {"combat": {"real_time_headless": False}}
    
    return ctx

@pytest.fixture
def battle_manager(mock_context):
    with patch("src.managers.battle_manager.InvasionManager") as MockIM:
        with patch("src.managers.battle_manager.RetreatHandler") as MockRH:
             bm = BattleManager(context=mock_context)
             bm.invasion_manager = MockIM.return_value
             bm.retreat_handler = MockRH.return_value
             return bm

@pytest.fixture
def mock_fleet_pair():
    # Fleet 1: Imperium
    f1 = MagicMock()
    f1.id = "f1"
    f1.faction = "Imperium"
    f1.is_destroyed = False
    f1.is_engaged = False
    f1.destination = None
    f1.power = 100
    f1.units = [MagicMock(is_ship=lambda: True, _fleet_id=None)]
    f1.units[0].is_alive.return_value = True
    f1.units[0].cost = 50
    f1.units[0].grid_size = [1, 1]
    f1.units[0].grid_x = 0
    f1.units[0].grid_y = 0
    f1.units[0].home_defense_morale_bonus = 0
    f1.units[0].home_defense_toughness_bonus = 0
    f1.units[0].current_morale = 50
    f1.units[0].toughness = 10
    f1.units[0].armor = 10

    # Fleet 2: Orks
    f2 = MagicMock()
    f2.id = "f2"
    f2.faction = "Orks"
    f2.is_destroyed = False
    f2.is_engaged = False
    f2.destination = None
    f2.power = 100
    f2.units = [MagicMock(is_ship=lambda: True, _fleet_id=None)]
    f2.units[0].is_alive.return_value = True
    f2.units[0].cost = 50
    f2.units[0].grid_size = [1, 1]
    f2.units[0].grid_x = 0
    f2.units[0].grid_y = 0
    f2.units[0].home_defense_morale_bonus = 0
    f2.units[0].home_defense_toughness_bonus = 0
    f2.units[0].current_morale = 50
    f2.units[0].toughness = 10
    f2.units[0].armor = 10
    
    return f1, f2

def test_resolve_battles_at_creates_new_battle(battle_manager, mock_context, mock_fleet_pair):
    """Test that a new battle is initialized when two hostile fleets meet."""
    f1, f2 = mock_fleet_pair
    location = MagicMock()
    location.name = "TestSystem"
    location.owner = "Neutral"  # No owner means conflict
    
    # Setup Fleets at location
    f1.location = location
    f2.location = location
    
    # Mock interactions - patch the factory module instead of the facade
    with patch("src.combat.management.resolution_factory.initialize_battle_state") as mock_init_state:
        mock_state = MagicMock()
        mock_state.armies_dict = {"Imperium": f1.units, "Orks": f2.units}
        mock_state.round_num = 1
        mock_state.faction_doctrines = {}
        mock_state.faction_metadata = {}
        mock_state.grid = MagicMock()
        mock_state.grid.place_unit_near_edge = MagicMock(return_value=True)
        mock_state.grid.place_unit_randomly = MagicMock()
        mock_init_state.return_value = mock_state
        
        # Mock strategic AI for doctrine fetching
        mock_context.strategic_ai = MagicMock()
        mock_task_force = MagicMock()
        mock_task_force.combat_doctrine = "CHARGE"
        mock_task_force.faction_combat_doctrine = "STANDARD"
        mock_task_force.doctrine_intensity = 1.0
        mock_context.strategic_ai.get_task_force_for_fleet.return_value = mock_task_force
        
        # Set up fleets to always return same fleets
        mock_context.get_all_fleets.return_value = [f1, f2]
        
        # Run
        battle_manager.resolve_battles_at(location)
        
        # Verify
        assert location in battle_manager.active_battles
        assert f1.is_engaged
        assert f2.is_engaged
        
        # Verify telemetry log
        mock_context.telemetry.log_event.assert_called()

def test_resolve_battles_at_joins_existing_battle(battle_manager, mock_context, mock_fleet_pair):
    """Test that fleets join an existing battle."""
    f1, f2 = mock_fleet_pair
    location = MagicMock()
    location.name = "TestSystem"
    location.owner = "Neutral"
    
    # Pre-seed battle - use real ActiveBattle with mocked state
    from src.managers.combat.active_battle import ActiveBattle
    mock_state = MagicMock()
    mock_state.armies_dict = {"Imperium": f1.units}
    mock_state.faction_doctrines = {}
    mock_state.faction_metadata = {}
    mock_state.grid = MagicMock()
    mock_state.grid.place_unit_near_edge = MagicMock(return_value=True)
    mock_state.grid.place_unit_randomly = MagicMock()
    mock_state.add_faction_units = MagicMock()
    
    # Mock strategic AI
    mock_context.strategic_ai = MagicMock()
    mock_task_force = MagicMock()
    mock_task_force.combat_doctrine = "CHARGE"
    mock_task_force.faction_combat_doctrine = "STANDARD"
    mock_task_force.doctrine_intensity = 1.0
    mock_context.strategic_ai.get_task_force_for_fleet.return_value = mock_task_force
    
    existing_battle = ActiveBattle(location, mock_state, 1, context=mock_context)
    existing_battle.participating_fleets = {f1.id}
    battle_manager.active_battles[location] = existing_battle
    
    # Fleet 2 arrives
    f1.location = location
    f2.location = location
    # f1 is already IN the battle (id in participating_fleets)
    # f2 is NEW
    
    # Set up fleets to always return same fleets
    mock_context.get_all_fleets.return_value = [f1, f2]
    
    # Run
    battle_manager.resolve_battles_at(location)
    
    # Verify
    # existing_battle.add_fleet should be called with f2
    assert f2.id in existing_battle.participating_fleets
    assert f2.is_engaged

def test_process_active_battles_execution(battle_manager, mock_context):
    """Test that active battles are ticked and finalized when done."""
    location = MagicMock()
    location.name = "TestSystem"
    battle = MagicMock()
    battle.state.round_num = 1
    battle.participating_fleets = set() # Avoid cleanup crash
    battle.state.armies_dict = {"Imperium": [MagicMock()], "Orks": [MagicMock()]}
    battle.is_finished = False
    battle.battle_id = "test_battle_1"
    battle.start_time = 1000.0
    battle.pre_battle_counts = {"Imperium": 1, "Orks": 1}
    
    # Add attributes to mock units to avoid errors
    for faction, units in battle.state.armies_dict.items():
        for unit in units:
            unit.grid_size = [1, 1]
            unit.grid_x = 0
            unit.grid_y = 0
            unit.is_alive.return_value = True
            unit.current_suppression = 0
            unit.xp = 0
            unit.cost = 50
            unit.tier = 1
            unit.domain = "space"
            unit.unit_type = "infantry"
            unit.ship_class = "Escort"
    
    battle.state.battle_stats = {"Imperium": {}, "Orks": {}}
    battle.state.tracker = MagicMock()
    
    battle_manager.active_battles[location] = battle
    
    # Mock execute_battle_round to finish immediately
    # Returns: winner, survivors, is_finished
    with patch("src.managers.battle_manager.execute_battle_round", return_value=("Imperium", 50, True)):
        with patch.object(battle_manager, "_finalize_battle") as mock_finalize:
            # Run
            battle_manager.process_active_battles()
            
            # Verify
            assert battle.is_finished
            assert location not in battle_manager.active_battles
            mock_finalize.assert_called_once()


def test_finalize_battle_rewards(battle_manager, mock_context):
    """Test that finalization awards intel and xp."""
    location = MagicMock()
    location.name = "TestSystem"
    battle = MagicMock()
    battle.state.battle_stats = {
        "Imperium": {"enemy_tech_encountered": {"laser"}, "enemy_units_analyzed": ["ork_ship"]}
    }
    battle.state.armies_dict = {"Imperium": [MagicMock(is_alive=lambda: True, gain_xp=MagicMock(), xp=0, grid_size=[1,1], cost=50, tier=1, domain="space", unit_type="infantry", ship_class="Escort")]}
    battle.state.round_num = 1
    battle.state.tracker = MagicMock()
    battle.pre_battle_counts = {"Imperium": 1}
    battle.participating_fleets = set()
    battle.battle_id = "test_battle"
    battle.start_time = 1000.0
    battle.state.battle_stats = {"Imperium": {"enemy_tech_encountered": {"laser"}, "enemy_units_analyzed": ["ork_ship"]}}
    
    # Setup Faction for Intel reward
    f_imperium = MagicMock()
    mock_context.get_faction.return_value = f_imperium
    
    # Run
    battle_manager._finalize_battle(battle, location, "Imperium", 100)
    
    # Verify XP
    unit = battle.state.armies_dict["Imperium"][0]
    unit.gain_xp.assert_called()
    
    # Verify Intel
    # Tech count 1 * 100 + Unit count 1 * 10 = 110
    f_imperium.earn_intel.assert_called_with(110, source="combat")

pub mod mechanics;
pub mod targeting;
pub mod engine;
use std::collections::HashMap;

/// Enumeration of Weapon Types for damage calculation context
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum WeaponType {
    Kinetic,
    Energy,
    Missile,
    Beam,
    Fighter,
}

/// A lightweight representation of a weapon system on a unit.
#[derive(Debug, Clone)]
pub struct Weapon {
    pub name: String,
    pub weapon_type: WeaponType,
    pub range: f32,
    pub damage: f32,
    pub accuracy: f32,
    pub cooldown: f32,
    pub current_cooldown: f32,
}

/// A flattened, memory-efficient representation of a combat unit.
#[derive(Debug, Clone)]
pub struct CombatUnit {
    pub id: u32,
    pub name: String,
    pub faction_idx: u8, // 0-255 index into faction list
    
    // Core Vitals
    pub hp: f32,
    pub max_hp: f32,
    pub shields: f32,
    pub max_shields: f32,
    pub armor: f32,
    pub integrity: f32, // Structural integrity (0.0 - 1.0)
    
    // Capabilities
    pub weapons: Vec<Weapon>,
    pub speed: f32,
    pub evasion: f32,
    
    // State
    pub position: (f32, f32), // Grid coordinates
    pub velocity: (f32, f32), // Movement vector
    pub target_id: Option<u32>, // Current target
    pub is_alive: bool,
}

impl CombatUnit {
    pub fn new(id: u32, name: String, faction_idx: u8, max_hp: f32) -> Self {
        Self {
            id,
            name,
            faction_idx,
            hp: max_hp,
            max_hp,
            shields: 0.0,
            max_shields: 0.0,
            armor: 0.0,
            integrity: 1.0,
            weapons: Vec::new(),
            speed: 0.0,
            evasion: 0.0,
            position: (0.0, 0.0),
            velocity: (0.0, 0.0),
            target_id: None,
            is_alive: true,
        }
    }
    
    pub fn is_alive(&self) -> bool {
        self.hp > 0.0
    }
}

/// The main container for a battle simulation state.
pub struct BattleState {
    pub units: Vec<CombatUnit>,
    pub grid_size: (f32, f32),
    pub turn: u32,
    pub time_elapsed: f32,
}

impl BattleState {
    pub fn new(width: f32, height: f32) -> Self {
        Self {
            units: Vec::new(),
            grid_size: (width, height),
            turn: 0,
            time_elapsed: 0.0,
        }
    }
    
    pub fn add_unit(&mut self, unit: CombatUnit) {
        self.units.push(unit);
    }
    
    pub fn get_unit(&self, id: u32) -> Option<&CombatUnit> {
        self.units.iter().find(|u| u.id == id)
    }
    
    pub fn get_unit_mut(&mut self, id: u32) -> Option<&mut CombatUnit> {
        self.units.iter_mut().find(|u| u.id == id)
    }
}

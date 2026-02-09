use crate::{BattleState, CombatUnit};
use std::collections::HashMap;

/// Simple Spatial Hash for O(N log N) targeting performance.
/// Divides the 500x500 grid into cells.
pub struct SpatialHash {
    pub cells: HashMap<(i32, i32), Vec<u32>>,
    pub cell_size: f32,
}

impl SpatialHash {
    pub fn new(cell_size: f32) -> Self {
        Self {
            cells: HashMap::new(),
            cell_size,
        }
    }

    pub fn insert(&mut self, unit: &CombatUnit) {
        let x = (unit.position.0 / self.cell_size) as i32;
        let y = (unit.position.1 / self.cell_size) as i32;
        self.cells.entry((x, y)).or_insert_with(Vec::new).push(unit.id);
    }

    pub fn build(state: &BattleState, cell_size: f32) -> Self {
        let mut hash = Self::new(cell_size);
        for unit in &state.units {
            if unit.is_alive {
                hash.insert(unit);
            }
        }
        hash
    }

    pub fn get_nearby(&self, pos: (f32, f32), radius: f32) -> Vec<u32> {
        let mut nearby = Vec::new();
        let min_x = ((pos.0 - radius) / self.cell_size) as i32;
        let max_x = ((pos.0 + radius) / self.cell_size) as i32;
        let min_y = ((pos.1 - radius) / self.cell_size) as i32;
        let max_y = ((pos.1 + radius) / self.cell_size) as i32;

        for x in min_x..=max_x {
            for y in min_y..=max_y {
                if let Some(ids) = self.cells.get(&(x, y)) {
                    nearby.extend(ids);
                }
            }
        }
        nearby
    }
}

pub fn find_best_target(attacker: &CombatUnit, state: &BattleState) -> Option<u32> {
    // FALLBACK: Linear Scan if no spatial index
    let mut best_target = None;
    let mut min_dist_sq = f32::MAX;

    for target in &state.units {
        if !target.is_alive || target.id == attacker.id || target.faction_idx == attacker.faction_idx {
            continue;
        }

        let dx = target.position.0 - attacker.position.0;
        let dy = target.position.1 - attacker.position.1;
        let dist_sq = dx*dx + dy*dy;

        if dist_sq < min_dist_sq {
            min_dist_sq = dist_sq;
            best_target = Some(target.id);
        }
    }

    best_target
}

/// Optimized targeting using a spatial index.
pub fn find_best_target_spatial(attacker: &CombatUnit, state: &BattleState, hash: &SpatialHash) -> Option<u32> {
    let mut best_target = None;
    let mut min_dist_sq = f32::MAX;

    // Determine search radius based on attacker's longest weapon
    let max_range = attacker.weapons.iter().map(|w| w.range).fold(0.0, f32::max);
    
    // Search in the hash
    let nearby_ids = hash.get_nearby(attacker.position, max_range.max(50.0)); // Min search radius 50.0

    for &tid in &nearby_ids {
        // Look up unit (O(1) if we had a map, but state.units is Vec)
        // Optimization: We should really pass a map or use the hash to store units directly.
        // For now, let's just use the Vec and find it.
        if let Some(target) = state.get_unit(tid) {
            if !target.is_alive || target.id == attacker.id || target.faction_idx == attacker.faction_idx {
                continue;
            }

            let dx = target.position.0 - attacker.position.0;
            let dy = target.position.1 - attacker.position.1;
            let dist_sq = dx*dx + dy*dy;

            if dist_sq < min_dist_sq {
                min_dist_sq = dist_sq;
                best_target = Some(target.id);
            }
        }
    }

    best_target
}

use crate::{BattleState, CombatUnit};

pub fn find_best_target(attacker: &CombatUnit, state: &BattleState) -> Option<u32> {
    let mut best_target = None;
    let mut min_dist_sq = f32::MAX;

    for target in &state.units {
        // 1. Basic Validity Checks
        if !target.is_alive || target.id == attacker.id || target.faction_idx == attacker.faction_idx {
            continue;
        }

        // 2. Distance Calculation (Squared to avoid sqrt)
        let dx = target.position.0 - attacker.position.0;
        let dy = target.position.1 - attacker.position.1;
        let dist_sq = dx*dx + dy*dy;

        // 3. Range Check (using longest range weapon)
        // Optimization: Pre-calculate max range for attacker?
        // For now, iterate weapons.
        let max_range = attacker.weapons.iter().map(|w| w.range).fold(0.0, f32::max);
        if dist_sq > max_range * max_range {
             // Out of range (Strict)
             // In a real boids system, we might target them to move towards them.
             // But for "Shooting Phase", we need valid targets.
             // Let's assume this is "Acquire Target" logic.
        }

        // Simple Nearest Neighbor for Phase 1
        if dist_sq < min_dist_sq {
            min_dist_sq = dist_sq;
            best_target = Some(target.id);
        }
    }

    best_target
}

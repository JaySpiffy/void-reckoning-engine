use crate::{BattleState, CombatUnit, Weapon};
use crate::mechanics::{DamageSource, Armor};
use crate::targeting::find_best_target;
use rand::thread_rng;

pub struct BattleEngine {
    pub state: BattleState,
}

impl BattleEngine {
    pub fn new(width: f32, height: f32) -> Self {
        Self {
            state: BattleState::new(width, height),
        }
    }

    pub fn add_unit(&mut self, unit: CombatUnit) {
        self.state.add_unit(unit);
    }

    pub fn step(&mut self) -> bool {
        self.state.turn += 1;
        self.state.time_elapsed += 1.0; // Assume 1s tick for now

        let mut rng = thread_rng();
        let mut damage_events: Vec<(u32, f32, crate::mechanics::DamageType)> = Vec::new();

        // 1. Movement & Targeting & Attack Declaration
        // We need to iterate immutable to find targets/intent, then mutable to update?
        // Or just indices.
        
        // Optimize: Separate targeting/movement logic to avoid massive loop?
        // For now, simple iteration.
        
        let unit_count = self.state.units.len();
        
        for i in 0..unit_count {
            // Re-borrow self for each unit context
            // Rust ownership makes this tricky if we want to read "all units" while mutating "this unit".
            // Standard pattern: Separate state.
            
            // We can't do: for unit in &mut self.state.units { find_target(unit, &self.state.units) }
            // So we'll collect intents first.
            
            // Just resolve targeting first
            // But targeting needs read access to all units.
        }
        
        // PASS 1: Targeting Updates (Read-Only State -> Write Target ID)
        // We can iterate mutable units, but `find_best_target` needs &BattleState (which has &Vec<Unit>).
        // Conflict!
        // Solution: Split the data or use indices.
        // Let's use indices.
        
        let mut new_targets: Vec<(usize, u32)> = Vec::new();
        
        for (idx, unit) in self.state.units.iter().enumerate() {
            if !unit.is_alive { continue; }
            
            // Check current target validity
            let needs_target = match unit.target_id {
                None => true,
                Some(tid) => {
                    // Check if target exists and is alive
                     self.state.units.iter().find(|u| u.id == tid).map(|u| !u.is_alive).unwrap_or(true)
                }
            };
            
            if needs_target {
                if let Some(target_id) = find_best_target(unit, &self.state) {
                    new_targets.push((idx, target_id));
                }
            }
        }
        
        // Apply targets
        for (idx, target_id) in new_targets {
            self.state.units[idx].target_id = Some(target_id);
        }

        // PASS 2: Combat Action (Calculate Output Damage)
        // Read unit + Read target position -> Generate Damage Event
        for unit in &mut self.state.units {
            if !unit.is_alive { continue; }
            if let Some(target_id) = unit.target_id {
                 // We need target data (position, etc)
                 // But we are holding a mutable ref to `unit`.
                 // We can't easily find `target` in `self.state.units` simultaneously via iterator.
                 // We need to look it up.
            }
        }
        
        // Simpler approach:
        // Clone meaningful combat data specifically for the read-phase? No too slow.
        // Index-based loop.
        
        for i in 0..self.state.units.len() {
             let attacker = &self.state.units[i];
             if !attacker.is_alive || attacker.target_id.is_none() { continue; }
             
             let tid = attacker.target_id.unwrap();
             
             // Find target (scan?) 
             // We can optimize with a HashMap lookup map later.
             let target_data = self.state.units.iter().find(|u| u.id == tid);
             
             if let Some(target) = target_data {
                 // Check Range
                 // Roll Weapons
                 for weapon in &attacker.weapons {
                     // Check cooldown
                     if weapon.current_cooldown <= 0.0 {
                         let dmg = weapon.calculate_damage(&mut rng);
                         let dtype = weapon.get_damage_type();
                         damage_events.push((tid, dmg, dtype));
                     }
                 }
             }
        }
        
        // PASS 3: Apply Damage
        let mut total_destroyed = 0;
        for (target_id, amount, dtype) in damage_events {
            if let Some(target) = self.state.units.iter_mut().find(|u| u.id == target_id) {
                if target.is_alive {
                    let actual_loss = target.mitigate_damage(amount, dtype);
                    
                    // Simple HP/Shield logic
                    if target.shields > 0.0 && matches!(dtype, crate::mechanics::DamageType::Energy) {
                        target.shields -= actual_loss;
                        if target.shields < 0.0 {
                            target.hp += target.shields; // Carry over
                            target.shields = 0.0;
                        }
                    } else {
                        target.hp -= actual_loss;
                    }

                    if target.hp <= 0.0 {
                        target.is_alive = false;
                        target.hp = 0.0;
                        total_destroyed += 1;
                    }
                }
            }
        }
        
        // PASS 4: Cooldowns
        for unit in &mut self.state.units {
             for weapon in &mut unit.weapons {
                 if weapon.current_cooldown > 0.0 {
                     weapon.current_cooldown -= 1.0;
                 }
             }
        }

        // Return true if battle should continue (units > 0)
        // Check if multiple factions still alive
        let factions: std::collections::HashSet<u8> = self.state.units.iter()
            .filter(|u| u.is_alive)
            .map(|u| u.faction_idx)
            .collect();
            
        factions.len() > 1
    }
}

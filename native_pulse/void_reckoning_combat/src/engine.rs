use crate::{BattleState, CombatUnit, Weapon};
use crate::mechanics::{DamageSource, Armor};
use crate::targeting::find_best_target;
use rand::thread_rng;

use void_reckoning_shared::{Event, EventLog, EventSeverity, CorrelationContext};
use std::sync::Arc;

pub struct BattleEngine {
    pub state: BattleState,
    pub event_log: Option<EventLog>,
    pub current_context: CorrelationContext,
}

impl BattleEngine {
    pub fn new(width: f32, height: f32) -> Self {
        Self {
            state: BattleState::new(width, height),
            event_log: None,
            current_context: CorrelationContext::new(),
        }
    }
    
    pub fn set_event_log(&mut self, log: EventLog) {
        self.event_log = Some(log);
    }

    pub fn set_correlation_context(&mut self, context: CorrelationContext) {
        self.current_context = context;
        // Also update the run_id in state for legacy compatibility if needed
        self.state.run_id = self.current_context.trace_id.clone();
    }

    pub fn add_unit(&mut self, unit: CombatUnit) {
        self.state.add_unit(unit);
    }
    
    pub fn set_unit_cover(&mut self, unit_id: u32, cover_val: u8) {
        if let Some(unit) = self.state.get_unit_mut(unit_id) {
            unit.cover = match cover_val {
                1 => crate::CoverType::Light,
                2 => crate::CoverType::Heavy,
                3 => crate::CoverType::Fortified,
                _ => crate::CoverType::None,
            };
        }
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
        
        // PASS 0: Movement
        let mut moves: Vec<(usize, (f32, f32))> = Vec::new();
        
        // Snapshot positions for safe lookup
        let unit_positions: std::collections::HashMap<u32, (f32, f32)> = self.state.units.iter()
            .map(|u| (u.id, u.position))
            .collect();

        for (idx, unit) in self.state.units.iter().enumerate() {
            if !unit.is_alive { continue; }
            if unit.speed <= 0.0 { continue; }

            if let Some(tid) = unit.target_id {
                if let Some(target_pos) = unit_positions.get(&tid) {
                    let dx = target_pos.0 - unit.position.0;
                    let dy = target_pos.1 - unit.position.1;
                    let dist = (dx * dx + dy * dy).sqrt();
                    
                    // Simple logic: Move to range 20.0
                    let desired_range = 20.0;
                    
                    if dist > desired_range {
                        let move_dist = unit.speed.min(dist - desired_range);
                        if move_dist > 0.0 {
                            let angle = dy.atan2(dx);
                            let new_x = unit.position.0 + move_dist * angle.cos();
                            let new_y = unit.position.1 + move_dist * angle.sin();
                            moves.push((idx, (new_x, new_y)));
                        }
                    }
                }
            }
        }
        
        for (idx, new_pos) in moves {
            self.state.units[idx].position = new_pos;
        }

        // PASS 1: Targeting Updates (Read-Only State -> Write Target ID)
        use crate::targeting::find_best_target;
        
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
        
        // PASS 2: Combat Action (Calculate Output Damage)
        let mut fired_weapons: Vec<(usize, usize)> = Vec::new(); // (unit_idx, weapon_idx)

        for i in 0..self.state.units.len() {
             let attacker = &self.state.units[i];
             if !attacker.is_alive || attacker.target_id.is_none() { continue; }
             
             let tid = attacker.target_id.unwrap();
             
             // Find target (scan?) 
             let target_data = self.state.units.iter().find(|u| u.id == tid);
             
             if let Some(target) = target_data {
                 // Check Range - Distance calculation needed here or assume cached?
                 // Recalculate distance for safety
                 let dx = target.position.0 - attacker.position.0;
                 let dy = target.position.1 - attacker.position.1;
                 let dist_sq = dx*dx + dy*dy;
                 let dist = dist_sq.sqrt();

                 for (w_idx, weapon) in attacker.weapons.iter().enumerate() {
                     // Check range
                     if dist > weapon.range { continue; }

                     // Check cooldown
                     if weapon.current_cooldown <= 0.0 {
                         let dmg = weapon.calculate_damage(&mut rng);
                         let dtype = weapon.get_damage_type();
                         damage_events.push((tid, dmg, dtype));
                         fired_weapons.push((i, w_idx));
                     }
                 }
             }
        }
        
        // Apply cooldown resets
        for (u_idx, w_idx) in fired_weapons {
            if let Some(unit) = self.state.units.get_mut(u_idx) {
                if let Some(weapon) = unit.weapons.get_mut(w_idx) {
                    weapon.current_cooldown = weapon.cooldown;
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
                        
                        if let Some(log) = &self.event_log {
                            let evt = Event::new(
                                EventSeverity::Info,
                                "Combat".to_string(),
                                format!("Unit {} destroyed by Unit {}", target_id, "Unknown"), // Context missing for attacker ID here
                                self.current_context.child(), // Use child context for causal tracing
                                None
                            );
                            log.add(evt);
                        }
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

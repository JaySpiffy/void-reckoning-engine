use serde::{Deserialize, Serialize};
use std::collections::HashMap;

pub const SCALE_FACTOR: i128 = 1_000_000;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default, PartialEq, Eq)]
pub struct ResourceState {
    pub credits: i128,
    pub minerals: i128,
    pub energy: i128,
    pub research: i128,
}

impl ResourceState {
    pub fn new(credits: f64, minerals: f64, energy: f64, research: f64) -> Self {
        Self {
            credits: (credits * SCALE_FACTOR as f64) as i128,
            minerals: (minerals * SCALE_FACTOR as f64) as i128,
            energy: (energy * SCALE_FACTOR as f64) as i128,
            research: (research * SCALE_FACTOR as f64) as i128,
        }
    }

    pub fn to_floats(&self) -> (f64, f64, f64, f64) {
        (
            self.credits as f64 / SCALE_FACTOR as f64,
            self.minerals as f64 / SCALE_FACTOR as f64,
            self.energy as f64 / SCALE_FACTOR as f64,
            self.research as f64 / SCALE_FACTOR as f64,
        )
    }

    pub fn add(&mut self, other: &ResourceState) {
        self.credits += other.credits;
        self.minerals += other.minerals;
        self.energy += other.energy;
        self.research += other.research;
    }

    pub fn subtract(&mut self, other: &ResourceState) {
        self.credits -= other.credits;
        self.minerals -= other.minerals;
        self.energy -= other.energy;
        self.research -= other.research;
    }

    pub fn multiply_fixed(&mut self, factor_scaled: i128) {
        // factor_scaled is assumed to be scaled by SCALE_FACTOR
        self.credits = (self.credits * factor_scaled) / SCALE_FACTOR;
        self.minerals = (self.minerals * factor_scaled) / SCALE_FACTOR;
        self.energy = (self.energy * factor_scaled) / SCALE_FACTOR;
        self.research = (self.research * factor_scaled) / SCALE_FACTOR;
    }
    
    pub fn multiply_int(&mut self, factor: i128) {
        self.credits *= factor;
        self.minerals *= factor;
        self.energy *= factor;
        self.research *= factor;
    }
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum NodeType {
    Planet,
    Fleet,
    Army,
    Station,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EconomicNode {
    pub id: String,
    pub owner_faction: String,
    pub node_type: NodeType,
    pub base_income: ResourceState,
    pub base_upkeep: ResourceState,
    pub efficiency_scaled: i128, // Scaled by SCALE_FACTOR
    pub modifiers: Vec<EconomicModifier>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalEconomicRules {
    pub orbit_discount_scaled: i128,      // 0.5 * SCALE_FACTOR
    pub garrison_discount_scaled: i128,   // 0.25 * SCALE_FACTOR
    pub navy_penalty_ratio: u32,          // e.g. 4 (fleets per planet)
    pub navy_penalty_rate_scaled: i128,   // e.g. 0.05 * SCALE_FACTOR
    pub vassal_tribute_rate_scaled: i128, // 0.2 * SCALE_FACTOR
    pub fleet_upkeep_scalar_scaled: i128, // e.g. 0.5 * SCALE_FACTOR
}

impl Default for GlobalEconomicRules {
    fn default() -> Self {
        Self {
            orbit_discount_scaled: 500_000,      // 50%
            garrison_discount_scaled: 250_000,   // 25%
            navy_penalty_ratio: 4,               // 4:1 fleets:planets
            navy_penalty_rate_scaled: 50_000,    // 5%
            vassal_tribute_rate_scaled: 200_000, // 20%
            fleet_upkeep_scalar_scaled: 1_000_000, // 100% (Default)
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EconomicModifier {
    pub name: String,
    pub multiplier_scaled: i128, // Scaled by SCALE_FACTOR
    pub flat_bonus: ResourceState,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EconomicReport {
    pub faction_name: String,
    pub total_income: ResourceState,
    pub total_upkeep: ResourceState,
    pub net_profit: ResourceState,
    pub income_by_category: HashMap<String, ResourceState>,
    pub is_insolvent: bool,
    pub active_nodes: usize,
}

use crate::types::{ResourceState, SCALE_FACTOR};
use void_reckoning_pathfinder::GraphTopology;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TradeRoute {
    pub from: String,
    pub to: String,
    pub base_value: ResourceState,
    pub efficiency_scaled: i128, // 1.0 = SCALE_FACTOR
}

pub struct TradeRouteManager {
    routes: Vec<TradeRoute>,
}

impl TradeRouteManager {
    pub fn new() -> Self {
        Self { routes: Vec::new() }
    }

    pub fn add_route(&mut self, route: TradeRoute) {
        self.routes.push(route);
    }

    pub fn calculate_efficiencies(&mut self, topology: &GraphTopology) {
        for route in &mut self.routes {
            if let Some((path, weight)) = topology.find_path(&route.from, &route.to, None) {
                // Heuristic: Weight of 1.0 is a standard jump.
                // If weight > 1.5 per jump, it suggests a warzone or hazards.
                let hop_count = path.len() as f32 - 1.0;
                let avg_weight = if hop_count > 0.0 { weight / hop_count } else { 1.0 };

                if avg_weight > 2.0 {
                    // Severed
                    route.efficiency_scaled = 0;
                } else if avg_weight > 1.0 {
                    // Throttled: 1.0 -> 2.0 maps to 1.0 -> 0.0 efficiency
                    let penalty = (avg_weight - 1.0).clamp(0.0, 1.0);
                    route.efficiency_scaled = ((1.0 - penalty) * SCALE_FACTOR as f32) as i128;
                } else {
                    route.efficiency_scaled = SCALE_FACTOR;
                }
            } else {
                // No path
                route.efficiency_scaled = 0;
            }
        }
    }

    pub fn get_total_trade_income(&self) -> HashMap<String, ResourceState> {
        let mut income = HashMap::new();
        for route in &self.routes {
            let mut route_gain = route.base_value;
            route_gain.multiply_fixed(route.efficiency_scaled);

            // Split 50/50 between both ends as simplification
            let mut half_gain = route_gain;
            half_gain.credits /= 2;
            half_gain.minerals /= 2;
            half_gain.energy /= 2;
            half_gain.research /= 2;

            income.entry(route.from.clone()).or_insert(ResourceState::default()).add(&half_gain);
            income.entry(route.to.clone()).or_insert(ResourceState::default()).add(&half_gain);
        }
        income
    }
}

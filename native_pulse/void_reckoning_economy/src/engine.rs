use crate::types::{EconomicNode, EconomicReport, GlobalEconomicRules, NodeType, ResourceState, SCALE_FACTOR};
use std::collections::HashMap;

use void_reckoning_shared::{Event, EventLog, EventSeverity, CorrelationContext};

pub struct IncomeEngine {
    nodes: Vec<EconomicNode>,
    rules: GlobalEconomicRules,
    pub event_log: Option<EventLog>,
    pub current_context: CorrelationContext,
}

impl IncomeEngine {
    pub fn new(rules: GlobalEconomicRules) -> Self {
        Self { 
            nodes: Vec::new(), 
            rules, 
            event_log: None,
            current_context: CorrelationContext::new(),
        }
    }
    
    pub fn set_event_log(&mut self, log: EventLog) {
        self.event_log = Some(log);
    }

    pub fn set_correlation_context(&mut self, context: CorrelationContext) {
        self.current_context = context;
    }

    pub fn add_node(&mut self, node: EconomicNode) {
        self.nodes.push(node);
    }

    pub fn set_rules(&mut self, rules: GlobalEconomicRules) {
        self.rules = rules;
    }

    pub fn process_faction(&self, faction_name: &str) -> EconomicReport {
        let mut total_income = ResourceState::default();
        let mut total_upkeep = ResourceState::default();
        let mut income_by_category: HashMap<String, ResourceState> = HashMap::new();
        let mut active_nodes = 0;
        let mut planet_count = 0;
        let mut fleet_count = 0;

        for node in &self.nodes {
            if node.owner_faction == faction_name {
                active_nodes += 1;
                let category = match node.node_type {
                    NodeType::Planet => "Tax",
                    NodeType::Station => "Mining",
                    _ => "Other",
                };

                if node.node_type == NodeType::Planet {
                    planet_count += 1;
                } else if node.node_type == NodeType::Fleet {
                    fleet_count += 1;
                }

                // Apply node efficiency & Global Rules
                let mut node_income = node.base_income;
                let mut node_upkeep = node.base_upkeep;

                node_income.multiply_fixed(node.efficiency_scaled);

                // Specialized Discounts
                if node.efficiency_scaled < SCALE_FACTOR {
                    if node.node_type == NodeType::Fleet {
                        // Efficiency < 1.0 on Fleet implies "In Orbit" (Discount)
                        node_upkeep.multiply_fixed(self.rules.orbit_discount_scaled);
                    } else if node.node_type == NodeType::Army {
                        // Efficiency < 1.0 on Army implies "In Garrison" (Discount)
                        node_upkeep.multiply_fixed(self.rules.garrison_discount_scaled);
                    }
                }

                // Apply Global Fleet Upkeep Scalar
                if node.node_type == NodeType::Fleet {
                    node_upkeep.multiply_fixed(self.rules.fleet_upkeep_scalar_scaled);
                }

                // Apply modifiers
                for modifier in &node.modifiers {
                    node_income.multiply_fixed(modifier.multiplier_scaled);
                    node_income.add(&modifier.flat_bonus);
                }

                total_income.add(&node_income);
                total_upkeep.add(&node_upkeep);

                let cat_entry = income_by_category.entry(category.to_string()).or_default();
                cat_entry.add(&node_income);
            }
        }

        // Apply Navy Penalty (Base Upkeep Scaler)
        let fleet_limit = (planet_count * self.rules.navy_penalty_ratio).max(1);
        if fleet_count > fleet_limit {
            let over = (fleet_count - fleet_limit) as i128;
            let penalty_pct = (over * self.rules.navy_penalty_rate_scaled).min(SCALE_FACTOR);
            // Apply penalty to credits upkeep
            let penalty = (total_upkeep.credits * penalty_pct) / SCALE_FACTOR;
            total_upkeep.credits += penalty;
        }

        let mut net_profit = total_income;
        net_profit.subtract(&total_upkeep);

        if net_profit.credits < 0 {
            if let Some(log) = &self.event_log {
                let evt = Event::new(
                    EventSeverity::Warning,
                    "Economy".to_string(),
                    format!("Faction {} is insolvent! Deficit: {}", faction_name, net_profit.credits),
                    self.current_context.child(),
                    None
                );
                log.add(evt);
            }
        }

        EconomicReport {
            faction_name: faction_name.to_string(),
            total_income,
            total_upkeep,
            net_profit,
            income_by_category,
            is_insolvent: net_profit.credits < 0,
            active_nodes,
        }
    }

    pub fn process_all(&self) -> HashMap<String, EconomicReport> {
        let mut faction_names = std::collections::HashSet::new();
        for node in &self.nodes {
            faction_names.insert(node.owner_faction.clone());
        }

        let mut reports = HashMap::new();
        for faction in faction_names {
            reports.insert(faction.clone(), self.process_faction(&faction));
        }
        reports
    }
}

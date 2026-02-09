use pyo3::prelude::*;
use serde_json::Value;
use std::collections::HashMap;
use std::sync::Arc;

// --- Pathfinder ---
use void_reckoning_pathfinder::GraphTopology;

#[pyclass]
pub struct RustPathfinder {
    pub inner: GraphTopology,
}

#[pymethods]
impl RustPathfinder {
    #[new]
    pub fn new() -> Self {
        RustPathfinder {
            inner: GraphTopology::new(),
        }
    }

    fn add_node(&mut self, id: String, terrain: Option<String>) {
        self.inner.add_node(id, terrain);
    }

    fn add_edge(&mut self, u: String, v: String, weight: f32) {
        self.inner.add_edge(&u, &v, weight);
    }
    
    fn clear(&mut self) {
        self.inner.clear();
    }

    #[pyo3(signature = (start, end, profile=None))]
    fn find_path(&self, start: String, end: String, profile: Option<String>) -> Option<(Vec<String>, f32)> {
        self.inner.find_path(&start, &end, profile)
    }
    
    fn sync_topology(&mut self, systems: Vec<(String, Vec<String>)>) {
        self.inner.clear();
        for (sys_id, connections) in systems {
            self.inner.add_node(sys_id.clone(), None);
            for target in connections {
                self.inner.add_edge(&sys_id, &target, 1.0);
            }
        }
    }

    fn set_correlation_context(&mut self, context: &void_reckoning_shared::CorrelationContext) {
        self.inner.run_id = context.span_id.clone();
    }
}

// --- Combat ---
use void_reckoning_combat::engine::BattleEngine;
use void_reckoning_combat::{CombatUnit, Weapon, WeaponType};

#[pyclass]
pub struct RustCombatEngine {
    pub inner: BattleEngine,
}

#[pymethods]
impl RustCombatEngine {
    #[new]
    pub fn new(width: f32, height: f32) -> Self {
        RustCombatEngine {
            inner: BattleEngine::new(width, height),
        }
    }
    
    fn add_unit(&mut self, id: u32, name: String, faction_idx: u8, max_hp: f32, x: f32, y: f32, weapons: Vec<(String, String, f32, f32, f32, f32)>, speed: f32, evasion: f32, shields_max: f32, armor: f32, cover_val: Option<u8>) {
        let mut unit = CombatUnit::new(id, name, faction_idx, max_hp);
        unit.position = (x, y);
        unit.speed = speed;
        unit.evasion = evasion;
        unit.shields = shields_max;
        unit.max_shields = shields_max;
        unit.armor = armor;
        unit.cover = match cover_val.unwrap_or(0) {
            1 => void_reckoning_combat::CoverType::Light,
            2 => void_reckoning_combat::CoverType::Heavy,
            3 => void_reckoning_combat::CoverType::Fortified,
            _ => void_reckoning_combat::CoverType::None,
        };
        
        for (w_name, w_type_str, range, damage, accuracy, cooldown) in weapons {
             let w_type = match w_type_str.as_str() {
                 "Energy" => WeaponType::Energy,
                 "Missile" => WeaponType::Missile,
                 "Beam" => WeaponType::Beam,
                 "Fighter" => WeaponType::Fighter,
                 _ => WeaponType::Kinetic,
             };
             
             let weapon = Weapon {
                 name: w_name,
                 weapon_type: w_type,
                 range,
                 damage,
                 accuracy,
                 cooldown,
                 current_cooldown: 0.0,
             };
             unit.weapons.push(weapon);
        }
        
        self.inner.add_unit(unit);
    }
    
    fn set_unit_cover(&mut self, id: u32, cover_val: u8) {
        self.inner.set_unit_cover(id, cover_val);
    }
    
    fn step(&mut self) -> bool {
        self.inner.step()
    }
    
    fn get_unit_status(&self, id: u32) -> Option<(f32, f32, bool)> {
        if let Some(u) = self.inner.state.get_unit(id) {
            Some((u.hp, u.shields, u.is_alive))
        } else {
            None
        }
    }
    
    fn get_state(&self) -> Vec<(u32, f32, f32, f32, bool)> {
        self.inner.state.units.iter().map(|u| (u.id, u.position.0, u.position.1, u.hp, u.is_alive)).collect()
    }

    fn set_correlation_context(&mut self, context: &void_reckoning_shared::CorrelationContext) {
        // Delegate to the inner engine which now supports full context
        self.inner.set_correlation_context(context.clone());
    }
    
    fn get_event_log(&self) -> Option<void_reckoning_shared::EventLog> {
        self.inner.event_log.clone()
    }
    
    fn enable_event_logging(&mut self) -> void_reckoning_shared::EventLog {
        let log = void_reckoning_shared::EventLog::new();
        self.inner.set_event_log(log.clone());
        log
    }
}

// --- Auditor ---
use void_reckoning_auditor::engine::ValidationEngine;
use void_reckoning_auditor::registry::Registries;
use void_reckoning_auditor::types::EntityType;

pub mod observability;

#[pyclass]
pub struct RustAuditor {
    engine: Option<ValidationEngine>,
    registries: Arc<Registries>,
}

#[pymethods]
impl RustAuditor {
    #[new]
    pub fn new() -> Self {
        Self {
            engine: None,
            registries: Arc::new(void_reckoning_auditor::registry::Registries::new()),
        }
    }

    pub fn load_registry(&mut self, registry_type: String, data_json: String) -> PyResult<()> {
        let data: serde_json::Map<String, Value> = serde_json::from_str(&data_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON error: {}", e)))?;
        
        let regs = Arc::make_mut(&mut self.registries);
        match registry_type.as_str() {
            "buildings" => regs.buildings = data,
            "technology" => regs.technology = data,
            "factions" => regs.factions = data,
            "weapons" => regs.weapons = data,
            "abilities" => regs.abilities = data,
            _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Unknown registry type")),
        }
        Ok(())
    }

    pub fn initialize(&mut self) -> PyResult<()> {
        self.engine = Some(ValidationEngine::new(Arc::clone(&self.registries)));
        Ok(())
    }

    pub fn enable_event_logging(&mut self) -> PyResult<void_reckoning_shared::EventLog> {
        let engine = self.engine.as_mut().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Auditor not initialized"))?;
        let log = void_reckoning_shared::EventLog::new();
        engine.set_event_log(log.clone());
        Ok(log)
    }

    pub fn validate_entity(&self, id: String, entity_type: String, data_json: String, universe_id: String, turn: u64) -> PyResult<String> {
        let engine = self.engine.as_ref().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Auditor not initialized"))?;
        let data: Value = serde_json::from_str(&data_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON error: {}", e)))?;
        
        let ent_type = match entity_type.as_str() {
            "unit" => EntityType::Unit,
            "building" => EntityType::Building,
            "technology" => EntityType::Technology,
            "faction" => EntityType::Faction,
            "portal" => EntityType::Portal,
            "campaign" => EntityType::Campaign,
            "fleet" | "Fleet" => EntityType::Fleet,
            "planet" | "Planet" => EntityType::Planet,
            _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Unknown entity type: {}", entity_type))),
        };

        let results = engine.validate_entity(id, ent_type, data, universe_id, turn);
        let result_json = serde_json::to_string(&results)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Serialization error: {}", e)))?;
        
        Ok(result_json)
    }

    pub fn set_correlation_context(&mut self, context: &void_reckoning_shared::CorrelationContext) -> PyResult<()> {
        let engine = self.engine.as_mut().ok_or_else(|| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Auditor not initialized"))?;
        engine.set_correlation_context(context.clone());
        Ok(())
    }
}

// --- Economy ---
use void_reckoning_economy::engine::IncomeEngine;
use void_reckoning_economy::types::{EconomicNode, GlobalEconomicRules};
use void_reckoning_economy::trade::{TradeRoute, TradeRouteManager};

#[pyclass]
pub struct RustEconomyEngine {
    engine: IncomeEngine,
    trade_manager: TradeRouteManager,
}

#[pymethods]
impl RustEconomyEngine {
    #[new]
    pub fn new() -> Self {
        Self {
            engine: IncomeEngine::new(GlobalEconomicRules::default()),
            trade_manager: TradeRouteManager::new(),
        }
    }

    pub fn set_rules(&mut self, rules_json: String) -> PyResult<()> {
        let rules: GlobalEconomicRules = serde_json::from_str(&rules_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON error: {}", e)))?;
        self.engine.set_rules(rules);
        Ok(())
    }

    pub fn add_node(&mut self, node_json: String) -> PyResult<()> {
        let node: EconomicNode = serde_json::from_str(&node_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON error: {}", e)))?;
        self.engine.add_node(node);
        Ok(())
    }

    pub fn add_trade_route(&mut self, route_json: String) -> PyResult<()> {
        let route: TradeRoute = serde_json::from_str(&route_json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON error: {}", e)))?;
        self.trade_manager.add_route(route);
        Ok(())
    }

    pub fn calculate_trade(&mut self, pathfinder: &RustPathfinder) -> PyResult<String> {
        self.trade_manager.calculate_efficiencies(&pathfinder.inner);
        let reports = self.trade_manager.get_total_trade_income();
        let reports_json = serde_json::to_string(&reports)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Serialization error: {}", e)))?;
        Ok(reports_json)
    }

    pub fn process_faction(&self, faction_name: String) -> PyResult<String> {
        let report = self.engine.process_faction(&faction_name);
        let report_json = serde_json::to_string(&report)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Serialization error: {}", e)))?;
        Ok(report_json)
    }

    pub fn process_all(&self) -> PyResult<String> {
        let reports = self.engine.process_all();
        let reports_json = serde_json::to_string(&reports)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Serialization error: {}", e)))?;
        Ok(reports_json)
    }

    pub fn enable_event_logging(&mut self) -> void_reckoning_shared::EventLog {
        let log = void_reckoning_shared::EventLog::new();
        self.engine.set_event_log(log.clone());
        log
    }

    pub fn set_correlation_context(&mut self, context: &void_reckoning_shared::CorrelationContext) {
        self.engine.set_correlation_context(context.clone());
    }
}

// --- Observability ---
use void_reckoning_shared::{CausalGraph, Event};

#[pyclass]
pub struct RustCausalGraph {
    pub inner: CausalGraph,
}

#[pymethods]
impl RustCausalGraph {
    #[new]
    pub fn new() -> Self {
        RustCausalGraph {
            inner: CausalGraph::new(),
        }
    }

    fn add_event_json(&mut self, json_str: String) -> PyResult<()> {
        self.inner.add_event_json(&json_str)
    }

    fn get_causal_chain(&self, span_id: String) -> Vec<Event> {
        self.inner.get_causal_chain(span_id)
    }

    fn get_consequences(&self, span_id: String) -> Vec<Event> {
        self.inner.get_consequences(span_id)
    }
    
    fn size(&self) -> usize {
        self.inner.size()
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn void_reckoning_bridge(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustPathfinder>()?;
    m.add_class::<RustCombatEngine>()?;
    m.add_class::<RustAuditor>()?;
    m.add_class::<RustEconomyEngine>()?;
    m.add_class::<RustCausalGraph>()?; // New
    
    // Add shared classes for correct type mapping
    m.add_class::<void_reckoning_shared::Event>()?;
    m.add_class::<void_reckoning_shared::CorrelationContext>()?;
    m.add_class::<void_reckoning_shared::EventSeverity>()?;
    
    // Submodule for observability
    let obs_submodule = PyModule::new_bound(m.py(), "observability")?;
    observability::observability(&obs_submodule)?;
    m.add_submodule(&obs_submodule)?;
    
    Ok(())
}

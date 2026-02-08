use pyo3::prelude::*;
use void_reckoning_pathfinder::GraphTopology;
use void_reckoning_combat::engine::BattleEngine;
use void_reckoning_combat::{CombatUnit, Weapon, WeaponType};

#[pyclass]
struct RustPathfinder {
    inner: GraphTopology,
}

#[pymethods]
impl RustPathfinder {
    #[new]
    fn new() -> Self {
        RustPathfinder {
            inner: GraphTopology::new(),
        }
    }

    fn add_node(&mut self, id: String) {
        self.inner.add_node(id);
    }

    fn add_edge(&mut self, u: String, v: String, weight: f32) {
        self.inner.add_edge(&u, &v, weight);
    }
    
    fn clear(&mut self) {
        self.inner.clear();
    }

    fn find_path(&self, start: String, end: String) -> Option<(Vec<String>, f32)> {
        self.inner.find_path(&start, &end)
    }
    
    fn sync_topology(&mut self, systems: Vec<(String, Vec<String>)>) {
        // Bulk Sync for performance?
        // Logic: clear -> add nodes -> add edges
        self.inner.clear();
        for (sys_id, connections) in systems {
            self.inner.add_node(sys_id.clone());
            for target in connections {
                // We add directed edges; python graph is usually undirected (bi-directional)
                // We'll rely on the input list having both directions or handle it.
                // Assuming input is Adjacency List: A -> [B, C]
                self.inner.add_edge(&sys_id, &target, 1.0);
            }
        }
    }
}

#[pyclass]
struct RustCombatEngine {
    inner: BattleEngine,
}

#[pymethods]
impl RustCombatEngine {
    #[new]
    fn new(width: f32, height: f32) -> Self {
        RustCombatEngine {
            inner: BattleEngine::new(width, height),
        }
    }
    
    fn add_unit(&mut self, id: u32, name: String, faction_idx: u8, max_hp: f32, x: f32, y: f32, weapons: Vec<(String, String, f32, f32, f32, f32)>) {
        let mut unit = CombatUnit::new(id, name, faction_idx, max_hp);
        unit.position = (x, y);
        
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
        // Return simplified state: (id, x, y, hp, is_alive)
        self.inner.state.units.iter().map(|u| (u.id, u.position.0, u.position.1, u.hp, u.is_alive)).collect()
    }
}

use void_reckoning_auditor::engine::ValidationEngine;
use void_reckoning_auditor::registry::Registries;
use void_reckoning_auditor::types::{EntityType, ValidationSeverity};
use serde_json::Value;
use std::sync::Arc;
use std::str::FromStr;

#[pyclass]
struct RustAuditor {
    registries: Option<Registries>,
    engine: Option<ValidationEngine>,
}

#[pymethods]
impl RustAuditor {
    #[new]
    fn new() -> Self {
        RustAuditor {
            registries: Some(Registries::new()),
            engine: None,
        }
    }

    fn load_registry(&mut self, registry_type: String, data_json: String) -> PyResult<()> {
        if let Some(regs) = &mut self.registries {
            let parsed_data: serde_json::Map<String, Value> = serde_json::from_str(&data_json)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid JSON: {}", e)))?;
            
            match registry_type.as_str() {
                "buildings" => regs.buildings.extend(parsed_data),
                "technology" => regs.technology.extend(parsed_data),
                "factions" => regs.factions.extend(parsed_data),
                "weapons" => regs.weapons.extend(parsed_data),
                "abilities" => regs.abilities.extend(parsed_data),
                 _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Unknown registry type")),
            }
            Ok(())
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Registries already initialized"))
        }
    }

    fn initialize(&mut self) -> PyResult<()> {
        if let Some(regs) = self.registries.take() {
            let engine = ValidationEngine::new(Arc::new(regs));
            self.engine = Some(engine);
            Ok(())
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Already initialized or registries missing"))
        }
    }

    fn validate_entity(&self, id: String, entity_type_str: String, data_json: String, universe_id: String, turn: u64) -> PyResult<String> {
        if let Some(engine) = &self.engine {
            let entity_type = match entity_type_str.as_str() {
                "unit" => EntityType::Unit,
                "building" => EntityType::Building,
                "technology" => EntityType::Technology,
                "faction" => EntityType::Faction,
                "portal" => EntityType::Portal,
                "campaign" => EntityType::Campaign,
                _ => return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("Unknown entity type")),
            };
            
            let data: Value = serde_json::from_str(&data_json)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("Invalid JSON data: {}", e)))?;

            let results = engine.validate_entity(id, entity_type, data, universe_id, turn);
            
            // Serialize results back to JSON string for Python
            serde_json::to_string(&results)
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(format!("Serialization error: {}", e)))
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Engine not initialized"))
        }
    }
}

/// A Python module implemented in Rust.
#[pymodule]
fn void_reckoning_bridge(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<RustPathfinder>()?;
    m.add_class::<RustCombatEngine>()?;
    m.add_class::<RustAuditor>()?;
    Ok(())
}

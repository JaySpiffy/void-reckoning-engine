use serde_json::{Map, Value};

#[derive(Debug, Clone)]
pub struct Registries {
    pub buildings: Map<String, Value>,
    pub technology: Map<String, Value>,
    pub factions: Map<String, Value>,
    pub weapons: Map<String, Value>,
    pub abilities: Map<String, Value>,
}

impl Registries {
    pub fn new() -> Self {
        Self {
            buildings: Map::new(),
            technology: Map::new(),
            factions: Map::new(),
            weapons: Map::new(),
            abilities: Map::new(),
        }
    }
}

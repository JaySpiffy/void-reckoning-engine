use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::algo::astar;
use petgraph::visit::EdgeRef;
use std::collections::HashMap;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub enum TerrainType {
    Space,
    Plains,
    Forest, 
    Mountain,
    Water,
}

#[derive(Debug, Clone, Copy)]
pub enum MovementProfile {
    Space,
    Ground,
    Hover,
}

/// A lightweight wrapper around petgraph to manage the universe topology.
pub struct GraphTopology {
    graph: DiGraph<NodeData, f32>,
    node_map: HashMap<String, NodeIndex>,
    pub run_id: String,
}

#[derive(Clone)]
pub struct NodeData {
    pub id: String,
    pub terrain: TerrainType,
}

impl GraphTopology {
    pub fn new() -> Self {
        Self {
            graph: DiGraph::new(),
            node_map: HashMap::new(),
            run_id: uuid::Uuid::new_v4().to_string(),
        }
    }

    /// Adds a node (system) to the graph. Returns the NodeIndex.
    pub fn add_node(&mut self, id: String, terrain_str: Option<String>) -> NodeIndex {
        if let Some(&idx) = self.node_map.get(&id) {
            // Update terrain if needed? For now just return.
            return idx;
        }
        
        let terrain = match terrain_str.as_deref() {
            Some("Mountain") => TerrainType::Mountain,
            Some("Water") => TerrainType::Water,
            Some("Forest") => TerrainType::Forest,
            Some("Plains") => TerrainType::Plains,
            _ => TerrainType::Space,
        };
        
        let node_data = NodeData { id: id.clone(), terrain };
        let idx = self.graph.add_node(node_data);
        self.node_map.insert(id, idx);
        idx
    }

    /// Adds a directional edge between two systems with a given cost (weight).
    pub fn add_edge(&mut self, from_id: &str, to_id: &str, weight: f32) {
        // Default terrain to Space if nodes don't exist yet (auto-create)
        let from_idx = self.add_node(from_id.to_string(), None);
        let to_idx = self.add_node(to_id.to_string(), None);
        self.graph.add_edge(from_idx, to_idx, weight);
    }
    
    /// Clears the graph state.
    pub fn clear(&mut self) {
        self.graph.clear();
        self.node_map.clear();
    }

    /// Finds the shortest path between two systems using A*.
    /// Returns a vector of system IDs (strings) including start and end.
    pub fn find_path(&self, start_id: &str, end_id: &str, profile_str: Option<String>) -> Option<(Vec<String>, f32)> {
        let start_idx = *self.node_map.get(start_id)?;
        let end_idx = *self.node_map.get(end_id)?;

        let profile = match profile_str.as_deref() {
            Some("Ground") => MovementProfile::Ground,
            Some("Hover") => MovementProfile::Hover,
            _ => MovementProfile::Space,
        };

        // Custom cost function closure
        let edge_cost = |e: petgraph::graph::EdgeReference<f32> | -> f32 {
            let base_cost = *e.weight();
            let target_node = &self.graph[e.target()];
            
            match profile {
                MovementProfile::Space => {
                    // Space units ignore terrain penalties (usually)
                    base_cost 
                },
                MovementProfile::Ground => {
                    match target_node.terrain {
                        TerrainType::Mountain => base_cost * 2.0,
                        TerrainType::Water => f32::INFINITY, // Impassable
                        TerrainType::Forest => base_cost * 1.5,
                        _ => base_cost,
                    }
                },
                MovementProfile::Hover => {
                    // Hover ignores water/forest penalties, but maybe mountain doubles?
                    match target_node.terrain {
                        TerrainType::Mountain => base_cost * 2.0,
                        _ => base_cost,
                    }
                }
            }
        };

        let path_result: Option<(f32, Vec<NodeIndex>)> = astar(
            &self.graph,
            start_idx,
            |finish| finish == end_idx,
            edge_cost,
            |_| 0.0, // Heuristic
        );

        match path_result {
            Some((cost, path_indices)) => {
                if cost.is_infinite() { return None; }
                
                let path_ids: Vec<String> = path_indices
                    .into_iter()
                    .map(|idx| self.graph[idx].id.clone())
                    .collect();
                Some((path_ids, cost))
            }
            None => None,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_simple_path() {
        let mut topo = GraphTopology::new();
        topo.add_edge("A", "B", 10.0);
        topo.add_edge("B", "C", 20.0);
        topo.add_edge("A", "C", 100.0); // Expensive shortcut

        // A -> B -> C is 30.0
        // A -> C is 100.0
        let (path, cost) = topo.find_path("A", "C").unwrap();
        
        assert_eq!(path, vec!["A", "B", "C"]);
        assert_eq!(cost, 30.0);
    }
    
    #[test]
    fn test_no_path() {
        let mut topo = GraphTopology::new();
        topo.add_edge("A", "B", 10.0);
        topo.add_edge("C", "D", 10.0);
        
        let result = topo.find_path("A", "D");
        assert!(result.is_none());
    }
}

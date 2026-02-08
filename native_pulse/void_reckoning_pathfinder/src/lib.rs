use petgraph::graph::{DiGraph, NodeIndex};
use petgraph::algo::astar;
use std::collections::HashMap;

/// A lightweight wrapper around petgraph to manage the universe topology.
pub struct GraphTopology {
    graph: DiGraph<String, f32>,
    node_map: HashMap<String, NodeIndex>,
}

impl GraphTopology {
    pub fn new() -> Self {
        Self {
            graph: DiGraph::new(),
            node_map: HashMap::new(),
        }
    }

    /// Adds a node (system) to the graph. Returns the NodeIndex.
    /// If the node already exists, returns the existing index.
    pub fn add_node(&mut self, id: String) -> NodeIndex {
        if let Some(&idx) = self.node_map.get(&id) {
            return idx;
        }
        let idx = self.graph.add_node(id.clone());
        self.node_map.insert(id, idx);
        idx
    }

    /// Adds a directional edge between two systems with a given cost (weight).
    pub fn add_edge(&mut self, from_id: &str, to_id: &str, weight: f32) {
        let from_idx = self.add_node(from_id.to_string());
        let to_idx = self.add_node(to_id.to_string());
        self.graph.add_edge(from_idx, to_idx, weight);
    }
    
    /// Clears the graph state.
    pub fn clear(&mut self) {
        self.graph.clear();
        self.node_map.clear();
    }

    /// Finds the shortest path between two systems using A*.
    /// Returns a vector of system IDs (strings) including start and end.
    pub fn find_path(&self, start_id: &str, end_id: &str) -> Option<(Vec<String>, f32)> {
        let start_idx = *self.node_map.get(start_id)?;
        let end_idx = *self.node_map.get(end_id)?;

        // Simple heuristic: 0 for now (Dijkstra). 
        // For true A*, we'd scope coordinates into the node weight.
        let path_result = astar(
            &self.graph,
            start_idx,
            |finish| finish == end_idx,
            |e| *e.weight(),
            |_| 0.0, // Heuristic
        );

        match path_result {
            Some((cost, path_indices)) => {
                let path_ids: Vec<String> = path_indices
                    .into_iter()
                    .map(|idx| self.graph[idx].clone())
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

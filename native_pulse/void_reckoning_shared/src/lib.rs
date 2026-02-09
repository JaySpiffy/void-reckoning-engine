use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use std::fmt;
use std::sync::{Arc, Mutex};
use uuid::Uuid;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct CorrelationContext {
    #[pyo3(get, set)]
    pub trace_id: String,
    #[pyo3(get, set)]
    pub span_id: String,
    #[pyo3(get, set)]
    pub parent_id: Option<String>,
}

#[pymethods]
impl CorrelationContext {
    #[new]
    pub fn new() -> Self {
        Self {
            trace_id: Uuid::new_v4().to_string(),
            span_id: Uuid::new_v4().to_string(),
            parent_id: None,
        }
    }

    pub fn child(&self) -> Self {
        Self {
            trace_id: self.trace_id.clone(),
            span_id: Uuid::new_v4().to_string(),
            parent_id: Some(self.span_id.clone()),
        }
    }

    #[staticmethod]
    pub fn from_json(json: &str) -> PyResult<Self> {
        serde_json::from_str(json)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON error: {}", e)))
    }

    pub fn to_json(&self) -> String {
        serde_json::to_string(self).unwrap_or_default()
    }
}

impl fmt::Display for CorrelationContext {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[Trace: {} | Span: {}]", self.trace_id, self.span_id)
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(eq, eq_int)]
#[derive(PartialEq)]
pub enum EventSeverity {
    Debug,
    Info,
    Warning,
    Error,
    Critical,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Event {
    #[pyo3(get)]
    pub timestamp: f64,
    #[pyo3(get)]
    pub severity: EventSeverity,
    #[pyo3(get)]
    pub category: String,
    #[pyo3(get)]
    pub message: String,
    #[pyo3(get)]
    pub context: CorrelationContext,
    #[pyo3(get)]
    pub data: Option<String>,
}

#[pymethods]
impl Event {
    #[new]
    pub fn new(
        severity: EventSeverity,
        category: String,
        message: String,
        context: CorrelationContext,
        data: Option<String>,
    ) -> Self {
        let start = SystemTime::now();
        let since_the_epoch = start
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default();
        let timestamp = since_the_epoch.as_secs_f64();

        Self {
            timestamp,
            severity,
            category,
            message,
            context,
            data,
        }
    }

    fn __repr__(&self) -> String {
        format!("[{}] {:?} {}: {}", self.timestamp, self.severity, self.category, self.message)
    }
}

#[pyclass]
#[derive(Clone)]
pub struct EventLog {
   pub events: Arc<Mutex<Vec<Event>>>,
}

#[pymethods]
impl EventLog {
    #[new]
    pub fn new() -> Self {
        Self {
            events: Arc::new(Mutex::new(Vec::new())),
        }
    }

    pub fn add(&self, event: Event) {
        if let Ok(mut events) = self.events.lock() {
            events.push(event);
        }
    }

    pub fn get_all(&self) -> Vec<Event> {
        if let Ok(events) = self.events.lock() {
            events.clone()
        } else {
            Vec::new()
        }
    }
    
    pub fn clear(&self) {
        if let Ok(mut events) = self.events.lock() {
            events.clear();
        }
    }
}

use std::collections::{HashMap, VecDeque};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct CausalGraph {
    // We use Arc<Mutex> for thread safety if shared across threads, 
    // though typically the bridge might own it uniquely or wrap it.
    // simpler to just put the data in standard structs and wrap the whole Graph in Arc<Mutex> in the bridge.
    // For now, let's keep it simple internal logic.
    
    // Key: span_id
    pub events: HashMap<String, Event>,
    // Key: child_span_id -> parent_span_id
    pub parent_map: HashMap<String, String>,
    // Key: parent_span_id -> Vec<child_span_id>
    pub children_map: HashMap<String, Vec<String>>,
}

#[pymethods]
impl CausalGraph {
    #[new]
    pub fn new() -> Self {
        Self {
            events: HashMap::new(),
            parent_map: HashMap::new(),
            children_map: HashMap::new(),
        }
    }

    pub fn add_event(&mut self, event: Event) {
        let span_id = event.context.span_id.clone();
        
        // Link parent if exists
        if let Some(parent_id) = &event.context.parent_id {
            self.parent_map.insert(span_id.clone(), parent_id.clone());
            self.children_map.entry(parent_id.clone()).or_default().push(span_id.clone());
        }
        
        self.events.insert(span_id, event);
    }
    
    /// Adds a raw JSON event string (for fast bulk loading from python)
    pub fn add_event_json(&mut self, json_str: &str) -> PyResult<()> {
        let event: Event = serde_json::from_str(json_str)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyValueError, _>(format!("JSON error: {}", e)))?;
        self.add_event(event);
        Ok(())
    }

    /// Traces backward from the given event to find the root cause chain.
    /// Returns list of Events [Root ... -> Target].
    pub fn get_causal_chain(&self, span_id: String) -> Vec<Event> {
        let mut chain = Vec::new();
        let mut current_id = Some(span_id);

        while let Some(id) = current_id {
            if let Some(event) = self.events.get(&id) {
                chain.push(event.clone());
                // Move to parent
                current_id = self.parent_map.get(&id).cloned();
            } else {
                // Event not found (broken link or end of known history)
                break;
            }
        }
        
        // The chain is currently [Target -> ... -> Root]
        // Reverse it to be chronological [Root -> ... -> Target]
        chain.reverse();
        chain
    }
    
    /// Traces forward to find all downstream consequences (BFS).
    /// Returns a flat list of ALL descendent events.
    pub fn get_consequences(&self, span_id: String) -> Vec<Event> {
        let mut consequences = Vec::new();
        let mut queue = VecDeque::new();
        queue.push_back(span_id);
        
        while let Some(id) = queue.pop_front() {
            if let Some(children) = self.children_map.get(&id) {
                for child_id in children {
                    if let Some(child_event) = self.events.get(child_id) {
                        consequences.push(child_event.clone());
                        queue.push_back(child_id.clone());
                    }
                }
            }
        }
        
        consequences
    }
    
    pub fn size(&self) -> usize {
        self.events.len()
    }
}

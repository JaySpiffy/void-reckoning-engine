use crate::rules::{ValidationRule, ValidationContext, FieldExistenceRule, TypeValidationRule, ReferenceIntegrityRule};
use crate::types::{ValidationResult, ValidationSummary, ValidationReport, EntityType, ValidationSeverity};
use crate::registry::Registries;
use std::sync::Arc;
use serde_json::Value;

use void_reckoning_shared::{Event, EventLog, EventSeverity, CorrelationContext};

pub struct ValidationEngine {
    rules: Vec<Arc<dyn ValidationRule>>,
    registries: Arc<Registries>,
    pub event_log: Option<EventLog>,
    pub current_context: CorrelationContext,
}

impl ValidationEngine {
    pub fn new(registries: Arc<Registries>) -> Self {
        let rules: Vec<Arc<dyn ValidationRule>> = vec![
            Arc::new(FieldExistenceRule),
            Arc::new(TypeValidationRule),
            Arc::new(ReferenceIntegrityRule),
        ];
        
        Self {
            rules,
            registries,
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
    
    pub fn validate_entity(
        &self,
        entity_id: String,
        entity_type: EntityType,
        data: Value,
        universe_id: String,
        turn: u64,
    ) -> Vec<ValidationResult> {
        let context = ValidationContext {
            entity_id,
            entity_type,
            data,
            registries: Arc::clone(&self.registries),
            universe_id,
            turn,
        };
        
        let mut results = Vec::new();
        
        for rule in &self.rules {
            if rule.is_enabled() {
                let result = rule.validate(&context);
                if result.severity != ValidationSeverity::Info {
                    if let Some(log) = &self.event_log {
                        let severity = match result.severity {
                            ValidationSeverity::Warning => EventSeverity::Warning,
                            ValidationSeverity::Error => EventSeverity::Error,
                            ValidationSeverity::Critical => EventSeverity::Critical,
                            _ => EventSeverity::Info,
                        };
                        
                        let evt = Event::new(
                            severity,
                            "Auditor".to_string(),
                            format!("[Rule: {}] {}", result.rule_name, result.message),
                            self.current_context.child(),
                            Some(result.entity_id.clone())
                        );
                        log.add(evt);
                    }
                    results.push(result);
                }
            }
        }
        
        results
    }
    
    pub fn validate_batch(
        &self,
        entities: Vec<(String, EntityType, Value)>,
        universe_id: String,
        turn: u64,
    ) -> ValidationReport {
        let mut all_results = Vec::new();
        let mut summary = ValidationSummary {
            total_checks: entities.len(),
            passed: 0,
            warnings: 0,
            errors: 0,
            critical: 0,
        };
        
        for (entity_id, entity_type, data) in entities {
            let results = self.validate_entity(
                entity_id,
                entity_type,
                data,
                universe_id.clone(),
                turn,
            );
            
            if results.is_empty() {
                 summary.passed += 1;
            } else {
                 for result in &results {
                    match result.severity {
                        ValidationSeverity::Info => {}, // Should not happen in results list if filtered above
                        ValidationSeverity::Warning => summary.warnings += 1,
                        ValidationSeverity::Error => summary.errors += 1,
                        ValidationSeverity::Critical => summary.critical += 1,
                    }
                 }
                all_results.extend(results);
            }
        }
        
        ValidationReport {
            results: all_results,
            summary,
            // Simple correlation ID for now
            correlation_id: format!("{}-{}", universe_id, turn),
        }
    }
}

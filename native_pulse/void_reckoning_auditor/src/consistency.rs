use crate::types::{ValidationResult, ValidationCategory, ValidationSeverity};
use serde_json::Value;

pub trait InvariantValidator: Send + Sync {
    fn validate(&self, state: &Value) -> ValidationResult;
    fn name(&self) -> &str;
    fn description(&self) -> &str;
}

pub struct HealthInvariantValidator;

impl InvariantValidator for HealthInvariantValidator {
    fn validate(&self, state: &Value) -> ValidationResult {
        let mut violations = Vec::new();
        
        // Assuming state contains "units" array (simplified)
        // In real implementation, this would traverse the snapshot
        if let Some(units) = state.get("units").and_then(|v| v.as_array()) {
            for unit in units {
                let id = unit.get("id").and_then(|v| v.as_str()).unwrap_or("unknown");
                if let Some(hp) = unit.get("hp").and_then(|v| v.as_f64()) {
                    if hp < 0.0 {
                         violations.push(format!("Unit {} has negative HP: {}", id, hp));
                    }
                    if let Some(max_hp) = unit.get("max_hp").and_then(|v| v.as_f64()) {
                        if hp > max_hp {
                             violations.push(format!("Unit {} has HP > MaxHP: {} > {}", id, hp, max_hp));
                        }
                    }
                }
            }
        }
        
        if violations.is_empty() {
             ValidationResult {
                category: ValidationCategory::CrossSystem,
                severity: ValidationSeverity::Info,
                entity_id: "global".to_string(),
                message: "Health invariant satisfied".to_string(),
                rule_name: self.name().to_string(),
                file_path: None,
                timestamp: 0,
            }
        } else {
             ValidationResult {
                category: ValidationCategory::CrossSystem,
                severity: ValidationSeverity::Critical,
                entity_id: "global".to_string(),
                message: format!("Health invariant violations: {}", violations.join(", ")),
                rule_name: self.name().to_string(),
                file_path: None,
                timestamp: 0,
            }
        }
    }
    
    fn name(&self) -> &str { "health_invariant" }
    fn description(&self) -> &str { "Ensures unit health is within valid range [0, MaxHP]" }
}

use crate::types::{ValidationResult, ValidationCategory, ValidationSeverity, EntityType};
use crate::registry::Registries;
use std::sync::Arc;
use serde_json::Value;

#[derive(Debug, Clone)]
pub struct ValidationContext {
    pub entity_id: String,
    pub entity_type: EntityType,
    pub data: Value,
    pub registries: Arc<Registries>,
    pub universe_id: String,
    pub turn: u64,
}

pub trait ValidationRule: Send + Sync {
    fn validate(&self, context: &ValidationContext) -> ValidationResult;
    fn name(&self) -> &str;
    fn category(&self) -> ValidationCategory;
    fn severity(&self) -> ValidationSeverity;
    fn is_enabled(&self) -> bool;
}

pub struct FieldExistenceRule;

impl ValidationRule for FieldExistenceRule {
    fn validate(&self, context: &ValidationContext) -> ValidationResult {
        let required_fields = match context.entity_type {
            EntityType::Unit => vec!["name", "tier", "armor", "speed"],
            EntityType::Building => vec!["name", "tier", "cost"],
            EntityType::Technology => vec!["name", "tier", "cost"],
            EntityType::Faction => vec!["name", "subfactions"],
            _ => vec![],
        };
        
        for field in required_fields {
            if context.data.get(field).is_none() {
                return ValidationResult {
                    category: self.category(),
                    severity: self.severity(),
                    entity_id: context.entity_id.clone(),
                    message: format!("Missing required field: {}", field),
                    rule_name: self.name().to_string(),
                    file_path: None,
                    timestamp: 0,
                };
            }
        }
        
        ValidationResult {
            category: self.category(),
            severity: ValidationSeverity::Info,
            entity_id: context.entity_id.clone(),
            message: "All required fields present".to_string(),
            rule_name: self.name().to_string(),
            file_path: None,
            timestamp: 0,
        }
    }
    
    fn name(&self) -> &str { "field_existence" }
    fn category(&self) -> ValidationCategory { ValidationCategory::FileStructure }
    fn severity(&self) -> ValidationSeverity { ValidationSeverity::Critical }
    fn is_enabled(&self) -> bool { true }
}

pub struct TypeValidationRule;

impl ValidationRule for TypeValidationRule {
    fn validate(&self, context: &ValidationContext) -> ValidationResult {
        // Basic type checks based on field names
        let mut violations = Vec::new();
        
        if let Some(tier) = context.data.get("tier") {
            if !tier.is_u64() {
                violations.push("Field 'tier' must be an integer".to_string());
            }
        }
        
        if let Some(cost) = context.data.get("cost") {
            if !cost.is_u64() && !cost.is_f64() {
                 violations.push("Field 'cost' must be a number".to_string());
            }
        }

        if !violations.is_empty() {
             return ValidationResult {
                category: self.category(),
                severity: self.severity(),
                entity_id: context.entity_id.clone(),
                message: format!("Type violations: {}", violations.join(", ")),
                rule_name: self.name().to_string(),
                file_path: None,
                timestamp: 0,
            };
        }

        ValidationResult {
            category: self.category(),
            severity: ValidationSeverity::Info,
            entity_id: context.entity_id.clone(),
            message: "Type validation passed".to_string(),
            rule_name: self.name().to_string(),
            file_path: None,
            timestamp: 0,
        }
    }

    fn name(&self) -> &str { "type_validation" }
    fn category(&self) -> ValidationCategory { ValidationCategory::FileStructure }
    fn severity(&self) -> ValidationSeverity { ValidationSeverity::Error }
    fn is_enabled(&self) -> bool { true }
}

pub struct ReferenceIntegrityRule;

impl ValidationRule for ReferenceIntegrityRule {
    fn validate(&self, context: &ValidationContext) -> ValidationResult {
        let registries = &context.registries;
        
        // Check building reference
        if let Some(building_ref) = context.data.get("required_building") {
            if let Some(building_str) = building_ref.as_str() {
                if building_str != "None" && !registries.buildings.contains_key(building_str) {
                    return ValidationResult {
                        category: self.category(),
                        severity: self.severity(),
                        entity_id: context.entity_id.clone(),
                        message: format!("Invalid Building Reference: '{}'", building_str),
                        rule_name: self.name().to_string(),
                        file_path: None,
                        timestamp: 0,
                    };
                }
            }
        }
        
        // Check tech references
        if let Some(tech_refs) = context.data.get("required_tech") {
            if let Some(tech_array) = tech_refs.as_array() {
                for tech in tech_array {
                    if let Some(tech_str) = tech.as_str() {
                        if !registries.technology.contains_key(tech_str) {
                            return ValidationResult {
                                category: self.category(),
                                severity: self.severity(),
                                entity_id: context.entity_id.clone(),
                                message: format!("Invalid Tech Reference: '{}'", tech_str),
                                rule_name: self.name().to_string(),
                                file_path: None,
                                timestamp: 0,
                            };
                        }
                    }
                }
            }
        }
        
        ValidationResult {
            category: self.category(),
            severity: ValidationSeverity::Info,
            entity_id: context.entity_id.clone(),
            message: "Reference integrity valid".to_string(),
            rule_name: self.name().to_string(),
            file_path: None,
            timestamp: 0,
        }
    }
    
    fn name(&self) -> &str { "reference_integrity" }
    fn category(&self) -> ValidationCategory { ValidationCategory::Units } // Or specific based on context entity?
    fn severity(&self) -> ValidationSeverity { ValidationSeverity::Error }
    fn is_enabled(&self) -> bool { true }
}

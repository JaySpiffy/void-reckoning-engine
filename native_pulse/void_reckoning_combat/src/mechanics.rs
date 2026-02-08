use rand::Rng;

#[derive(Debug, Clone, Copy, PartialEq)] 
pub enum DamageType {
    Kinetic,
    Energy,
    Explosive,
}

pub trait DamageSource {
    fn calculate_damage(&self, rng: &mut impl Rng) -> f32;
    fn get_damage_type(&self) -> DamageType;
    fn get_accuracy(&self) -> f32;
}

pub trait Armor {
    fn mitigate_damage(&self, damage: f32, damage_type: DamageType) -> f32;
}

// Implementation for Weapon
impl DamageSource for crate::Weapon {
    fn calculate_damage(&self, rng: &mut impl Rng) -> f32 {
        // Simple variation: +/- 10%
        let variation = rng.gen_range(0.9..1.1);
        self.damage * variation
    }

    fn get_damage_type(&self) -> DamageType {
        match self.weapon_type {
            crate::WeaponType::Kinetic => DamageType::Kinetic,
            crate::WeaponType::Energy => DamageType::Energy,
            crate::WeaponType::Missile => DamageType::Explosive,
            crate::WeaponType::Beam => DamageType::Energy,
            crate::WeaponType::Fighter => DamageType::Kinetic,
        }
    }

    fn get_accuracy(&self) -> f32 {
        self.accuracy
    }
}

// Implementation for CombatUnit
impl Armor for crate::CombatUnit {
    fn mitigate_damage(&self, damage: f32, damage_type: DamageType) -> f32 {
        let mitigation_factor = match damage_type {
            DamageType::Kinetic => self.armor / (self.armor + 100.0), // Diminishing returns
            DamageType::Energy => {
                if self.max_shields > 0.0 {
                    (self.shields / self.max_shields).max(0.0) * 0.5
                } else {
                    0.0
                }
            },
            DamageType::Explosive => 0.0, // Explosive ignores armor? Or flat reduction?
        };
        
        let mitigated = damage * (1.0 - mitigation_factor);
        if mitigated < 0.0 { 0.0 } else { mitigated }
    }
}

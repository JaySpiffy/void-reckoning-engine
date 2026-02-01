import pytest
from src.core.payload_registry import PayloadRegistry
from src.core.elemental_signature import (
    ATOM_MASS, ATOM_ENERGY, ATOM_STABILITY, ATOM_FREQUENCY, 
    ATOM_AETHER, ATOM_VOLATILITY, ATOM_COHESION
)

class TestPayloadRegistry:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.registry = PayloadRegistry.get_instance()
        
    def test_tractor_beam_dynamic_pull(self):
        """
        Borg Cube (Mass 60, Energy 10) vs Defiant (Mass 20)
        Pull force = (60 * 10) / (20 + 1) = 600 / 21 = 28.57
        """
        caster_dna = {ATOM_MASS: 60.0, ATOM_ENERGY: 10.0}
        target_dna = {ATOM_MASS: 20.0}
        
        # Test with specific universe
        result = self.registry.execute_payload("tractor_beam", caster_dna, target_dna, universe="soase")
        
        assert result["effect_type"] == "mobility_debuff"
        # 28.57 / 100 = 0.2857 reduction
        assert result["magnitude"] == pytest.approx(0.2857, abs=1e-4)
        assert "Tractor Beam" in result["description"]

    def test_emp_stun_calculation(self):
        """
        High Frequency attacker vs Low Stability target
        """
        caster_dna = {ATOM_FREQUENCY: 40.0, ATOM_ENERGY: 30.0}
        target_dna = {ATOM_STABILITY: 10.0, ATOM_FREQUENCY: 10.0}
        
        # attack_power = 40 * 30 = 1200
        # defense_power = 10 * 10 + 1 = 101
        # stun_chance = 1200 / 101 = 11.88
        
        # Test with ironclad universe
        result = self.registry.execute_payload("emp", caster_dna, target_dna, universe="ironclad")
        
        assert result["effect_type"] == "stun"
        assert result["chance"] == pytest.approx(0.1188, abs=1e-4)

    def test_phase_jump_distance(self):
        """
        Vasari Phase Ship (Energy 40, Frequency 35, Aether 15)
        Distance = (40 * 35 * 0.5) + (15 * 0.2) = 700 + 3 = 703
        """
        caster_dna = {ATOM_ENERGY: 40.0, ATOM_FREQUENCY: 35.0, ATOM_AETHER: 15.0}
        
        # Test with generic universe
        result = self.registry.execute_payload("phase_jump", caster_dna)
        
        assert result["effect_type"] == "teleport"
        assert result["distance"] == 703.0

    def test_phasejump_keyword_support(self):
        """
        Verify that 'phasejump' without a space is correctly identified.
        """
        from src.core.ability_synthesizer import generate_ability_lens, classify_ability_payload
        
        ability_data = {
            "id": "PhaseJump",
            "name": "PhaseJump",
            "description": "Jump through phase space."
        }
        
        lens = generate_ability_lens(ability_data)
        payload_type = classify_ability_payload(ability_data)
        
        assert lens.get(ATOM_FREQUENCY, 0) > 0
        assert payload_type == "phase_jump"

    def test_universe_scoping_isolation(self):
        """
        Verify that payloads registered in one universe don't bleed into another 
        unless they are in generic.
        """
        def custom_execute(caster, target, context):
            return {"effect_type": "custom", "msg": "custom_universe"}
            
        self.registry.register_payload("custom_ability", "utility", custom_execute, universe="custom_uni")
        
        # Should find it in custom_uni
        res_ok = self.registry.execute_payload("custom_ability", {}, universe="custom_uni")
        assert res_ok["effect_type"] == "custom"
        
        # Should NOT find it in soase
        res_fail = self.registry.execute_payload("custom_ability", {}, universe="soase")
        assert res_fail["effect_type"] == "none"
        assert "Payload not found" in res_fail["description"]

    def test_payload_not_found(self):
        result = self.registry.execute_payload("invalid_ability", {}, universe="soase")
        assert result["effect_type"] == "none"
        assert "Payload not found" in result["description"]
        assert "universe soase" in result["description"]

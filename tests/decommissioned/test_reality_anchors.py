import pytest
from src.core.reality_anchor import RealityAnchor
from src.core.universe_physics import PhysicsProfile
from src.combat.tactical_grid import TacticalGrid
from src.core.elemental_signature import ATOM_AETHER, ATOM_MASS

class TestRealityAnchors:
    
    @pytest.fixture(autouse=True)
    def setup(self):
        # Base Universe: Standard Physics (1.0)
        self.global_profile = PhysicsProfile(
            description="Standard Reality",
            multipliers={ATOM_AETHER: 1.0, ATOM_MASS: 1.0}
        )
        self.grid = TacticalGrid(20, 20)

    def test_anchor_logic(self):
        """Test basic anchor range and effect application."""
        # Create a "Null Field" Anchor (Aether x0.0)
        null_profile = PhysicsProfile(multipliers={ATOM_AETHER: 0.0})
        anchor = RealityAnchor("Necron Pylon", null_profile, radius=5, x=10, y=10)
        
        # Check range (10,10 is center)
        assert anchor.is_in_range(10, 10)
        assert anchor.is_in_range(14, 10) # dx=4 <= 5
        assert not anchor.is_in_range(16, 10) # dx=6 > 5
        
        # Check effect blending
        # Global (1.0) * Anchor (0.0) = 0.0
        blended = anchor.apply_anchor_effect(self.global_profile)
        assert blended.multipliers[ATOM_AETHER] == 0.0
        assert blended.multipliers[ATOM_MASS] == 1.0 # Unchanged

    def test_grid_integration(self):
        """Test retrieving modified physics from the grid."""
        # 1. Register Anchor: Warp Rift (Aether x2.0) at (5,5) radius 3
        rift_profile = PhysicsProfile(multipliers={ATOM_AETHER: 2.0})
        rift = RealityAnchor("Warp Rift", rift_profile, radius=3, x=5, y=5)
        self.grid.register_anchor(rift)
        
        # 2. Check at center (5,5) -> Should be x2.0
        p_center = self.grid.get_physics_at_coordinates(5, 5, self.global_profile)
        assert p_center.multipliers[ATOM_AETHER] == 2.0
        
        # 3. Check outside range (0,0) -> Should be x1.0
        p_outside = self.grid.get_physics_at_coordinates(0, 0, self.global_profile)
        assert p_outside.multipliers[ATOM_AETHER] == 1.0

    def test_compound_anchors(self):
        """Test overlapping fields (Null Field + Warp Rift)."""
        # Pylon (x0) at (10,10) r5
        null_profile = PhysicsProfile(multipliers={ATOM_AETHER: 0.0})
        pylon = RealityAnchor("Pylon", null_profile, radius=5, x=10, y=10)
        
        # Rift (x2) at (12,10) r5 (Overlaps pylon)
        rift_profile = PhysicsProfile(multipliers={ATOM_AETHER: 2.0})
        rift = RealityAnchor("Rift", rift_profile, radius=5, x=12, y=10)
        
        self.grid.register_anchor(pylon)
        self.grid.register_anchor(rift)
        
        # At (11, 10) -> Inside BOTH.
        # Math: 1.0 (Global) * 0.0 (Pylon) * 2.0 (Rift) = 0.0
        # Null field should dominate simply by math.
        p_overlap = self.grid.get_physics_at_coordinates(11, 10, self.global_profile)
        assert p_overlap.multipliers[ATOM_AETHER] == 0.0

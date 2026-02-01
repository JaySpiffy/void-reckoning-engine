import pytest
from src.analysis.weapon_analyzer import WeaponAnalyzer, WeaponRole

def test_weapon_classification():
    """Verify standard 40k weapons get correct roles."""
    
    # 1. Bolter (S4, AP0, D1) -> Anti-Infantry
    bolter = {"S": 4, "AP": 0, "D": 1, "Range": 24, "Type": "Rapid Fire 1"}
    assert WeaponAnalyzer.classify_weapon(bolter) == WeaponRole.ANTI_INFANTRY.value
    
    # 2. Lascannon (S9, AP-3, D3.5) -> Anti-Tank
    lascannon = {"S": 9, "AP": -3, "D": 3.5, "Range": 48, "Type": "Heavy 1"}
    assert WeaponAnalyzer.classify_weapon(lascannon) == WeaponRole.ANTI_TANK.value
    
    # 3. Flamer (S4, AP0, D1, Blast implied/auto-hit) -> Anti-Infantry
    flamer = {"S": 4, "AP": 0, "D": 1, "Range": 12, "Type": "Assault D6 Blast"} # "Blast" keyword in type
    assert WeaponAnalyzer.classify_weapon(flamer) == WeaponRole.ANTI_INFANTRY.value
    
    # 4. Power Fist (S8, AP-3, D2, Melee) -> Melee Duelist
    power_fist = {"S": 8, "AP": -3, "D": 2, "Range": 0, "Type": "Melee"}
    assert WeaponAnalyzer.classify_weapon(power_fist) == WeaponRole.MELEE.value
    
    # 5. Volcano Cannon (S16, AP-5, D6) -> Titan Killer
    volcano = {"S": 16, "AP": -5, "D": 10, "Range": 120, "Type": "Heavy D3", "Macro": True}
    assert WeaponAnalyzer.classify_weapon(volcano) == WeaponRole.TITAN_KILLER.value
    
    # 6. Autocannon (S7, AP-1, D2) -> Monster Hunter / Light AT
    autocannon = {"S": 7, "AP": -1, "D": 2, "Range": 48, "Type": "Heavy 2"}
    # S7 is usually Monster Hunter in my logic (5 <= S <= 7, D >= 2)
    assert WeaponAnalyzer.classify_weapon(autocannon) == WeaponRole.MONSTER_HUNTER.value

def test_efficiency_score():
    """Verify efficiency math."""
    # Lascannon vs Vehicle (T7, 3+)
    # S9 vs T7 -> 3+ to wound (0.66)
    # AP-3 vs 3+ -> 6+ to save (eff save 6+). Fail on 1-5 (5/6 = 0.83)
    # D 3.5
    # Score = 0.66 * 0.83 * 3.5 = ~1.9 * 10 = ~19
    
    stats = {"S": 9, "AP": -3, "D": 3.5}
    score = WeaponAnalyzer.calculate_efficiency_score(stats, "VEHICLE")
    assert score > 15
    assert score < 25
    
    # Bolter vs Vehicle
    # S4 vs T7 -> 5+ to wound (0.33)
    # AP0 vs 3+ -> 3+ to save. Fail on 1-2 (2/6 = 0.33)
    # D1
    # Score = 0.33 * 0.33 * 1 = ~0.11 * 10 = ~1.1
    
    stats2 = {"S": 4, "AP": 0, "D": 1}
    score2 = WeaponAnalyzer.calculate_efficiency_score(stats2, "VEHICLE")
    assert score2 < 3.0

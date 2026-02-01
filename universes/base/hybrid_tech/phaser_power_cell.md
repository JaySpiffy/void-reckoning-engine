# Hybrid Tech: Phaser Power Cell
Cross-universe adaptation of Federation phaser technology for Imperial power systems.

## Description
By analyzing the modular nature of phaser energy capacitors, Imperial engineers have developed a high-density power cell that can be retrofitted into Lasgun and Multilaser arrays, significantly increasing shot discharge speed and energy efficiency.

## Adaptation Requirements
- **Universes**: Star Trek, Warhammer 40k
- **Prerequisites**:
  - `star_trek`: `hand_phaser_tech`
  - `warhammer40k`: `lasgun_standardization`
- **Intel Cost**: 2500 IP
- **Research Turns**: 3

## Strategic Benefits
- +10% Damage to Las-weapons
- -5% Requisition cost for Infantry units using Las-technology
- Unlocks: `hybrid_st_wh40k_pulse_las_carbine`

PARSER_DATA
```json
{
  "tech_id": "hybrid_st_wh40k_phaser_power_cell",
  "name": "Phaser Power Cell",
  "universes": ["star_trek", "warhammer40k"],
  "prerequisites": {
    "star_trek": ["hand_phaser_tech"],
    "warhammer40k": ["lasgun_standardization"]
  },
  "intel_cost": 2500,
  "research_turns": 3,
  "benefits": [
    {"type": "stat_mod", "target": "las_damage", "value": 0.10},
    {"type": "cost_mod", "target": "las_infantry", "value": -0.05}
  ],
  "unlocks": ["hybrid_st_wh40k_pulse_las_carbine"]
}
```

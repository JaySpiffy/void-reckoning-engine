# Syncretic Tech: Ferro-Hallowed Bulwark

Intra-universe adaptation combining Steel-Bound Syndicate metallurgy with Templars of the Flux protective rites.

## Description

By reinforcing the Steel-Bound Syndicate's high-density ceramite alloys with the Templars of the Flux' psycho-reactive hallowed script, this technology creates a defensive barrier that is physically impenetrable and spiritually resilient.

## Adaptation Requirements

- **Universe**: Void Reckoning
- **Prerequisites**:
  - `SteelBound_Syndicate`: `Tech_SteelBound_Syndicate_Heavy Armor`
  - `Templars_of_the_Flux`: `Tech_Templars_of_the_Flux_Basic Doctrine`
- **Intel Cost**: 3500 IP
- **Research Turns**: 5

## Strategic Benefits

- +20% Defense to Fortifications
- +10 Morale for garrisoned units
- Unlocks: `Building_Vanguard_Zealot_Shrine_Bastion`

PARSER_DATA

```json
{
  "tech_id": "syncretic_iv_zl_hallowed_bulwark",
  "name": "Ferro-Hallowed Bulwark",
  "universes": ["void_reckoning"],
  "prerequisites": {
    "void_reckoning": [
      "Tech_SteelBound_Syndicate_Heavy Armor",
      "Tech_Templars_of_the_Flux_Basic Doctrine"
    ]
  },
  "intel_cost": 3500,
  "research_turns": 5,
  "benefits": [
    {"type": "stat_mod", "target": "fortification_defense", "value": 0.20},
    {"type": "stat_mod", "target": "garrison_morale", "value": 10}
  ],
  "unlocks": ["Building_Vanguard_Zealot_Shrine_Bastion"]
}
```

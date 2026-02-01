# Faction Quirks Guide

This document details unique behaviors (quirks) implemented for factions in the **eternal_crusade** universe. These quirks are defined in the AI personality module and influence strategic, tactical, and economic decisions.

---

## eternal_crusade Universe

*These quirks capture the "Grimdark" nature of eternal_crusade warfare.*

| Faction               | Primary Quirk    | Effect                                                 | Implementation                                   |
|-----------------------|------------------|--------------------------------------------------------|--------------------------------------------------|
| **Zealot_Legions**    | Threat Affinity  | Increased aggression when enemies are nearby.          | `StrategicAI.process_faction_strategy`           |
| **Hive_Swarm**        | Biomass Hunger   | Massive expansion priority and 1.5x navy recruitment.  | `StrategicAI.calculate_expansion_target_score`   |
| **Ascended_Order**    | Elite Caster     | +20% research speed and values elite unit lives.       | `ResearchManager.calculate_bonus`                |
| **Iron_Vanguard**     | Attrition        | Stubborn retreat thresholds and 1.2x army recruitment | `StrategicAI.calculate_dynamic_retreat_threshold`|
| **Void_Corsairs**     | Raiding          | 50% casualty plunder and high evasion.                 | `CombatManager.calculate_plunder`                |
| **Cyber_Synod**       | Assimilation     | Tech-adaptive logic with on-kill assimilation effects | `FactionPersonality.quirks`                      |
| **Rift_Daemons**      | Shock Assault    | Never retreats and 2.0x base aggression.               | `StrategicAI.process_faction_strategy`           |
| **Scavenger_Clans**   | Scavenging       | 80% casualty plunder but avoids fair fights.           | `CombatManager.calculate_plunder`                |
| **Ancient_Guardians** | Tech Advantage   | Ancient tech modifiers and isolationist AI.           | `FactionPersonality.quirks`                      |

---

## Configuration & Customization

The eternal_crusade universe loads its personality data from an `ai_personalities.py` file located in its root directory:

- `universes/eternal_crusade/ai_personalities.py`

Developers can add new quirks by extending the base `FactionPersonality` class and registering their custom logic in the universe's configuration.

## Tech Doctrine Tags

*Controls how factions interact with alien/stolen technology.*

| Doctrine      | Behavior                        | Effect                                  |
|---------------|---------------------------------|-----------------------------------------|
| **RADICAL**   | Embraces all alien tech         | +10% research speed for stolen/salvaged |
| **PURITAN**   | Rejects alien tech              | +5 morale for destroying captured tech  |
| **PRAGMATIC** | Uses tech selectively           | Only if strategic value > 3.0           |
| **XENOPHOBIC**| Never uses alien tech           | -20 diplomacy with tech sharers         |
| **ADAPTIVE**  | Uses allied tech, rejects enemy | +5% intel gain from alien tech combat   |

### Examples

- **Zealot_Legions (eternal_crusade)**: PURITAN - Rejects alien tech, favors fanatical melee
- **Void_Corsairs (eternal_crusade)**: ADAPTIVE - Loots and uses anything that provides an edge
- **Cyber_Synod (eternal_crusade)**: ADAPTIVE - Assimilates enemy technology efficiently
- **Hive_Swarm (eternal_crusade)**: XENOPHOBIC - Consumes technology only as raw biomass

---

## Future Expansion

When additional universes are added, faction quirks for those universes will be documented here with their unique behaviors and implementation details.

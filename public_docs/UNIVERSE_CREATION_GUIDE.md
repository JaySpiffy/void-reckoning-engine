# Universe Creation Guide

This guide provides a comprehensive walkthrough for developers wishing to add new science fiction universes to the Multi-Universe Grand Strategy Campaign Simulator.

## Introduction

The simulation engine is designed to be **universe-agnostic**. All setting-specific content—factions, units, technologies, and even certain combat rules—resides within the `universes/` directory. By following this guide, you can create a fully functional new universe (e.g., "Dawn of Man", "The Outer Rim", etc.) that integrates with the engine's core strategic layer.

## Universe Directory Structure

All universes must be located in `universes/<universe_name>/`. Here is the required layout:

```text
universes/custom_universe/
├── config.json               # Required: Universe metadata and mappings
├── game_data.json            # Required: Planet types and terrain
├── diplomacy_data.json       # Required: Default relations
├── factions/                 # Required: Faction subdirectories
│   ├── Solar_Hegemony/
│   ├── Ancient_Guardians/
│   └── faction_registry.json
├── infrastructure/           # Required: Buildings and upgrades
├── technology/               # Required: Research trees
├── combat_phases.py          # Optional: Custom combat logic (e.g., Special Powers)
├── ai_personalities.py       # Optional: Behavioral overrides
└── combat_utils.py           # Optional: Custom combat math
```

## Universe Configuration (config.json)

The `config.json` file is the heart of your universe. It tells the `UniverseLoader` where everything is.

```json
{
  "name": "custom_universe",
  "version": "1.0.0",
  "factions": ["Solar_Hegemony", "Ancient_Guardians"],
  "factions_dir": "factions",
  "infrastructure_dir": "infrastructure",
  "technology_dir": "technology",
  "combat_rules": "combat_phases.py",
  "ai_personalities": "ai_personalities.py",
  "metadata": {
    "era": "The Great Expansion",
    "description": "A vast, multi-star system conflict..."
  }
}
```

## Universe Configuration Reference

The `config.json` file must adhere to the schema in `universes/base/universe_config_schema.json`.

### Schema Fields

| Field | Type | Required | Description | Default |
| :--- | :--- | :--- | :--- | :--- |
| `name` | string | **Yes** | Canonical unique name of the universe. | N/A |
| `version` | string | **Yes** | Version string for the universe data. | N/A |
| `factions` | array | **Yes** | List of faction folder names to load. | N/A |
| `description`| string | No | High-level description of the universe. | N/A |
| `factions_dir`| string | No | Subdirectory containing faction folders. | `"factions"` |
| `infrastructure_dir`| string | No | Subdirectory containing building data. | `"infrastructure"` |
| `technology_dir`| string | No | Subdirectory containing tech tree data. | `"technology"` |
| `game_data` | string | No | Path to planet/terrain data JSON. | `"game_data.json"` |
| `diplomacy_data`| string | No | Path to initial relations JSON. | `"diplomacy_data.json"` |
| `combat_rules`| str\|obj | No | Custom combat logic (Path or Module Object). | N/A |
| `ai_personalities`| str\|obj | No | Behavioral overrides (Path or Module Object). | N/A |
| `metadata` | object | No | Custom key-value pairs for universe data. | `{}` |

### Portal Configuration (portal_config.json)

The `portal_config.json` determines how your universe connects to others in the Multiverse.

```json
{
  "enable_portals": true,
  "portals": [
    {
      "portal_id": "nexus_gateway",
      "source_coords": [50, 50],
      "dest_universe": "another_universe",
      "dest_coords": [10, 10],
      "placement_strategy": "galactic_core",
      "metadata": {
        "name": "The Great Rift"
      }
    }
  ],
  "portal_pairs": [
    {
      "universe_a": "custom_universe",
      "universe_b": "another_universe",
      "portal_id": "nexus_gateway"
    }
  ]
}
```

### Portal Linkage

The `portal_pairs` section explicitly defines the bidirectional link between two universes. This is required for the Multi-Universe Runner to validate that a portal in Universe A has a corresponding exit in Universe B.

- `universe_a`: The name of the first universe (usually the one this config belongs to).
- `universe_b`: The name of the connected universe.
- `portal_id`: Must match the `portal_id` defined in the `portals` array.

#### Placement Strategies

- **`nearest_system`**: Spawns the portal at the system geographically closest to `source_coords`.
- **`galactic_core`**: Spawns at the center of the galaxy (50, 50).
- **`border_region`**: Spawns at a random system near the galactic rim (<25 or >75).
- **`exact_coords`**: Forces spawn at exact coordinates (may be in deep space if no system is nearby).

### Minimal Valid Configuration

```json
{
  "name": "minimal_universe",
  "version": "1.0.0",
  "factions": ["Faction_A", "Faction_B"]
}
```

### Essential Files and Folders

To pass validation, your universe directory must contain:

1. `config.json`: Metadata and faction list.
2. `game_data.json`: Planet classes and terrain modifiers.
3. `diplomacy_data.json`: Faction relationship matrix.
4. `factions/`: Directory containing subfolders for each listed faction.
5. `infrastructure/`: Directory containing building definitions and registries.
6. `technology/`: Directory containing research trees and registries.

## Game Data Definition (game_data.json)

Define the physical properties of your universe, such as planet classes and terrain.

### Planet Classes

Planets are categorized by classes that influence resource production and defense.

- `req_mod`: Multiplier for Requisition/Resource income.
- `def_mod`: Multiplier for defensive units.
- `slots`: Number of building slots available.

### Terrain Multipliers

Define how different terrain types (Urban, Forest, Desert) affect combat efficacy.

## Faction Data Structure

Each faction requires a dedicated folder containing its unit definitions.

1. **Unit Files**: Markdown files following the `PARSER_DATA_SPEC.md` format.
2. **Space_Units/**: Capital ships, escorts, and starfighters.
3. **Land_Units/**: Infantry, vehicles, and specialized squads.
4. **Registries**: `weapon_registry.json` and `ability_registry.json` list all available gear and traits for that faction.

## Infrastructure and Technology

- **Buildings**: Defined in `infrastructure/<faction_name>/`. Buildings can provide income, boost defense, or unlock specific units.
- **Tech Trees**: Defined in `technology/`. Techs use a prerequisite system to gate powerful units and abilities.

## Custom Combat Phases

If your universe has unique mechanics (like Aetheric powers or Shield Modulation), you must implement a custom combat rules class.

1. Create `combat_phases.py`.
2. Inherit from `universes.base.combat_rules.CombatRulesBase`.
3. Implement `register_phases()` to inject your custom logic into the battle loop.

```python
from universes.base.combat_rules import CombatRulesBase

class CustomCombatRules(CombatRulesBase):
    def register_phases(self):
        phases = super().register_phases()
        phases.append({"name": "Special_Phase", "handler": self.resolve_special_effect, "priority": 5})
        return phases
```

## AI Personality Customization

Customize how factions in your universe think by creating `ai_personalities.py`.

- **aggression**: Bias toward war and conquest.
- **expansion_bias**: Priority on taking new systems.
- **combat_doctrine**: Preference for `CHARGE`, `KITE`, or `DEFEND`.

## Integration Checklist

- [ ] Create directory `universes/<name>/`.
- [ ] Implement `config.json`.
- [ ] Define planet classes in `game_data.json`.
- [ ] Create at least 3 factions with complete unit rosters.
- [ ] Define building trees in `infrastructure/`.
- [ ] Define technology trees in `technology/`.
- [ ] Build registries: `python run.py validate --universe <name> --rebuild-registries`.
- [ ] Run a test campaign: `python run.py campaign --universe <name> --quick`.
- [ ] Validate blueprints: `python tools/validate_blueprints.py --universe <name>`.

## Blueprint System

The Blueprint System provides a library of base templates for units and components. This enables a template-based architecture where thousands of units can be generated from a handful of optimized templates, reducing memory usage and ensuring consistency across the universe.

### Directory Structure

```text
universes/custom_universe/
├── blueprints/               # Optional: Universe-specific templates
│   ├── interceptor_template.json
│   └── cruiser_overrides.json
...
```

### Blueprint Format

Blueprints are JSON files defining `base_stats` (legacy) and `universal_stats` (stat multipliers).

```json
{
  "id": "base_ship_cruiser",
  "name": "Base Cruiser Ship",
  "type": "ship",
  "category": "cruiser",
  "base_stats": {
    "hp": 1500,
    "armor": 80,
    "damage": 60,
    "shield": 800
  },
  "universal_stats": {
    "hull_structural_integrity": 1.5,
    "weapon_kinetic_damage": 1.2,
    "armor_kinetic_resistance": 1.2
  },
  "default_traits": ["Crew Experience I"],
  "cost": 1200
}
```

### Inheritance and Overrides

1. **Base Blueprints**: Defined in `universes/base/blueprints/`. Available to all universes.
2. **Universe Overrides**: Defined in `universes/<universe_name>/blueprints/`.
   - If an `id` matches a base blueprint, it is merged.
   - `base_stats` values in the universe file replace base values.
   - `universal_stats` values are **multiplied** with base values.
   - `default_traits` are concatenated.

### Using Blueprints in Unit Files

In your unit's markdown file, reference a blueprint ID in the `PARSER_DATA` block. The unit will inherit all stats and traits from the blueprint unless explicitly overridden in the markdown.

```markdown
<!-- PARSER_DATA
blueprint_id: base_ship_cruiser
name: Hegemony Strike Cruiser
hp: 1800  # Overrides blueprint base_stats.hp
-->
```

## Memory Optimization with Blueprints

By using blueprints, the engine only stores the template once in memory. Individual units only track their `blueprint_id` and unique `traits`. This architecture is optimized for the high-cache performance of modern CPUs, keeping frequently accessed template data in L3 cache while scaling to massive unit counts.

| Component | Memory Strategy |
| :--- | :--- |
| **Blueprints** | Cached in Singleton Registry |
| **Traits** | Cached in Singleton Registry |
| **Unit Instances** | Track Delta + References only |

The simulation supports **Hybrid Content** where unit definitions can be provided in multiple formats (e.g., XML and Markdown) simultaneously. This is particularly useful for universes that leverage existing external source data.

### How it Works

1. **Format Detection**: The `UniverseLoader` automatically scans faction subdirectories for `.md` and other supported formatting files.
2. **Unified Parsing**: The `UnitFactory` routes files to the appropriate parser based on extension.
3. **Registry Merging**: When building weapon/ability registries, data from all formats is merged.
4. **Precedence**: In cases of ID conflict within the same faction, specific format definitions can be prioritized in the configuration.

### Configuration

To explicitly enable external data support features in the UI and logs, add the following to your `config.json`:

```json
{
  "metadata": {
    "supports_external_data": true
  }
}
```

### Validation Requirements

Mixed-format universes must pass additional checks:

- External units must have corresponding component definitions.
- Markdown-sourced units must contain valid `PARSER_DATA` blocks.
- Registry entries will include a `source_format` field (e.g., "external" or "markdown").

## Testing Your Universe

Use the built-in validation tool to find errors in your unit files or config:

```bash
python run.py validate --universe <your_universe>
```

Common issues include missing weapon stats, cyclic tech dependencies, or invalid planet references.

---
*Generated by the Antigravity Multi-Universe Team.*

## External Mod Integration

For universes based on external data sources, the engine supports direct parsing of standard script files.

### Features

- **Components**: Parsed as Weapons and Abilities.
- **Technologies**: Extracted with prerequisites, costs, and unlock chains.
- **Buildings**: Converted to Infrastructure registry with effects mapped to simulation modifiers.
- **Unlock Mapping**: Automatically links technologies to the ships and components they unlock.

### How to Enable

1. Place your external data files in an accessible directory (e.g. `examples_only/custom_data/common`).
2. Update `src/utils/registry_builder.py` to point to your data path for your specific universe.
3. Run `python run.py validate --universe <name> --rebuild-registries`.

### File Support

- Component templates: Weapons and Utilities.
- Technology files: Research trees.
- Building files: Planetary infrastructure.
- Unit size files: Ship hulls and class definitions.

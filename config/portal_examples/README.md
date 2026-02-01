# Portal Configuration Examples

This directory contains examples for configuring the Multiverse Portal Infrastructure.

## Examples

- `simple_two_universe.json`: A basic 1-to-1 portal connection using the `galactic_core` placement strategy.
- `multi_portal_network.json`: A more complex configuration for a 'hub' universe connecting to multiple other universes.
- `strategic_placement.json`: Showcases different `placement_strategy` options.

## Usage

To use an example, copy its content into your universe's `portal_config.json` file:

```bash
cp config/portal_examples/simple_two_universe.json universes/my_universe/portal_config.json
```

Ensure that the target universe (`dest_universe`) also has a matching portal definition with the same `portal_id`.

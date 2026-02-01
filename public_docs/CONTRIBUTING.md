# Contributing to the Multi-Universe Strategy Engine

This project has transitioned to a **Multi-Universe architecture**. Contributions should distinguish between core engine logic (universe-agnostic) and universe-specific content.

## Development Workflow

### Adding a New Universe
1. Create a new directory under `universes/<your_universe>/`.
2. Follow the directory structure and schema requirements outlined in the [Universe Creation Guide](UNIVERSE_CREATION_GUIDE.md).
3. Register your universe in `universes/base/universe_loader.py` (if manual registration is required) or ensure it follows discovery conventions.
4. Validate your data: `python run.py validate --universe <your_universe>`.

### Modifying Core Engine Logic
- **Location**: `src/` (e.g., `src/managers/`, `src/combat/`).
- **Rule**: Core logic must remain **universe-agnostic**. Do not hardcode references to Warhammer 40k or Star Trek in the `src/` directory.
- **Abstraction**: Use the abstract base classes in `universes/base/` to interface with universe-specific content.

### Adding Universe Content (Units, Tech, Buildings)
1. Navigate to `universes/<universe_name>/factions/`.
2. Update the relevant Markdown files following the `PARSER_DATA_SPEC.md` format.
3. Rebuild registries: `python run.py validate --universe <universe_name> --rebuild-registries`.

## Coding Standards
- **Decoupling**: Always check if a feature should be a global engine change or a universe-specific rule implementation.
- **Path Handling**: Never use hardcoded paths. Use the path constants defined in `src/core/config.py`.
- **Type Hinting**: Enrich all new functions with Python type hints for clarity across the complex simulation state.
- **Documentation**: If you change the universe interface, you **must** update the `UNIVERSE_CREATION_GUIDE.md`.

## Testing Guidelines
- **Core Changes**: Must pass `pytest` and not break any existing universes.
- **Universe Changes**: Must pass validation and at least one full `--quick` campaign run.
- **Parallelism**: Test multi-universe execution to ensure no shared-state side effects: `python run.py multi-universe`.

## Git Workflow
- Commit data changes (universe content) separately from engine changes.
- Use descriptive tags: `[Engine]`, `[Universe-WH40k]`, `[Docs]`.

---
*Reference: [Project Structure](../PROJECT_STRUCTURE.md) | [Testing Guide](../TESTING.md)*

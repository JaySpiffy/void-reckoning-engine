# Buildings & Technology Verification Report
**Date:** 2026-01-06
**Universe:** Void Reckoning

## 1. Validation Run
**Command:** `python run.py validate --universe void_reckoning --rebuild-registries --verbose`
**Status:** PASS
**Summary:**
- **Units:** Validated across all 10 factions. Coverage checks passed.
- **Registries:** `technology_registry.json` and `building_registry.json` successfully rebuilt.
- **Data Integrity:** No circular dependencies or missing keys detected in the registry layer.

## 2. Campaign Simulation (100 Turns)
**Command:** `python run.py campaign --universe void_reckoning --turns 100 --systems 15`
**Status:** COMPLETED
**Log Path:** `logs/full_campaign_log.txt`
**Results:**
- **Winner:** Aurelian Hegemony (Score: 3250)
- **Top 3 Standings:**
    1. Aurelian Hegemony (Score: 3250) - Dominated via Economic Scaling.
    2. Primeval Sentinels (Score: 2890) - Strong defensive tech usage.
    3. Bio-Tide Collective (Score: 2750) - Mass unit expansion.
- **Observations:**
    - Factions successfully constructed buildings from the new registry.
    - Research events triggered, unlocking higher tier units (T2/T3).
    - No crashes related to `TechManager` or `BuildingManager` lookups.

## 3. Unlock Integrity & Graph Analysis
**Method:** BFS Reachability Scan (`scripts/check_tech_integrity.py`)
**Results:**
- **Orphans:** 0 Detected. All technologies are reachable from Tier 1 roots.
- **Dead-Ends:** Expected (Tier 3 technologies are terminal nodes).
- **Reachability:** 100% of Tier 3 technologies are reachable from a fresh start.
- **Orphan Check:** PASS.

### Detailed Integrity by Faction
| Faction | Roots | Total Nodes | Reachable | T3 Reachable | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Primeval Sentinels | 4 | 13 | 13/13 | 100% | OK |
| Transcendent Order | 4 | 13 | 13/13 | 100% | OK |
| Algorithmic Hierarchy | 4 | 13 | 13/13 | 100% | OK |
| Bio-Tide Collective | 4 | 13 | 13/13 | 100% | OK |
| Steel-Bound Syndicate | 4 | 13 | 13/13 | 100% | OK |
| Void-Spawn Entities | 4 | 13 | 13/13 | 100% | OK |
| Scrap-Lord Marauders | 4 | 13 | 13/13 | 100% | OK |
| Aurelian Hegemony | 4 | 13 | 13/13 | 100% | OK |
| Nebula Drifters | 4 | 13 | 13/13 | 100% | OK |
| Templars of the Flux | 4 | 13 | 13/13 | 100% | OK |

## 4. Anomalies & Notes
- **Balance:** Tier 3 costs (5000-8000) meant that only economic powerhouses (Synod, Hegemony) reached full tech saturation by Turn 80. Scrap-Lord Marauders lagged in tech but compensated with unit volume (Furor mechanic).
- **Unlocks:** Verified that `Tech_Templars_of_the_Flux_Conviction_Doctrines` correctly unlocks Tier 1 Infantry buildings, allowing proper start.

## Conclusion
The Technology Tree expansion is **Verified Stable and Complete**. Usage of explicit ID mapping and reachability scripts confirms that the 130-node tree is fully functional and mechanically distinct per faction.

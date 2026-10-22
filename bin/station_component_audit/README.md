# Station component audit

Read-only audit of active FL_MOD archetypes and static placements in 78 systems.
No runtime model or configuration file was changed. Freelancer was running.
Internal names are used to identify custom candidates; that convention alone
is not proof of provenance. Primary candidates below have explicit custom names
and one render LOD. Existing industrial/trading model LODs remain installed.

| Model | Vertices | Trial LOD1 | Trial LOD2 | Groups before/after | Static uses | or_hq / ku_tgk |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| space_control_tower.3db | 2425 | 1541 | 1142 | 11 / 5 / 5 | 388 | 26 / 2 |
| space_medium_control_tower.3db | 1435 | 952 | 660 | 11 / 4 / 4 | 228 | 7 / 6 |
| space_sml_control_tower.3db | 434 | 335 | 327 | 6 / 4 / 4 | 304 | 14 / 9 |
| space_production.3db | 6997 | 4623 | 2876 | 11 / 8 / 8 | 52 | 0 / 0 |
| space_large_production.3db | 6412 | 4679 | 2918 | 11 / 8 / 8 | 36 | 0 / 0 |
| shipyard_small.3db | 2956 | 1702 | 1000 | 5 / 5 / 5 | 12 | 0 / 0 |
| shipyard_medium.3db | 3099 | 1732 | 1022 | 5 / 5 / 5 | 41 | 0 / 2 |
| space_domea.3db | 1161 | 710 | 369 | 7 / 7 / 7 | 92 | 36 / 0 |
| space_small_control_block.3db | 792 | 492 | 424 | 6 / 6 / 6 | 134 | 1 / 7 |
| space_windows.3db | 972 | 618 | 448 | 9 / 3 / 3 | 54 | 0 / 0 |
| space_long_large_arch.3db | 1977 | 1397 | 1366 | 8 / 3 / 3 | 28 | 0 / 0 |

Trial counts come from attribute-aware simplification in memory, including
material-island retention and thin-piece protection. They are feasibility numbers,
not accepted production LODs: silhouette/texture previews, opacity/material checks,
reference generation and transition tests are still required before installation.
Large and medium control tower materials were checked: all are opaque DcDt, so
combining equal groups is a useful additional opportunity (11 to 5 / 4 groups).

Suggested order:

1. Large and medium control towers: frequent, currently only one LOD; both geometry and material groups can be reduced.
2. Production and large-production modules: highest individual geometry cost among these ordinary station parts.
3. Medium/small shipyards and dome A/B: useful reduction with repeated placements.
4. Small control block, windows and long arch. Small tower is frequent but already comparatively cheap.

Geometry findings:

- space_medium_control_tower.3db: four thin triangles on top/bottom horizontal panels have geometric normals opposite to all three stored normals. They are not paired reverse faces. Stored normals are +Y/-Y and match the panel orientation, so inspect/fix triangle winding rather than indiscriminately replacing normals.
- space_long_large_arch.3db: one zero-length normal is used at two triangle corners. A local normal repair can remove this invalid input; sharp-edge/smoothing intent should be respected.
- dyson_box_detail_fixed.3db: 755 exact duplicate same-material, same-winding triangles out of 6056 (12.47%). Opposite winding copies are excluded by the diagnostic. Material detailmap_dyson_skin04 resolves to DcDtBt. Removing verified duplicates and compacting vertices is a separate opportunity without deliberate geometric simplification; it should be previewed and checked for material behavior.
- space_production, space_large_production and shipyard_medium each have two zero padding bytes after mesh data. This is ordinary alignment, not a damaged mesh.
- space_control_tower has no zero-area or exact duplicate triangles and no wholly opposed-normal triangles in this check. Its cost does not by itself imply a model defect.

Cheap high-count parts:

- space_girder / space_girdera are only 60 vertices each; adding more LODs has limited geometry benefit. Draw-call/attachment overhead is the more relevant concern.
- Repaired space_panel variants are 240 vertices / 80 triangles; preserve hard shading before attempting further vertex welding.

Method and limitations:

Counts use the universe files listed by Freelancer.ini, then static [Object]
placements and object/default loadouts. Includes equipment attachments; excludes
mission/encounter spawns and camera visibility. A global placement count is not
a count of simultaneous visible instances or a GPU timing measurement.
Main geometry is read from VMeshRef and exporter-compatible CRC references.
Zero normals, nonfinite data, zero-area triangles, same-winding exact duplicates
and wholly opposed normals are diagnostic flags; intended smoothing/back faces
must be distinguished before repair. These tests do not prove a mesh is otherwise
perfect. Normal retail records and custom-name heuristic errors may remain in the
full inventory; use the verified shortlist rather than applying a global rewrite.

audit.json includes all 829 referenced solar model records and per-system counts.
simplification_trials.json records the eleven dry-run results. Four missing model
paths were recorded in the audit; no game file was altered to address them.

Reproduce: python tools/audit_station_components.py from the workspace root.

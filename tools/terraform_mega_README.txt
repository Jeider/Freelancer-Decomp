OR_HQ terraformer optimization, 2026-11-13

Installed one shared tfm_or_hq_body CMP/SUR for all three terraformers.
Each station: 185 static cargo attachments plus three tank carriers baked into
one body; 713 near material groups -> 43, 33,243 near triangles, seven internal
mesh parts preserving original LOD cohorts. Seven solar objects -> four:
body, original planet sphere, two original animated ring carriers.
External terraform FX objects are unchanged. HpLaser01 is transferred from
the attached laser to the body at the same world transform.

The two ring carriers per station retain polygon2.cmp, planetform_rings,
their child hardpoints and the_barrel_animation (Sc_rotate barrel). No animated
carrier was flattened. Only the nonanimated tank carriers' Rev is evaluated at
rest. All three instances share the body model; no station-specific mesh copies.

Pythonlancer: original terraforming.py saved byte-for-byte as terraformingOriginal.py.
Existing template classes remain intact. TerraformingTwoOrHQ is appended and
selected only by the three OrdHQTerraform classes in or_hq_static.py.
Pythonlancer generation was NOT run. No engine binary was changed.
Current static system snapshot: or_hqTerraformOriginal.ini, retaining Valensia fixes.

Validation: exact per-LOD material/triangle/vertex records, exact source terminal
SUR leaf faces/points, identical relative layouts of all three stations, unchanged
ring carrier blocks, unrelated system objects, template syntax, original classes,
unique embedded filenames and mesh IDs. Native Common.dll/ReadFile SUR load passed.
Source convex-plane imperfections are retained with measured tolerance, as in
Valensia. In-game visual/animation confirmation remains the user's restart check.

One minimal rollback under out/stations/terraform_mega/rollback, 1.96 MiB excluding the
small source snapshots already retained in the game. Generated staging removed
after installation and byte comparison. No timestamped/full-tree backups.

Tools: terraform_mega.py (initial build, refuses installed marker),
install_terraform_mega.py (validation / --apply). Native validation reuses
check_valensia_mega_native.py with valensia_mega.OUT set to out/stations/terraform_mega.
Reports and installed hashes: out/stations/terraform_mega/*.json.

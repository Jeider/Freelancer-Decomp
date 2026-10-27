# Internal equipment class checks

Native Win32 integration checks against the workspace's **real Common.dll**, INI loader,
archetypes, CShip and CE equipment. No graphics, retail assets or installed-game changes.

Build Common, Server and freelancer in Release/Win32 with
`/p:FreelancerEquipmentSlots=1`. Then, from the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/equipment_slots/check.ps1
```

The script builds a small executable in `src/obj/equipment_slots_tests` and writes **its own**
port.ini beside that executable. It runs in separate processes with the runtime option on
and off. Deliberately invalid fixtures print rejection messages; the final PASS lines and
zero exit code indicate success. An assertion failure is an error, never an expected result.

For the metadata lifecycle changes, build Common in DebugASan with the feature enabled,
then use `-GameBin binasan -ASan` to compile the fixture with matching debug containers/CRT
and AddressSanitizer. Required debug dependencies must already be built in binasan.

After rebuilding the modules with `/p:FreelancerEquipmentSlots=0`, verify that even runtime
`internal_classes=1` cannot enable it:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/equipment_slots/check.ps1 -FeatureOff
```

`-GameBin PATH` selects another directory containing the matching Common.dll/Common.lib and
DACOM binaries. The current compiler paths in check.ps1 target VS 18 Community, MSVC
14.51.36231, Windows SDK 10.0.26100 and `C:/DXSDK`; adapt these to another build machine.
Locally, project builds used `PlatformToolset=v145`, `FreelancerRp9=1`,
`Dx8SdkDir=C:/DXSDK`, `Dx9SdkDir=C:/DXSDK_Jun10` and `BuildProjectReferences=false`.

Coverage:

- All three families, strict class parsing, section/family mismatch, malformed/duplicate slots.
- Maximum-class slots versus exact-class hp_type declarations; case-insensitive matching.
- Class/family/occupied-slot rejection, mounted count, missing hull/slot, legacy coexistence.
- Real CShip installation gate in both legacy/classed installation orders; cargo accounting.
- Empty-scanner next/previous enemy and target selection.
- Real CInternalEquip serialization/copying for armor, scanner and tractor slot bindings.
- Archetype inheritance, copy/redefine, address reuse, ignored duplicate definitions and reload.
- Compile-time and runtime disabled paths.

The fixture skips only LoadEquipment's unrelated renderer-dependent BEAM_ARCH creation tail.
It does not exercise the client UI, trade message transport, disk saves or a flight simulation.
Interactive acceptance checks are listed in the [feature document](../../docs/re/equipment_mount_classes.md)
([Russian](../../docs/ru/re/equipment_mount_classes.md)).

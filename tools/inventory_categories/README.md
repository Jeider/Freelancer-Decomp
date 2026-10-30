# Boosters and Keys

Both player inventory and the equipment dealer use the new filters. `RepairKit`
and `ShieldBattery` appear in **Boosters** (Russian: **Усилители**); their existing
use actions and ship capacity limits remain in effect. `DoorKey` appears in
**Keys** (Russian: **Ключи**). No existing key definitions are converted.

## DoorKey

`[DoorKey]` is an Equipment archetype with no active device state or attachment
type. It belongs in cargo, consumes no hardware slot, and has no mount toggle.
Use the usual Equipment fields and a `[Good]` with `category = equipment` and
`equipment = <key nickname>` to expose it in inventory/markets. Set `ids_name`
to a valid localized resource ID. A zero-price key remains visible.

Minimal equipment declaration (replace the example resource ID with your own):

```ini
[DoorKey]
nickname = station_access_key
ids_name = 123456
volume = 0
lootable = false
```

For authored loadouts use `cargo = station_access_key, 1`. The existing
`dock_key` plugin resolves the key by nickname from `DATA/dock_key.ini`:

```ini
[locked_docks]
key = station_access_key
mounted = false
docks = station_dock_nickname
```

For `DoorKey`, presence in the docking player's cargo is sufficient even when
`mounted` is omitted or true. The key is not consumed. Legacy archetypes retain
their existing `mounted` rules. The plugin must be enabled; this uses its existing
locked-dock checks and does not add proximity-door rules.

## Independent icons

Installed files: `DATA/INTERFACE/NEURONET/INVENTORY/boosters.3db` and `keys.3db`.
Boosters uses the updated `data/Equipment/models/commodities/nn_icons/machines.3db`
from Freelancer Beta. Its quad is centered and sized for the filter row, with
the original texture and UVs preserved. Health's RepairDroid action uses this same
asset, enlarged at the right edge of Health; CloakingDevice sits at the left edge,
with weapon groups centered between them. The number below RepairDroid shows
its remaining HP reserve as an integer percentage (0–100), including while off.
Keys copies Internal Equipment (`cargobay.3db`) as a textured quad. Each copy contains independent mesh, material and
texture names, so editing either leaves the original icons unchanged.

The filter row is shifted one icon step to the right in both inventory layouts.
Boosters is enlarged 25% and offset 0.003 UI units left within that row. Health
normalizes the same model to a fixed radius, so this does not enlarge RepairDroid.
The independent Keys file is `DATA/INTERFACE/NEURONET/INVENTORY/keys.3db`.
Replace `Texture library / inventory_keys_icon.tga / MIP0` in that file to draw
your own key or lock. Its texture is also exported to
`assets/inventory_categories/inventory_keys_icon.tga`. Alternatively regenerate
only Keys using `stage_icons.py --keys-only --keys-texture path/to/texture.tga`.
In `boosters.3db`, replace `Texture library / inventory_boosters_icon.tga / MIP0`.
The exported original texture is `assets/inventory_categories/inventory_boosters_icon.tga`.
Alternatively regenerate the staged icon with:

```powershell
python -B tools/inventory_categories/stage_icons.py --boosters-texture path/to/texture.tga
```

## Build, check, install

```powershell
& tools/inventory_categories/build.ps1
python -B tools/inventory_categories/check.py
python -B tools/inventory_categories/prepare_install.py
```

Run the generated `src/obj/inventory_categories_install/<timestamp>/install.ps1`
with the game closed. It installs Common, Content, client and the two icons,
checks source/destination hashes, backs up originals, and rolls back on failure.
It changes no game INIs or key definitions.

The native check uses the real Common DLL to load/inherit DoorKey archetypes,
create and reload cargo, and load ship limits. It compiles the production filter,
lock and purchase-limit functions to verify cargo keys, player ownership, legacy
mount rules, Boosters limits, and free/paid key purchases. UI appearance still
needs an in-game check.

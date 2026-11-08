Local ship parking (single player)

Default: zero owned slots, maximum three per base, 20,000 credits per permanent
slot. DATA/RPG/ship_parking.ini owns defaults and per-base overrides. Restart the
game after changing the configuration. A ParkingBase supplies base and seller;
max_slots, initial_slots and slot_price inherit ParkingDefaults. Zero maximum
disables additional parking. No shared/global allowance or automatic faction pricing.

Server owns the cash/rights transaction and checks base, seller, quoted ownership
and price. Retrying a confirmation cannot buy the same quoted slot twice. Local
rights survive an empty parking list and save/load. Old parked hulls grant up to
the local maximum once; excess hulls remain collectible/exchangeable. Mission
cache records are separate, never consume a paid slot, and cannot be taken from
the parking UI. While using a mission replacement ship, manual park/take is blocked.
Exchange replaces the selected local record without needing a temporary free slot.

Save keys: ship_parking_version=1; ship_parking_owned=base_id,count; ship_cache has
an optional sixth value (1=parking, 0=mission). Legacy park_N names migrate to
parking; other names remain mission records. Existing ship/equipment/group/weapon
group serialization is retained. Lowering max_slots never deletes owned rights
or stored ships; new parking uses min(owned,max_slots), exchange is still allowed.

NPCs use a separate RPG/parking_contacts.ini catalog. generate.py discovers the
installed bar layouts and avoids authored fixtures and existing RPG reservations.
Standing placements are preferred, then seated male placements. Three special
story rooms have no suitable marker; bases without a bar or missing definitions
are listed in parking_report.json. Existing story contacts are not overwritten.
The generator preserves installed pricing overrides. Re-run it after regenerating
world content. A standalone copy is installed in Pythonlancer/tools/ship_parking.py.
All parking DATA output goes through tools.data_folder.DataFolder, including
staging, installation and rollback. The module accepts an explicit root, supports
sync_ship_parking for the generated set, and owns sync_data_file/remove_data_file
for exact-byte installation/restore. Existing build_to_folder behavior is retained.
The DATA-only write rule lives in both repositories' AGENTS.md instructions.
The manager name (IDS 238390) is registered in Pythonlancer/text/static.py and in
the resource DLLs actually referenced by the startup INIs for both languages.

Commands from repository root:
  python tools/ship_parking/check.py
  powershell -NoProfile -ExecutionPolicy Bypass -File tools/rpg_contacts/check.ps1
  python tools/train_courier/build.py Server Content freelancer
  python tools/ship_parking/install.py
  python tools/ship_parking/install.py --apply
  python tools/ship_parking/install.py --verify

Builds use FreelancerRpgWorld=1. Installation targets D:/Games/FL_MOD/bin only for
Server.dll, Content.dll, freelancer.exe and PDBs. Name resource DLLs follow the
actual startup INI paths. Installation checks hashes, requires a closed game,
backs up all replaced files, and rolls back a failed transaction. Saves are never
edited by the installer.

Native checks execute production server and dialogue code against fake game I/O:
cash failure, stale confirmations, base-local pricing/rights, full exchanges,
save round trips including empty rights, migration/over-cap saves, mission cache,
SP-only behavior, dialogue cancellation and repeat visits. The contact harness
also checks direct dialog entry without a preceding movie and lifecycle cleanup.
In-game acceptance: verify NPC placement/camera, RU/EN captions and parking layout;
buy at Bismarck and Bremen, fill three slots, exchange, save/reload, and take a
courier assignment with the parking lot full. Harness tests do not validate pixels.

Avalon voiced conversation (rm0002)
---------------------------------
Scenario: tools/ship_parking/rm0002.json, installed as story/rpg/rm0002.json
in Pythonlancer. It contains 23 fragments: 8 Trent lines and 15 officer lines.
RpgAvalonParkingOfficer has an independent English reference at
Assets/VOICE_SOURCE_EN/RpgAvalonParkingOfficer.wav. Delivery is neutral;
Trent retains his configured teenager, high pitch delivery.

The existing park_br_avl_01 seller in the Avalon bar (br_avl_01_base) wears
br_captain_head and br_male_elite_body. Its marker stays
Zg/NPC/mFloor2/01/A/Stand. The shared conversation binds the clicked NPC,
uses the room's PCU/ACU cameras, and retains the rm0001 facial/gesture pipeline.
The scene covers purchase, explicit confirmation/cancel, permanent ownership,
base-local rights, full-lot exchange, success, insufficient funds, maximum and
stale/error outcomes, plus greeting/success variants. Spoken wording avoids
fixed prices/limits; the UI renders current configuration and the quoted price.
Buying requires reputation strictly greater than zero with the seller's faction.
Both quote and purchase check it; a failed purchase never deducts money. Existing
owned berths remain usable. All 233 sellers have a refusal branch, including the
55 voiced conversations; the remaining sellers use text. English refusal audio
and scenes are generated through the existing VoiceStudio/RPG pipeline.

Commands (Pythonlancer venv; RPG CLI runs from Pythonlancer):
  python -B tools/ship_parking/install_avalon.py sources  [from this repository]
  python -B single.py rpg build --group rm0002 --language en
  python -B single.py rpg scenes --group rm0002 --language en
  python -B single.py rpg runtime --group rm0002 --language en --dry-run
  python -B single.py rpg runtime --group rm0002 --language en
The runtime command verifies every compiled scene/audio file and both cameras;
tools.data_folder.sync_rpg_parking_runtime owns the two-file DATA transaction.
Regenerating the parking catalog preserves authored external-dialog contacts.
For the engine fix: build Content with RPG=1, then install_avalon.py engine.
Only Content.dll/PDB are installed; game must be closed. Backup paths are printed.
Production harness coverage includes voiced transactions and speech cursor sync,
cancel, no money, third-slot limit, replay, stale quote and changing bases.

ShipDealer commandants and service-window behavior
-------------------------------------------------
Parking now opens through NavBar::OpenService (type 13), with deferred creation
after the tab animation. NeuroNet panels close it through the same notification
as ShipTrader. Returning to the dealer/desk closes parking too. Its close
notification releases the service tab. ShipParkOpen uses that same path.
NeuroNet panels wait for the base service's close animation before opening.
Repeated close notifications do not queue another shrink/slide animation.
Pending panel requests can be replaced or cancelled while the service closes.
  python tools/ship_parking/check_window_transition.py
  python tools/train_courier/build.py freelancer
  python -B tools/ship_parking/build_commandants.py client
The ship card contains IdsInfo1 and IdsInfo only: the separate comparison
labels/values IdsInfo2/IdsInfo3 are no longer appended.

Coverage comes from the instantiated Pythonlancer UniverseManager: every IS_BASE
dockable with have_shipdealer(), including locked/story bases. The first audit
found 55 out of 423 bases, with 52 existing parking contacts. No other source base
has an installed standalone ShipDealer room. Three custom base definitions were
missing: co_mad_04_base, arch_01_base, heavy_barrel2_01_base. They receive the
existing Ocho-Rios split-room interior with their own base nickname. Dock locks
are unchanged. Malta's source interior flag says no bar, but its actual custom
base has a Bar; the generator validates actual rooms and camera markers.

managers/parking_commandants.py is installed from commandants.py. The end of
UniverseManager.sync_data calls sync_from_universe after room export. It assigns
stable rm0100+ IDs, creates per-base scenario JSON, reserves free bar placements,
checks both cameras and costume parts, and exports via DataFolder. The identity
registry is story/rpg/parking_commandants.json. Authored rm0002 remains Avalon.
There are 54 additional conversations of 23 fragments each, with distinct heads,
bodies and location-specific greetings. Three commandants sit, with chair poses
and seated gestures. Each group's conversation.thn binds its actor and idle pose;
scene_group plus local_scene=1 selects it in Content/client.

English uses the supplied RpgAvalonParkingOfficer reference and Trent's configured
delivery: distinct appearances and dialogue, one shared officer voice. Identical
text/actor/reference/delivery combinations reuse an audio cache. Every group has
its own sound names, manifests, WAV files and THNs. New/unrecorded fragments use
text until explicitly recorded. World export never calls the voice service.

Use the Pythonlancer venv from this repository:
  python -B tools/ship_parking/build_commandants.py sources
  python -B tools/ship_parking/build_commandants.py prepare
  python -B tools/ship_parking/build_commandants.py voices
  python -B tools/ship_parking/build_commandants.py install
  python -B tools/ship_parking/check_commandants.py
Before prepare, run audit_bases.py with Pythonlancer as cwd (absolute script path).
Build Content and freelancer with RPG=1, then build_commandants.py engine.
Coverage, inventory and installation reports: src/obj/ship_parking/commandants.
DATA staging, backups and rollback all use tools.data_folder.

Static ShipDealer rooms
----------------------
managers/parking_rooms.py follows the actual base Room/file references and adds
StartShipPark beside every StartShipDealer service. It preserves existing bytes
and is idempotent. The universe export hook runs this after exporting generated
rooms, so static interiors such as rh_biz_01_base are covered as well.
The audited 55 source markets use 35 unique service-room files; 25 lacked parking.
Two authored interiors declare a market but have no actual ship-sales room:
om11_01_base uses Deck and sig42_01_base uses Planetscape for parking access.
The central DataFolder writer permits only the additive hotspot transformation
for rooms and rejects stale or unrelated room changes.
  python -B tools/ship_parking/check_parking_rooms.py
check_commandants.py verifies one parking hotspot in every actual service room.

Parking button and contact icons
--------------------------------
The parking service uses IDS 238391 (Parking / Парковка) and its own standalone
Interface/Baseside/parking_p.3db. The P and square frame are native geometry;
the unique UI material uses normal button tint/highlight/disabled states.
ui.py build creates the asset from polygons; ui.py apply installs both resource
DLL translations, text/static.py, the Pythonlancer source asset and DATA via
DataFolder.sync_parking_ui. parking_ui.py restores the mapping/asset on export.

RPG CharacterEncounter accepts icon = rumor or icon = mission (default rumor).
For RPG behaviors only, the existing extra offer field carries this presentation
hint; dialogue ids and entry kinds are unchanged. The client selects the normal
talk_rumor/talk_mission cursor on hover. Parking contacts use rumor; the Bismarck
trader and generated courier owners use mission. The courier generator and
legacy rm0001 binder retain this field when regenerating contacts.
  python tools/ship_parking/ui.py build
  python -B tools/ship_parking/build_commandants.py sources
  python -B tools/ship_parking/ui.py apply
  python tools/train_courier/build.py Content freelancer
  python -B tools/ship_parking/build_commandants.py engine

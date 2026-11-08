ARCHIVED / NOT INSTALLED -- 2026-11-06

This experiment was shelved at the user's request. Default builds disable it;
the ARCHIVED marker blocks its build/check/install helpers. Read ARCHIVE.txt
for the current state and unfinished work. Everything below is a historical
description of the FIRST prototype, not the current implementation or a valid
installation procedure. Do not run these commands to resume it automatically.

Historical notes -- Capital interiors: first base om15_01_base

The Rheinland equip_depot_deck.ini uses rh_08_bar_hardpoint_r6.thn.
prepare.py extracts its rh_08_depot shell and shadow/glare lights, removes
tables/chairs/props/character placements, and adds five service cameras and
X/ShipExterior/01. Existing ambient lighting and base-specific space background
are reused. The room displays the player's real ship/equipment through HpMount.
The compound bounds determine distance and centering; ship scale is unchanged.
No small-ship landing/launch animation or ground shadow is used.

DATA/INTERFACE/capital_interiors.ini opts bases in. Each repeated room line is:
    room = logical_room_nickname, path_relative_to_DATA
The current pilot uses Deck only. Bar and its mission contacts stay available.
CRUISER, TRANSPORT and CAPITAL object types select the alternative profile.
ship_class is intentionally ignored (the train uses freighter label 2).
Fighters and ordinary freighters keep the original rooms and ship dealer.

Client-owned RoomData variants preserve BaseId/RoomId and never change the
Common database shared with the single-player server. Switching ships while
docked refreshes the current room when camera/modal work is idle. ShipDealer
routes and UI entry points are disabled in an active capital profile; the
server also rejects entering ShipDealer, buying a hull/package or client-side
ReqShipArch replacement. Server mission ship grants/restores remain available.

Build and check from the repository root:
    python tools/capital_interiors/prepare.py
    python tools/train_consist/build_yard.py freelancer
    python tools/train_consist/build_yard.py Server
    python tools/capital_interiors/check.py
    python tools/capital_interiors/preview.py
    python tools/capital_interiors/install.py
    python tools/capital_interiors/install.py --apply

The build helper reuses the current RPG-enabled train-yard client/server build
directories. Installation targets D:/Games/FL_MOD/bin and DATA. Common.dll and
Content.dll are preserved. Backup hashes and the exact file list are recorded
in out/capital_interiors/installed.json and the game's BACKUP directory.
No generated base or Pythonlancer template is overwritten: the optional mapping
survives regeneration of gen_om15_01_base.ini. The source assets are DATA_EXTRA.

Validation: check.py loads the installed Common/Thorn/DALib against staged data,
checks ship selection, cameras/orientation, services, no character placements,
reload lifecycle, and staged Server + installed Content dependency loading.
preview.py renders actual CMP geometry/textures for composition only; this is
not an in-game screenshot (it omits game lighting, equipment and moving proxies).

In-game acceptance still requires docking/loading om15_01_base with a fighter,
a cruiser, ge_train_player and ge_train_loco_player; checking Deck/Bar/Trader/
Equipment/repair/launch; receiving and restoring the mission ship while docked;
and confirming ShipDealer is absent. Also check widescreen framing and a saved
ShipDealer location loaded with a capital ship (redirect to Deck).

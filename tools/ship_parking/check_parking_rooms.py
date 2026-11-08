"""Regression checks for static room preservation and constrained DATA writes."""
from pathlib import Path
import sys
import tempfile

PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0,str(PROJECT))
sys.dont_write_bytecode=True
from managers.parking_rooms import ensure_parking_hotspot, plan_room_hotspots
from tools.data_folder import DataFolder

for nl in (b'\n',b'\r\n'):
    original=nl.join((b'; keep this comment',b'[Room_Info]',b'set_script = existing.thn',
                      b'[Hotspot]',b'name = IDS_HOTSPOT_SHIPDEALER',
                      b'behavior = StartShipDealer',b'state_read = 2',b'state_send = 1'))
    patched=ensure_parking_hotspot(original)
    assert patched.startswith(original)
    assert patched.count(b'StartShipPark')==1
    assert nl+b'behavior = StartShipPark'+nl in patched
    assert ensure_parking_hotspot(patched)==patched
    unrelated=b'; behavior = StartShipDealer\n[Hotspot]\nbehavior = StartDealer\n'
    assert ensure_parking_hotspot(unrelated)==unrelated
    try: ensure_parking_hotspot(patched+b'\n[Hotspot]\nbehavior = StartShipPark\n')
    except ValueError: pass
    else: raise AssertionError('Duplicate parking accepted')
    try: ensure_parking_hotspot(original+b'\n[Hotspot]\nname = IDS_HOTSPOT_SHIPPARK\nbehavior = StartDealer\n')
    except ValueError: pass
    else: raise AssertionError('Occupied hotspot name accepted')

# Reproduce the static Bismarck room by following its base definition.
base='rh_biz_01_base'
room='Universe/custom/static_shipdealer.ini'
inputs={'Universe/base.ini':b'[Room]\nnickname = ShipDealer\nfile = Universe\\custom\\static_shipdealer.ini\n',room:original}
files,coverage=plan_room_hotspots([base],{base:'Universe/base.ini'},inputs.__getitem__)
assert files[room]==patched and coverage[0]['rooms'][0]['added']
inputs.update(files)
again,coverage=plan_room_hotspots([base],{base:'Universe/base.ini'},inputs.__getitem__)
assert again==files and not coverage[0]['rooms'][0]['added']

with tempfile.TemporaryDirectory() as temporary:
    folder=DataFolder(root=Path(temporary)/'game')
    backup=Path(temporary)/'backup'
    folder.sync_data_file(room,original)
    folder.sync_parking_commandants(files,backup)
    assert folder.data_path(room).read_bytes()==patched
    for invalid in (patched.replace(b'existing.thn',b'changed.thn'), original):
        try: folder.sync_parking_commandants({room:invalid},backup)
        except ValueError: pass
        else: raise AssertionError('Nonadditive/incomplete room edit accepted')
        assert folder.data_path(room).read_bytes()==patched
print('PASS: static room discovery, newline/comment preservation, repeat export, duplicate rejection and constrained DATA writes')

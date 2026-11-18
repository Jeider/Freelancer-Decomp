"""Deploy the accepted hold repair only on the user's explicit installation request."""
import hashlib
import importlib.util
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/ship_design/rh_freighter/rh_pir_freighter/hold_repair'
GAME = Path('D:/Games/FL_MOD')
PY = GAME / 'Assets/Pythonlancer'
REL = 'ships/rheinland/rh_pir_freighter/'
NAME = 'rh_pir_freighter.cmp'
SOURCE = PY / 'assets' / REL
PLAN = OUT / 'deployment/plan.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def safe(path, root):
    path = path.absolute()
    root = root.resolve()
    assert path.resolve().is_relative_to(root), path
    for parent in [path, *path.parents]:
        if not parent.is_relative_to(root):
            break
        if parent.exists():
            assert not getattr(parent.stat(), 'st_file_attributes', 0) & 0x400, parent
    return path


def api(root):
    spec = importlib.util.spec_from_file_location('rpf_hold_data_folder', PY / 'tools/data_folder.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFolder(root=root)


def guard(hashes):
    for filename, expected in hashes.items():
        assert sha(Path(filename)) == expected, ('Changed since review', filename)


def prepare():
    import rh_freighter_hold_repair as repair
    repair.verify_delivery()
    delivery = read(OUT / 'delivery_manifest.json')
    validation = read(OUT / 'validation.json')
    shield = read(OUT / 'shield_check.json')
    digest = sha(OUT / NAME)
    assert digest == shield['cmp_sha256'] == validation['cmp_sha256']
    assert shield['shield_hpid_present'] and shield['generator_hull_present']
    assert sha(GAME / 'DATA' / REL / 'rh_pir_freighter.sur') == shield['sur_sha256']
    live = GAME / 'DATA' / REL / NAME
    hp = lambda p: repair.d.hardpoints(repair.d.tree(p)[1], ('Sc_extend wing', 0))
    old, new = hp(live), hp(OUT / NAME)
    assert len(old) == len(new) == 68 and old.keys() == new.keys()
    for name in old:
        assert old[name]['owner'] == new[name]['owner'] and old[name]['leaves'] == new[name]['leaves'], name
    manifest_path = SOURCE / 'manifest.json'
    manifest = read(manifest_path)
    before = {str(manifest_path): sha(manifest_path), str(live): sha(live)}
    protected = {str(GAME / 'DATA/SHIPS/shiparch.ini'): sha(GAME / 'DATA/SHIPS/shiparch.ini')}
    mat = delivery['shared_mat']
    protected[mat['path']] = mat['sha256']
    for name, entry in manifest['files'].items():
        source = safe(SOURCE / name, SOURCE)
        assert sha(source) == entry['sha256'], source
        if name == NAME:
            before[str(source)] = sha(source)
        else:
            assert entry['sha256'] == delivery['dependencies'][name]['sha256']
            protected[str(source)] = entry['sha256']
            protected[str(GAME / 'DATA' / REL / name)] = entry['sha256']
    guard(protected)
    manifest['files'][NAME] = dict(bytes=(OUT / NAME).stat().st_size, sha256=digest)
    manifest.update(cmp_sha256=digest, revision='hold_repair', lod_triangles=validation['counts'],
                    authoring_report=str(OUT / 'README.md'))
    save(OUT / 'deployment/manifest.json', manifest)
    free = shutil.disk_usage(GAME).free
    assert free > 64 * 1024 * 1024
    staged = api(OUT / 'deployment/staged')
    staged.sync_rh_pir_freighter({REL + NAME: (OUT / NAME).read_bytes()})
    assert sha(staged.data_path(REL + NAME)) == digest
    guard(before)
    guard(protected)
    save(PLAN, dict(before=before, protected=protected, cmp_sha256=digest,
                    manifest_sha256=sha(OUT / 'deployment/manifest.json'), hardpoints_preserved=68,
                    user_authorization='Explicit installation request: ставь', free_bytes=free))
    print('READY: one CMP, canonical source and manifest; all 68 user hardpoints preserved; staged DATA verified')


def apply():
    plan = read(PLAN)
    guard(plan['before'])
    guard(plan['protected'])
    assert sha(OUT / NAME) == plan['cmp_sha256']
    assert sha(OUT / 'deployment/manifest.json') == plan['manifest_sha256']
    folder = api(GAME)
    live = safe(folder.data_path(REL + NAME), GAME / 'DATA' / REL)
    sources = {safe(SOURCE / NAME, SOURCE): (OUT / NAME).read_bytes(),
               safe(SOURCE / 'manifest.json', SOURCE): (OUT / 'deployment/manifest.json').read_bytes()}
    backups = {p: p.read_bytes() for p in sources}
    game_backup = live.read_bytes()
    game_attempted = False
    try:
        # Source update is verified separately before the DATA synchronization.
        for path, payload in sources.items():
            path.write_bytes(payload)
        for path, payload in sources.items():
            assert path.read_bytes() == payload
        assert sha(live) == plan['before'][str(GAME / 'DATA' / REL / NAME)]
        guard(plan['protected'])
        game_attempted = True
        folder.sync_rh_pir_freighter({REL + NAME: sources[SOURCE / NAME]})
        assert sha(live) == sha(SOURCE / NAME) == plan['cmp_sha256']
        guard(plan['protected'])
    except BaseException:
        if game_attempted:
            folder.sync_rh_pir_freighter({REL + NAME: game_backup})
        for path, payload in backups.items():
            path.write_bytes(payload)
        raise
    save(OUT / 'installation.json', dict(installed=True, installed_at=datetime.now(timezone.utc).isoformat(),
         game_file=str(live), canonical_source=str(SOURCE / NAME), cmp_sha256=plan['cmp_sha256'],
         hardpoints_preserved=68, unchanged=plan['protected'], game_launched=False,
         data_api='DataFolder.sync_rh_pir_freighter', authorization=plan['user_authorization'],
         rollback='in-memory transaction copies released after verification'))
    print('INSTALLED AND VERIFIED: accepted CMP and Pythonlancer source; SUR, damage, shared MAT and shiparch preserved')


def cleanup():
    report = read(OUT / 'installation.json')
    assert report['installed']
    for filename in ('game_file', 'canonical_source'):
        assert sha(Path(report[filename])) == report['cmp_sha256']
    guard(report['unchanged'])
    removed = []
    for path in (OUT / NAME, OUT / 'deployment/staged/DATA' / REL / NAME):
        safe(path, OUT)
        if path.exists():
            assert sha(path) == report['cmp_sha256'], ('Edited authoring export; preserved', path)
            path.unlink()
            removed.append(str(path))
    save(OUT / 'installed_cleanup.json', dict(removed=removed, canonical_source=report['canonical_source'],
         user_source_blender_static_open_cmp_and_previews_preserved=True, binary_rollback_copies=0))
    print('CLEANED: verified installed export and staged DATA copy; editable sources retained')

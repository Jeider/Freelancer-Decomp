"""Install the two accepted exhaust-HP CMP patches on explicit user request.

DATA writes/recovery use DataFolder. No generation, shared MAT write or launch.
"""
import argparse
import copy
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
import numpy as np
import rh_engine_exhaust_alignment as alignment

d, f = alignment.d, alignment.f
GAME = d.GAME
PY = GAME / 'Assets/Pythonlancer'
SOURCE = PY / 'assets/ships/rheinland/rh_pir_freighter'


def checked(path, root):
    path = path.absolute()
    assert path.resolve() != root.resolve() and path.resolve().is_relative_to(root.resolve()), path
    for parent in (path, *path.parents):
        assert not parent.is_symlink() and not parent.is_junction(), parent
    return path.resolve()


def read(path):
    return json.loads(path.read_text(encoding='utf8'))


def guard(hashes):
    for path, expected in hashes.items():
        assert f.digest(Path(path)) == expected, ('Changed since review', path)


def api():
    spec = importlib.util.spec_from_file_location('rh_exhaust_data_folder', PY / 'tools/data_folder.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFolder(root=GAME)


def plan():
    payload, revisions, before, protected = {}, {}, {}, {}
    for ship, root in alignment.ROOTS.items():
        out = root / 'exhaust_alignment'
        manifest = read(out / 'manifest.json')
        assert manifest['model'] == ship
        name = ship + '.cmp'
        info = manifest['files'][name]
        stage = checked(out / name, out)
        relative = 'ships/rheinland/' + ship + '/' + name
        live = checked(GAME / 'DATA' / relative, GAME / 'DATA')
        assert f.digest(stage) == info['sha256']
        assert f.digest(live) == info['source_sha256'], 'Import newer manual edits first'
        _, old = d.tree(live)
        _, new = d.tree(stage)
        targets = {k: np.array(v['after']) for k, v in manifest['changes'].items()}
        checks = alignment.check_exact(old, new, info['private_resources'], targets, ('Sc_extend wing', 0))
        assert checks == info['checks']
        measured, _ = alignment.nozzle_targets(new)
        assert all(np.allclose(targets[k], measured[k], atol=2e-6, rtol=0) for k in targets)
        for key in ('unchanged_sur', 'shared_mat'):
            entry = manifest[key]
            protected[entry['path']] = entry['sha256']
        for path in live.parent.iterdir():
            if path.is_file() and path != live:
                checked(path, GAME / 'DATA')
                protected[str(path)] = f.digest(path)
        payload[relative] = stage.read_bytes()
        before[str(live)] = f.digest(live)
        revisions[ship] = dict(out=out, manifest=manifest, live=live, stage=stage, relative=relative)
    canonical = checked(SOURCE / 'rh_pir_freighter.cmp', PY)
    manifest_path = checked(SOURCE / 'manifest.json', PY)
    source_manifest = read(manifest_path)
    new_manifest = copy.deepcopy(source_manifest)
    for name, info in source_manifest['files'].items():
        path = checked(SOURCE / name, PY)
        assert f.digest(path) == info['sha256'], path
        if name != canonical.name:
            protected[str(path)] = info['sha256']
    freighter = revisions['rh_pir_freighter']
    assert f.digest(canonical) == freighter['manifest']['files'][canonical.name]['source_sha256']
    new_hash = freighter['manifest']['files'][canonical.name]['sha256']
    new_manifest['files'][canonical.name] = dict(bytes=freighter['stage'].stat().st_size, sha256=new_hash)
    new_manifest.update(cmp_sha256=new_hash, revision='exhaust_alignment', authoring_report=str(freighter['out'] / 'README.md'))
    sources = {canonical: payload[freighter['relative']],
               manifest_path: (json.dumps(new_manifest, ensure_ascii=False, indent=2) + '\n').encode('utf8')}
    before.update({str(p): f.digest(p) for p in sources})
    for path in (GAME / 'DATA/SHIPS/shiparch.ini', PY / 'tools/data_folder.py'):
        protected[str(path)] = f.digest(path)
    # A Windows path has one identity regardless of the spelling of its case.
    # Keep the JSON readable by case-insensitive consumers such as PowerShell.
    protected = {str(Path(p).resolve()): digest for p, digest in protected.items()}
    guard(protected)
    assert shutil.disk_usage(GAME).free > 64 * 1024**2
    for revision in revisions.values():
        d.dump(revision['out'] / 'installation_plan.json', dict(before=before, protected=protected,
            game_targets=list(payload), pythonlancer_targets=[str(p) for p in sources],
            authorization='User explicitly requested: внедри обоих в игру'))
    print('PLAN VERIFIED: two game CMPs and freighter canonical CMP/manifest.', flush=True)
    return payload, sources, revisions, before, protected


def apply():
    payload, sources, revisions, before, protected = plan()
    folder = api()
    guard(before)
    backups = {Path(path): Path(path).read_bytes() for path in before}
    source_attempts, game_attempts = [], []
    try:
        for path, content in sources.items():
            source_attempts.append(path)
            path.write_bytes(content)
        for relative, content in payload.items():
            game_attempts.append(relative)
            folder.sync_data_file(relative, content)
        for path, content in sources.items():
            assert path.read_bytes() == content
        for relative, content in payload.items():
            assert folder.data_path(relative).read_bytes() == content
        guard(protected)
    except BaseException:
        for relative in reversed(game_attempts):
            folder.sync_data_file(relative, backups[folder.data_path(relative)])
        for path in reversed(source_attempts):
            path.write_bytes(backups[path])
        guard(before)
        raise
    installed_at = datetime.now(timezone.utc).isoformat()
    for ship, revision in revisions.items():
        manifest = revision['manifest']
        info = manifest['files'][ship + '.cmp']
        assert f.digest(revision['live']) == info['sha256']
        if ship == 'rh_pir_freighter':
            assert f.digest(SOURCE / (ship + '.cmp')) == info['sha256']
        report = dict(installed=True, installed_at=installed_at, game_file=str(revision['live']),
            cmp_sha256=info['sha256'], hashes_verified=True, game_launched=False,
            authorization='User explicitly requested: внедри обоих в игру', protected=protected,
            canonical_source_updated=ship == 'rh_pir_freighter', staging_cmp_removed=False,
            rollback='Transaction held in memory only; released after verification')
        d.dump(revision['out'] / 'installation.json', report)
        stage = checked(revision['stage'], revision['out'])
        assert f.digest(stage) == f.digest(revision['live'])
        stage.unlink()
        report['staging_cmp_removed'] = True
        d.dump(revision['out'] / 'installation.json', report)
        manifest.update(installed=True, installed_file=str(revision['live']), installation_report='installation.json',
                        policy='Installed on explicit request. Editable review retained; staged animated CMP removed.')
        manifest['files'][ship + '.cmp']['installed_path'] = str(revision['live'])
        d.dump(revision['out'] / 'manifest.json', manifest)
        readme = revision['out'] / 'README.md'
        text = readme.read_text(encoding='utf8')
        old_path, new_path = stage.as_posix(), revision['live'].as_posix()
        text = text.replace(old_path, new_path)
        text = text.replace('Комплект офлайн. В игре пока предыдущие CMP. Конфиги и материалы менять не нужно.',
            'Установлено по прямому запросу пользователя. Хеш CMP проверен. Конфиги и материалы не менялись.')
        text = text.replace('Для freighter также заменить CMP в источнике Pythonlancer и обновить его manifest при разрешённой установке.',
            'Для freighter также обновлены канонический CMP и его manifest в Pythonlancer.')
        text += '\nУстановочный CMP удалён после проверки; редактируемый review_open сохранён. Отчёт: installation.json.\n'
        readme.write_text(text, encoding='utf8')
    print('INSTALLED AND VERIFIED: both CMPs; freighter source/manifest synchronized; staging CMPs removed.', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else plan()

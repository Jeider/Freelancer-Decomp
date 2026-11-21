"""Install the explicitly requested, already reviewed fighter asset set only.

All game DATA writes and transaction recovery use Pythonlancer DataFolder.
This does not generate shiparch, change shared materials, or launch the game.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'out/ship_design/rh_fighter/rh_pir_fighter'
ASSETS = OUT / 'assets'
GAME = Path('D:/Games/FL_MOD')
PY = GAME / 'Assets/Pythonlancer'
BASE = 'ships/rheinland/rh_pir_fighter/'
ZONES = ('port_engine', 'starboard_engine', 'port_wing', 'starboard_wing')
NAMES = {'rh_pir_fighter.cmp', 'rh_pir_fighter.sur', 'rh_pir_fighter_lods.mat'}
NAMES |= {'rh_pir_fighter_dmg_' + z + ext for z in ZONES for ext in ('.3db', '.sur')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((OUT / name).read_text(encoding='utf8'))


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


def checked(root, relative):
    raw = root.absolute() / relative
    for part in (raw, *raw.parents):
        if part.is_symlink() or part.is_junction():
            raise ValueError('Reparse path: ' + str(part))
    path = raw.resolve()
    assert path != root.resolve() and path.is_relative_to(root.resolve()), path
    return path


def data_api():
    spec = importlib.util.spec_from_file_location('fighter_install_data_folder', PY / 'tools/data_folder.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFolder


def plan():
    manifest = read('manifest.json')
    assert set(manifest['assets']) == NAMES
    assert manifest['model'] == 'rh_pir_fighter'
    assert manifest['shared_material_sha256'] == sha(Path(manifest['shared_material']))
    assert read('validation.json')['cmp_sha256'] == manifest['cmp_sha256']
    damage = read('damage_export_check.json')
    assert damage['cmp_sha256'] == manifest['cmp_sha256'] and set(damage['zones']) == set(ZONES)
    for zone in damage['zones'].values():
        assert zone['sha256'] == manifest['assets'][zone['file']]['sha256']
        assert len(zone['levels']) == 3
        assert all(v['boundary_edges'] == v['nonmanifold_edges'] == 0 for v in zone['levels'])
    hp = manifest['user_hardpoint_source']
    assert sha(Path(hp['file'])) == hp['sha256']
    assert sha(OUT / 'rh_pir_fighter_review_open.cmp') == 'be65b950f8d990005c07dc3697131bbf6bbad9b581390261d8a2994b0869dc63', 'Review model changed after release'
    sources = read('source_applied.json')
    for relative, entry in sources['files'].items():
        assert sha(checked(PY, relative)) == entry['after'], ('Source changed', relative)
    assert read('pythonlancer_check.json')['applied_generation_matches_review']
    payload, before = {}, {}
    for name in sorted(NAMES):
        source = checked(ASSETS, name)
        assert sha(source) == manifest['assets'][name]['sha256'], name
        assert source.stat().st_size == manifest['assets'][name]['bytes'], name
        relative = BASE + name
        target = checked(GAME / 'DATA', relative)
        before[relative] = sha(target) if target.exists() else None
        payload[relative] = source.read_bytes()
    protected = {str(p): sha(p) for p in (
        GAME / 'DATA/SHIPS/shiparch.ini', Path(manifest['shared_material']), PY / 'tools/data_folder.py')}
    plan_data = dict(files=manifest['assets'], before=before, protected=protected,
                     target=str(checked(GAME / 'DATA', BASE)), bytes=sum(map(len, payload.values())),
                     active_shiparch_written=False, game_launched=False,
                     authorization='User explicitly requested: венси файлы в игру')
    save('installation_plan.json', plan_data)
    print('PLAN: 11 reviewed assets,', plan_data['bytes'], 'bytes;', sum(v is not None for v in before.values()), 'existing files to replace.')
    print('Shared MAT and active shiparch are protected. Pythonlancer sources already applied.')
    return manifest, payload, plan_data


def update_documents(report):
    manifest = read('manifest.json')
    manifest.update(installed=True, stage='asset files installed and hash-verified; active shiparch generation remains with user',
                    installed_asset_root=str(GAME / 'DATA' / BASE), installation_report='installation.json')
    save('manifest.json', manifest)
    path = OUT / 'README.md'
    text = path.read_text(encoding='utf8')
    text = text.replace('# rh_pir_fighter — комплект для ручной установки', '# rh_pir_fighter — установленный комплект')
    text = text.replace('**Комплект подготовлен офлайн. В Pythonlancer внесены три исходника; игра и live DATA не изменены.**',
        '**По прямому запросу пользователя установлены и проверены 11 файлов модели. '
        'Исходники Pythonlancer обновлены; активный shiparch.ini пока требует генерации пользователем. Игра не запускалась.**')
    text = text.replace('Три проверенных исходника уже внесены в Pythonlancer. Генерация рабочей DATA\n'
                        'и установка моделей остаются за пользователем; source_applied.json фиксирует хеши.',
                        'Три проверенных исходника внесены в Pythonlancer, модели установлены. '
                        'Генерацию shiparch выполняет пользователь. Хеши: source_applied.json и installation.json.')
    for name in NAMES:
        text = text.replace('(assets/' + name + ')', '(' + (GAME / 'DATA' / BASE / name).as_posix() + ')')
    text = text.replace('- В `assets/` также четыре пары', '- В игровой папке также четыре пары')
    text = text.replace('LOD: **16941 / 3949 / 373**', 'LOD: **16997 / 4005 / 373**')
    text += '\n## Установка файлов\n\n' + report['utc'] + ': 11 файлов установлены через DataFolder в\n`' + (GAME / 'DATA' / BASE).as_posix() + '`.\n'
    text += 'Все SHA-256 совпали с manifest.json. Общий MAT и активный shiparch.ini не изменены.\n'
    text += 'Установочные бинарники и временные резервные копии удалены после проверки; исходные модели, review_open и Blender сохранены.\n'
    path.write_text(text, encoding='utf8')
    path = OUT / 'index.html'
    text = path.read_text(encoding='utf8').replace('rh_pir_fighter — офлайн-комплект', 'rh_pir_fighter — установленный комплект')
    text = text.replace('В игру не установлен.', 'Файлы модели установлены и проверены. Требуется генерация shiparch из обновлённого Pythonlancer.')
    text = text.replace('Состав и установка пользователем', 'Состав и отчёт установки')
    path.write_text(text, encoding='utf8')
    handoff = read('lod_material_handoff.json')
    handoff.update(file=(GAME / 'DATA' / BASE / 'rh_pir_fighter_lods.mat').as_posix(), installed_separately=True)
    save('lod_material_handoff.json', handoff)


def apply():
    manifest, payload, planned = plan()
    assert shutil.disk_usage(OUT).free > 100 * 1024**2
    transaction = checked(OUT, 'installation_transaction')
    assert not transaction.exists(), 'Inspect unfinished installation transaction first'
    transaction.mkdir()
    api = data_api()
    live, backup = api(root=GAME), api(root=transaction)
    old = {}
    for relative in payload:
        path = checked(GAME / 'DATA', relative)
        content = path.read_bytes() if path.exists() else None
        assert (hashlib.sha256(content).hexdigest() if content is not None else None) == planned['before'][relative]
        old[relative] = content
        if content is not None:
            backup.sync_data_file(relative, content)
    save('installation_transaction/before.json', planned['before'])
    touched = []
    try:
        for relative, content in payload.items():
            touched.append(relative)
            live.sync_data_file(relative, content)
        for name, info in manifest['assets'].items():
            assert sha(checked(GAME / 'DATA', BASE + name)) == info['sha256'], name
        for path, expected in planned['protected'].items():
            assert sha(Path(path)) == expected, ('Protected file changed', path)
    except BaseException:
        for relative in reversed(touched):
            if old[relative] is None:
                live.remove_data_file(relative)
            else:
                live.sync_data_file(relative, old[relative])
        raise
    report = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  authorization=planned['authorization'], target=planned['target'],
                  files=manifest['assets'], hashes_verified=True, game_launched=False,
                  active_shiparch_written=False, shared_mat_written=False, protected=planned['protected'],
                  staging_binaries_removed=False, transaction_backups_removed=False)
    save('installation.json', report)
    removed = []
    for name, info in manifest['assets'].items():
        stage = checked(ASSETS, name)
        assert sha(stage) == sha(checked(GAME / 'DATA', BASE + name)) == info['sha256']
        stage.unlink()
        removed.append(str(stage))
    # These two generated binary intermediates are reproducible from the preserved
    # authoring JSON and PNG. Editable Blender/review/source assets are retained.
    for name in ('authoring_animated.cmp', 'rh_pir_fighter_f01_projection_lod.dds'):
        path = checked(OUT, name)
        if path.exists():
            path.unlink()
            removed.append(str(path))
    for relative, content in old.items():
        if content is not None:
            checked(transaction / 'DATA', relative)
            backup.remove_data_file(relative)
    # Remove empty transaction folders only, never recursive deletion.
    for relative in (BASE.rstrip('/'), 'ships/rheinland', 'ships'):
        if checked(transaction / 'DATA', relative).exists():
            backup.remove_empty_data_directory(relative)
    if (transaction / 'DATA').exists():
        checked(transaction, 'DATA').rmdir()
    checked(transaction, 'before.json').unlink()
    transaction.rmdir()
    report.update(staging_binaries_removed=True, transaction_backups_removed=True, removed=removed)
    save('installation.json', report)
    update_documents(report)
    print('INSTALLED: 11 assets verified by SHA-256. Staging binaries removed; editing sources retained.')
    print('Active shiparch unchanged: user must generate the already applied Pythonlancer configuration.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else plan()

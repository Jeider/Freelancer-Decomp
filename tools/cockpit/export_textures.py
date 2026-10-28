"""Read-only cockpit texture export: lossless PNG, original blobs and round-trip map."""
import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import shutil
import struct
import sys

from PIL import Image

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / 'tools'))
from generate_station_lods import read_tree


def digest(data):
    return hashlib.sha256(data).hexdigest()


def walk(nodes, prefix=''):
    for node in nodes:
        path = prefix + '/' + node.name
        yield path, node
        yield from walk(node.children, path)


def filename(name):
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name).strip('.') or 'texture'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path('D:/games/FL_MOD/DATA'))
    parser.add_argument('--out', type=Path, default=REPO / 'src/obj/cockpit_textures')
    args = parser.parse_args()
    data, out = args.data.resolve(strict=True), args.out.resolve()
    root = data / 'COCKPITS'
    if out.exists():
        raise FileExistsError(f'Refusing to overwrite an existing export: {out}')
    if out.is_relative_to(data):
        raise ValueError('Export must be outside game DATA')

    configs = {}
    for ini in sorted(root.rglob('*.ini')):
        for line in ini.read_text(encoding='utf-8-sig').splitlines():
            match = re.match(r'\s*mesh\s*=\s*([^;]+)', line, re.I)
            if match:
                model = match[1].strip().replace('\\', '/').lower()
                configs.setdefault(model, []).append(ini.relative_to(data).as_posix())

    records, sources, unique = [], [], {}
    for source in sorted(root.rglob('*')):
        if source.suffix.lower() not in ('.cmp', '.3db', '.mat', '.txm'):
            continue
        raw = source.read_bytes()
        nodes = list(walk(read_tree(raw)[1]))
        rel = source.relative_to(data).as_posix()
        source_entry = dict(file=rel, sha256=digest(raw), configs=configs.get(rel.lower(), []))
        sources.append(source_entry)
        local_names = set()
        for lib_path, lib in nodes:
            if lib.name.lower() != 'texture library':
                continue
            for tex in lib.children:
                blobs = {n.name.lower(): n for n in tex.children if n.blob is not None}
                selected = blobs.get('mips') or blobs.get('mip0')
                if selected is None:
                    raise ValueError(f'No base mip: {rel}: {tex.name}')
                local_names.add(tex.name.lower())
                with Image.open(io.BytesIO(selected.blob)) as decoded:
                    original_format = decoded.format
                    rgba = decoded.convert('RGBA')
                pixels = rgba.tobytes()
                pixel_hash = digest(struct.pack('<II', *rgba.size) + pixels)
                if pixel_hash not in unique:
                    png = Path('PNG') / (filename(tex.name) + '__' + pixel_hash[:12] + '.png')
                    target = out / png
                    target.parent.mkdir(parents=True, exist_ok=True)
                    rgba.save(target)
                    with Image.open(target) as check:
                        assert check.size == rgba.size and check.convert('RGBA').tobytes() == pixels
                    unique[pixel_hash] = png.as_posix()

                # Keep the container extension in the directory to avoid stem collisions.
                model_dir = source.relative_to(root)
                per_model = Path('BY_COCKPIT') / model_dir / (filename(tex.name) + '.png')
                target = out / per_model
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    raise ValueError(f'Duplicate output path: {target}')
                shutil.copyfile(out / unique[pixel_hash], target)
                originals = []
                for leaf in tex.children:
                    if leaf.blob is None:
                        raise ValueError(f'Unexpected texture subtree: {rel}: {tex.name}')
                    extension = '.dds' if leaf.blob.startswith(b'DDS ') else (
                        '.tga' if re.fullmatch(r'MIP\d+', leaf.name, re.I) else '.bin')
                    path = Path('ORIGINALS') / model_dir / filename(tex.name) / (filename(leaf.name) + extension)
                    target = out / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(leaf.blob)
                    assert digest(target.read_bytes()) == digest(leaf.blob)
                    originals.append(dict(node=leaf.name, file=path.as_posix(), sha256=digest(leaf.blob)))
                alpha_min, alpha_max = rgba.getchannel('A').getextrema()
                records.append(dict(source=rel, texture=tex.name,
                    utf_path=lib_path + '/' + tex.name, base_mip=selected.name,
                    format=original_format, width=rgba.width, height=rgba.height,
                    alpha_min=alpha_min, alpha_max=alpha_max, pixel_sha256=pixel_hash,
                    png=unique[pixel_hash], by_cockpit=per_model.as_posix(), originals=originals))

        refs = {n.blob.split(b'\0')[0].decode('ascii').lower()
                for path, n in nodes if '/material library/' in path.lower()
                and n.blob and n.name.lower().endswith('_name')}
        if refs - local_names:
            raise ValueError(f'External textures need resolving: {rel}: {sorted(refs - local_names)}')

    if not records:
        raise ValueError('No cockpit textures found')
    for source in sources:
        assert digest((data / source['file']).read_bytes()) == source['sha256'], 'Source changed during export'
    manifest = dict(data_root=str(data), sources=sources, textures=records,
                    unique_pngs=len(unique), source_containers=len(sources), texture_entries=len(records))
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
    columns = ['source', 'texture', 'width', 'height', 'alpha_min', 'alpha_max', 'png', 'by_cockpit']
    with (out / 'textures.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
    (out / 'README.txt').write_text(
        'Текстуры кабин Freelancer для апскейла\n\n'
        f'Источник: {root}\n'
        f'Моделей: {len(sources)}; текстурных записей: {len(records)}; уникальных PNG: {len(unique)}.\n\n'
        'PNG — набор без дубликатов: удобно передать апскейлеру целиком.\n'
        'BY_COCKPIT — те же изображения, разложенные по исходным моделям кабин.\n'
        'ORIGINALS — точные копии DDS/TGA из контейнеров, включая исходные mip-уровни.\n'
        'manifest.json — пути моделей, узлов UTF, исходные имена, хеши и соответствия PNG.\n'
        'textures.csv — таблица размеров и соответствий для просмотра.\n\n'
        'PNG сохранены в исходном разрешении, RGBA, без апскейла и переворота изображения.\n'
        'Одинаковое имя текстуры может означать разные картинки: суффиксы в PNG сохраняйте.\n'
        'Для возврата в игру сохраняйте имена PNG и альфа-канал; увеличивайте обе стороны\n'
        'в одинаковое число раз. После апскейла потребуется перекодирование в DDS,\n'
        'генерация mip-уровней и упаковка обратно в указанные узлы CMP.\n'
        'Включены все модели из COCKPITS, в том числе альтернативные MODELSA и *_red.\n'
        'Исходные игровые файлы не изменены.\n', encoding='utf-8-sig')
    print(json.dumps(dict(output=str(out), models=len(sources), texture_entries=len(records),
                          unique_pngs=len(unique), verified='PNG pixels, original blobs, unchanged source files'),
                     ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

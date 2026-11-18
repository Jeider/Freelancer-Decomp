"""Keep Blender's working files and cache inside the selected output topic.

Example: python tools/blender_workspace.py --topic base_interiors
         --script tools/base_interiors/rheinland_inspect.py -- rh_depot_deck
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BLENDER = Path('C:/Program Files/Blender Foundation/Blender 5.2/blender.exe')


def configure(topic):
    if not re.fullmatch(r'[a-z0-9_]+', topic):
        raise ValueError('Expected a single output topic name')
    cache = (ROOT / 'out' / topic / 'tool_cache/blender').resolve()
    if not cache.is_relative_to(ROOT / 'out'):
        raise ValueError('Blender cache escapes the output tree')
    cache.mkdir(parents=True, exist_ok=True)
    for variable, subfolder in (('XDG_CACHE_HOME', 'cache'),
                                ('OPTIX_CACHE_PATH', 'optix'),
                                ('CUDA_CACHE_PATH', 'cuda')):
        target = cache / subfolder
        target.mkdir(exist_ok=True)
        os.environ[variable] = str(target)
    os.chdir(cache)
    # The working directory is the main protection even when a thumbnail
    # backend misreads a path. Disable unnecessary .blend previews as well.
    bpy = sys.modules.get('bpy')
    if bpy is not None:
        prefs = bpy.context.preferences.filepaths
        prefs.save_version = 0
        prefs.file_preview_type = 'NONE'
    return cache


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--topic', required=True)
    parser.add_argument('--script', required=True, type=Path)
    parser.add_argument('script_args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    script = args.script.resolve(strict=True)
    if not script.is_relative_to(ROOT / 'tools'):
        raise ValueError('Expected a script under the repository tools directory')
    cache = configure(args.topic)
    bootstrap = ('import sys;sys.path.insert(0,' + repr(str(ROOT / 'tools')) +
                 ');from blender_workspace import configure;configure(' + repr(args.topic) + ')')
    extra = args.script_args[1:] if args.script_args[:1] == ['--'] else args.script_args
    command = [str(BLENDER), '--background', '--python-exit-code', '1',
               '--python-expr', bootstrap, '--python', str(script)]
    if extra:
        command += ['--', *extra]
    return subprocess.run(command, cwd=cache, check=False).returncode


if __name__ == '__main__':
    raise SystemExit(main())

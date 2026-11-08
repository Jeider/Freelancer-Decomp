"""Prepare an additive update of Pythonlancer's authoritative tools.data_folder.

The preview is installed unchanged; this module never writes game DATA itself.
"""
from pathlib import Path
import importlib.util

RULE = '''## DATA writes

Pythonlancer may write to the game's DATA directory only through
`tools.data_folder`. Extend `DataFolder` with the necessary methods for new
content. Generators and installers must not write, copy, move or delete DATA
files directly. Use the same entry point for staged DATA output and rollback.
Direct reads are allowed.
'''

METHODS = '''    # Central DATA output API, also used for staging and installation rollback.
    def data_path(self, relative):
        relative = pathlib.Path(str(relative).replace('\\\\', '/'))
        if (relative.is_absolute() or relative.drive or not relative.parts or
                '..' in relative.parts or any(':' in part for part in relative.parts)):
            raise ValueError('Expected a path relative to DATA: ' + str(relative))
        root = (self.get_root() / 'DATA').resolve()
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or target == root:
            raise ValueError('Path escapes DATA: ' + str(relative))
        return target

    def sync_data_file(self, relative, content):
        target = self.data_path(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            target.write_text(content, encoding='utf-8')
        else:
            target.write_bytes(content)
        return target

    def remove_data_file(self, relative):
        # Only an individual DATA file; never remove a directory recursively.
        self.data_path(relative).unlink(missing_ok=True)

    def sync_ship_parking(self, files):
        for relative in files:
            name = str(relative).replace('\\\\', '/')
            if not (name in ('RPG/ship_parking.ini', 'RPG/parking_contacts.ini') or
                    (name.startswith('RPG/parking/') and name.endswith('.ini'))):
                raise ValueError('Unexpected ship parking file: ' + name)
            self.data_path(name)
        for relative, content in files.items():
            self.sync_data_file(relative, content)

'''


def prepare(game, stage):
    relative = 'Assets/Pythonlancer/tools/data_folder.py'
    original = (game / relative).read_bytes()
    newline = '\r\n' if b'\r\n' in original else '\n'
    source = original.decode('utf-8-sig').replace('\r\n', '\n')
    if '    def sync_ship_parking(self, files):' not in source:
        old = ('    def __init__(self, build_to_folder=None):\n'
               '        self.root = pathlib.Path().resolve().parent.parent\n')
        new = ('    def __init__(self, build_to_folder=None, *, root=None):\n'
               '        self.root = pathlib.Path(root).resolve() if root is not None else pathlib.Path().resolve().parent.parent\n')
        assert source.count(old) == 1, 'DataFolder constructor changed; update the additive patch'
        source = source.replace(old, new, 1)
        anchor = '    def get_root(self):\n'
        assert source.count(anchor) == 1
        source = source.replace(anchor, METHODS + anchor, 1)
    compile(source, relative, 'exec')
    target = stage / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.replace('\n', newline).encode('utf-8'))
    instructions = 'Assets/Pythonlancer/AGENTS.md'
    path = game / instructions
    text = path.read_text(encoding='utf-8-sig') if path.exists() else '# Pythonlancer agent instructions\n'
    if RULE not in text:
        text = text.rstrip() + '\n\n' + RULE
    (stage / instructions).write_text(text, encoding='utf-8')
    spec = importlib.util.spec_from_file_location('parking_data_folder_preview', target)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFolder, (relative, instructions)

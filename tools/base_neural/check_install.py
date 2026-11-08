"""Exercise install/rollback and concurrent-build guards in a tiny workspace fixture."""
from pathlib import Path
import json
import sys
import tempfile
import install

def main():
    root=Path(tempfile.mkdtemp(prefix='install_',dir=install.OUT/'checks')).resolve()
    assert root.is_relative_to((install.OUT/'checks').resolve())
    install.OUT=root/'stage'
    game=root/'game';payload=install.OUT/'package'
    (game/'bin').mkdir(parents=True);(payload/'bin').mkdir(parents=True)
    (game/'bin/core.dll').write_bytes(b'original core')
    (game/'bin/port.ini').write_bytes(b'[Language]\nlanguage=ru\n')
    files={}
    for name,data in [('core.dll',b'new core'),('adapter.dll',b'optional module'),('port.ini',b'[BaseNeural]\nenabled=1\n')]:
        rel='bin/'+name;(payload/rel).write_bytes(data)
        files[rel]={'before':install.digest(game/rel),'after':install.digest(payload/rel)}
    manifest={'game':str(game),'files':files,'dependencies':{}}
    (install.OUT/'package.json').write_text(json.dumps(manifest))
    install.stopped=lambda:None # This fixture contains no executable processes.
    def run(*args):
        sys.argv=['install.py',*args];install.main()
    run('--apply')
    backup=next((install.OUT/'backups').iterdir())
    assert (game/'bin/core.dll').read_bytes()==b'new core'
    # A different agent's binary must block rollback before any file changes.
    (game/'bin/core.dll').write_bytes(b'other build')
    try:run('--restore',str(backup),'--apply')
    except RuntimeError as exc:assert 'changed since installation' in str(exc)
    else:raise AssertionError('Concurrent build was overwritten')
    assert (game/'bin/adapter.dll').exists()
    (game/'bin/core.dll').write_bytes(b'new core')
    (game/'bin/port.ini').write_bytes(b'changed runtime settings')
    run('--restore',str(backup),'--apply')
    assert (game/'bin/core.dll').read_bytes()==b'original core'
    assert (game/'bin/port.ini').read_bytes()==b'[Language]\nlanguage=ru\n'
    assert not (game/'bin/adapter.dll').exists()
    assert (backup/'runtime_config/bin/port.ini').read_bytes()==b'changed runtime settings'
    try:install.path_under(game,'../../outside.dll')
    except RuntimeError:pass
    else:raise AssertionError('Path traversal accepted')
    print('PASS fixture install, rollback, changed-binary protection, config preservation, path containment')

if __name__=='__main__':main()

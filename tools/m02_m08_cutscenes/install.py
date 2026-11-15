"""Add scene assets and merge only imports/THORN bindings into live scripts."""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
BUNDLE = ROOT / 'bundle'
ASSETS = Path('D:/Games/FL_MOD/Assets')
PREP = ROOT / 'install_prepared'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def merge(original, staged):
    current = ast.parse(original)
    desired = ast.parse(staged)
    classes = {n.name:n for n in current.body if isinstance(n, ast.ClassDef)}
    edits = []
    modules = set()
    additions = []
    for node in desired.body:
        if not isinstance(node, ast.ClassDef) or node.name not in classes:
            continue
        live = classes[node.name]
        existing = {s.targets[0].id:s for s in live.body if isinstance(s, ast.Assign) and isinstance(s.targets[0], ast.Name)}
        for s in node.body:
            if not isinstance(s, ast.Assign) or not isinstance(s.targets[0], ast.Name): continue
            key = s.targets[0].id
            if not key.startswith('THORN_'): continue
            if key in existing:
                if ast.dump(existing[key].value) != ast.dump(s.value):
                    raise RuntimeError(f'Existing binding differs: {node.name}.{key}')
                continue
            assert isinstance(s.value, ast.Attribute) and isinstance(s.value.value, ast.Name)
            modules.add(s.value.value.id)
            additions.append((node.name,key))
            edits.append((live.lineno, '    '+ast.unparse(s)))
    newline = '\r\n' if b'\r\n' in original else '\n'
    lines = original.decode('utf-8-sig').splitlines(keepends=True)
    for lineno, text in sorted(edits, key=lambda item:item[0], reverse=True):
        lines.insert(lineno, text+newline)
    if modules:
        lines.insert(0, 'from story.cutscenes.story_scenes import '+', '.join(sorted(modules))+newline)
    result = ''.join(lines).encode('utf-8')
    if original.startswith(b'\xef\xbb\xbf'): result=b'\xef\xbb\xbf'+result
    # Removing precisely the additions must reproduce the original entire AST.
    stripped = ast.parse(result)
    if modules: stripped.body.pop(0)
    for node in stripped.body:
        if isinstance(node,ast.ClassDef):
            node.body=[s for s in node.body if not (isinstance(s,ast.Assign) and isinstance(s.targets[0],ast.Name) and (node.name,s.targets[0].id) in additions)]
    assert ast.dump(stripped)==ast.dump(current), 'Unexpected mission edit'
    return result, len(additions)

def prepare():
    PREP.mkdir(exist_ok=True)
    plan=[]
    skipped=[]
    bindings=0
    for source in sorted((BUNDLE/'Pythonlancer').rglob('*.py')):
        relative=source.relative_to(BUNDLE)
        target=ASSETS/relative
        incoming=source.read_bytes()
        is_script=relative.parts[1:4]==('story','scripts','main')
        before=target.read_bytes() if target.exists() else None
        if is_script:
            assert before is not None
            incoming,count=merge(before,incoming)
            bindings+=count
        elif before is not None and before!=incoming:
            raise RuntimeError(f'Will not overwrite existing asset: {target}')
        if before==incoming:
            skipped.append(str(target)); continue
        plan.append((relative,incoming,before))
    for source in sorted((BUNDLE/'SCENES').rglob('*')):
        if not source.is_file() or source.suffix not in ('.blend','.json'): continue
        relative=source.relative_to(BUNDLE);target=ASSETS/relative
        incoming=source.read_bytes()
        before=target.read_bytes() if target.exists() else None
        if before is not None:
            if before!=incoming: raise RuntimeError(f'Will not overwrite existing asset: {target}')
            skipped.append(str(target));continue
        plan.append((relative,incoming,before))
    manifest=[]
    for relative,data,before in plan:
        staged=PREP/'new'/relative
        staged.parent.mkdir(parents=True,exist_ok=True);staged.write_bytes(data)
        if before is not None:
            backup=PREP/'previous'/relative
            if backup.exists() and backup.read_bytes()!=before: raise RuntimeError(f'Backup conflict: {backup}')
            backup.parent.mkdir(parents=True,exist_ok=True);backup.write_bytes(before)
        manifest.append(dict(path=relative.as_posix(),old=sha(before) if before is not None else None,new=sha(data)))
    (PREP/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(f'Prepared: {sum(x["old"] is None for x in manifest)} additions, {sum(x["old"] is not None for x in manifest)} mission scripts, {bindings} bindings. Unchanged: {len(skipped)}.')

def apply():
    manifest=json.loads((PREP/'manifest.json').read_text())
    for entry in manifest:
        target=ASSETS/entry['path']; staged=PREP/'new'/entry['path']
        assert sha(staged.read_bytes())==entry['new']
        current=sha(target.read_bytes()) if target.exists() else None
        assert current in (entry['old'],entry['new']), f'Changed since preparation: {target}'
    for entry in manifest:
        target=ASSETS/entry['path']
        if target.exists() and sha(target.read_bytes())==entry['new']: continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if entry['old'] is None:
            with target.open('xb') as output: output.write((PREP/'new'/entry['path']).read_bytes())
        else:
            target.write_bytes((PREP/'new'/entry['path']).read_bytes())
        assert sha(target.read_bytes())==entry['new']
    print(f'Installed and hash-verified {len(manifest)} files. No DATA or final THN writes.')

if '--prepare' in sys.argv: prepare()
elif '--apply' in sys.argv: apply()
else: raise SystemExit('Use --prepare or --apply')

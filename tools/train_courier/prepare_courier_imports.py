"""Link this courier build against the installed Common DLL; no game writes."""
import importlib.util
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]

if __name__ == '__main__':
    path = ROOT / 'tools/room_materials/import_installed.py'
    spec = importlib.util.spec_from_file_location('installed_common_imports', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.OUT = ROOT / 'out/train_courier/audio_ru/imports'
    module.main()
    destination = ROOT / 'src/obj/train_courier/rpg1/bin/Common.lib'
    shutil.copyfile(module.OUT / 'Common.lib', destination)

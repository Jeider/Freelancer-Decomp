"""Use Pythonlancer's central DATA API for staging, install and rollback."""
import importlib.util
import sys


def data_folder(game, root):
    source=game/'Assets/Pythonlancer/tools/data_folder.py'
    spec=importlib.util.spec_from_file_location('courier_pythonlancer_data_folder',source)
    module=importlib.util.module_from_spec(spec)
    previous=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode=previous
    return module.DataFolder(root=root)

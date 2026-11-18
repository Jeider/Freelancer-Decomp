"""Read-only diagnostics for the emotion engine's first model load."""
from pathlib import Path
root=Path('C:/Users/Freel/AppData/Roaming/OmniVoice/engines/indextts2/index-tts-2.5')
for path in sorted((root/'checkpoints/hf_cache').rglob('*')):
    if path.is_file():
        info=path.stat();print(path.relative_to(root),info.st_size,info.st_mtime)
source=(root/'indextts/utils/model_download.py').read_text(encoding='utf-8').splitlines()
for start,end in ((1,94),(158,176),(228,265)):
    print('\n'.join(f'{i+1}: {line}' for i,line in enumerate(source) if start<=i+1<=end))

"""Compress the supplied clip and pack JPEG frames for an embedded RCDATA resource."""
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('D:/work/junko.mp4')
OUT = ROOT / 'out/shader_startup/animation'
TARGET = ROOT / 'src/freelancer/resources/shader_startup/junko.frames'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    avi = OUT / 'junko.avi'
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(SOURCE),
                    '-an', '-vf', 'fps=24,scale=480:480:flags=lanczos', '-c:v', 'mjpeg',
                    '-q:v', '8', '-pix_fmt', 'yuvj420p', '-threads', '2', str(avi)], check=True)
    packets = json.loads(subprocess.check_output([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_packets',
        '-show_entries', 'packet=pos,size', '-of', 'json', str(avi)]))['packets']
    raw = avi.read_bytes()
    frames = [raw[int(p['pos']):int(p['pos']) + int(p['size'])] for p in packets]
    assert frames and all(f.startswith(b'\xff\xd8') and f.endswith(b'\xff\xd9') for f in frames)
    header = struct.pack('<4s6I', b'FLJA', 1, 480, 480, 24, 1, len(frames))
    offset = len(header) + 4 * (len(frames) + 1)
    offsets = [offset]
    for frame in frames:
        offsets.append(offsets[-1] + len(frame))
    data = header + struct.pack(f'<{len(offsets)}I', *offsets) + b''.join(frames)
    TARGET.write_bytes(data)
    report = {'source': str(SOURCE), 'source_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              'source_bytes': SOURCE.stat().st_size, 'resource': str(TARGET),
              'resource_sha256': hashlib.sha256(data).hexdigest(), 'resource_bytes': len(data),
              'width': 480, 'height': 480, 'fps': 24, 'frames': len(frames),
              'duration': len(frames) / 24, 'audio': False}
    (OUT / 'encoding.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    # Only the embedded source asset is needed after packing; retain the user's MP4.
    assert avi.resolve().is_relative_to(OUT.resolve())
    assert not any(p.is_symlink() or p.is_junction() for p in (avi, *avi.parents))
    avi.unlink()
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()

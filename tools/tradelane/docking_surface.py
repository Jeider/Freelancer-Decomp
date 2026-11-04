"""Build and verify the missing parent SUR for the composite Trade_Lane_Ring.

The visible tlr_legal_lod5.cmp is attached below tlr_root.3db. Archetype::Root
loads surfaces by the parent filename, so without tlr_root.sur the parent gets
PhyArch's 1-metre default box. Dock then measures the approach against that box
instead of the ring and can reset states 1/2 forever just outside 1050 metres.

Only the SUR root-part id changes: the attached model uses Cmpnd/Root, while the
parent 3DB's root part is id 0 (the same convention as retail tlr_lod.sur).
"""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
SOURCE_REL = Path('DATA/SOLAR/DOCKABLE/tlr_legal_lod5.sur')
TARGET_REL = Path('DATA/SOLAR/DOCKABLE/tlr_root.sur')
OUTPUT = ROOT / 'out/tradelane_docking/tlr_root.sur'
SOURCE_PART_ID = 0x12688F2D  # DACOM CRC of "Root"
PARENT_PART_ID = 0


def parts(data):
    """Yield (part id, chunks), validating the complete SUR container."""
    if len(data) < 16 or data[:4] != b'vers' or struct.unpack_from('<f', data, 4)[0] != 2.0:
        raise ValueError('Expected a version 2.0 SUR')
    offset = 8
    result = []
    while offset < len(data):
        if offset + 8 > len(data):
            raise ValueError('Truncated SUR part header')
        part_id, chunk_count = struct.unpack_from('<II', data, offset)
        offset += 8
        chunks = []
        for _ in range(chunk_count):
            if offset + 4 > len(data):
                raise ValueError('Truncated SUR chunk')
            tag = data[offset:offset + 4]
            offset += 4
            if tag == b'exts':
                if offset + 24 > len(data):
                    raise ValueError('Truncated SUR extents')
                chunks.append((tag, data[offset:offset + 24]))
                offset += 24
            elif tag == b'surf':
                if offset + 4 > len(data):
                    raise ValueError('Truncated SUR surface size')
                size, = struct.unpack_from('<I', data, offset)
                offset += 4
                if offset + size > len(data):
                    raise ValueError('Truncated SUR surface')
                chunks.append((tag, data[offset:offset + size]))
                offset += size
            elif tag == b'hpid':
                if offset + 4 > len(data):
                    raise ValueError('Truncated SUR hardpoint count')
                count, = struct.unpack_from('<I', data, offset)
                offset += 4
                if offset + count * 4 > len(data):
                    raise ValueError('Truncated SUR hardpoints')
                chunks.append((tag, data[offset:offset + count * 4]))
                offset += count * 4
            elif tag == b'!fxd':
                chunks.append((tag, b''))
            else:
                raise ValueError(f'Unknown SUR chunk {tag!r}')
        result.append((part_id, chunks))
    return result


def build(source):
    parsed = parts(source)
    if len(parsed) != 1 or parsed[0][0] != SOURCE_PART_ID:
        raise ValueError('Unexpected attached-model SUR root')
    tags = {tag for tag, _ in parsed[0][1]}
    if not {b'exts', b'surf', b'!fxd'} <= tags:
        raise ValueError('Attached-model SUR lacks fixed geometry/extents')
    result = bytearray(source)
    struct.pack_into('<I', result, 8, PARENT_PART_ID)
    if parts(result)[0][0] != PARENT_PART_ID:
        raise AssertionError('Parent part id was not patched')
    return bytes(result)


def extents(data):
    part_list = parts(data)
    values = [chunk for _, chunks in part_list for tag, chunk in chunks if tag == b'exts']
    if len(values) != 1:
        raise ValueError('Expected one root extents record')
    return struct.unpack('<6f', values[0])


def main():
    parser = ArgumentParser()
    parser.add_argument('--check', type=Path, help='verify an installed/prepared tlr_root.sur')
    parser.add_argument('--game', type=Path, default=GAME)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    args = parser.parse_args()
    source = (args.game / SOURCE_REL).read_bytes()
    expected = build(source)
    if args.check:
        actual = args.check.read_bytes()
        if actual != expected:
            raise SystemExit('FAIL: tlr_root.sur differs from the attached-model surface')
        print('PASS: installed tlr_root.sur matches the expected parent surface')
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(expected)
        if args.output.read_bytes() != expected:
            raise SystemExit('FAIL: prepared SUR readback mismatch')
        print(args.output)
    minimum = extents(expected)[:3]
    maximum = extents(expected)[3:]
    if not all(maximum[i] - minimum[i] > 40 for i in range(3)):
        raise SystemExit('FAIL: parent extents are not the real ring geometry')
    print('root part: 0; extents:', minimum, maximum)
    print('sha256:', sha256(expected).hexdigest().upper())


if __name__ == '__main__':
    main()

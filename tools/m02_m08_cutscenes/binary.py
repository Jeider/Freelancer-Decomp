"""Restricted Lua 3.2 table bytecode decoder; rejects calls and control flow.

Format and opcode semantics: src/Thorn/lua32/src/{lundump.c,lopcodes.h,lvm.c}.
No Lua code is executed and no native functions are available.
"""
import struct

def read_binary(raw):
    offset = 0
    def take(n):
        nonlocal offset
        result = raw[offset:offset+n]
        if len(result) != n:
            raise ValueError('Truncated bytecode')
        offset += n
        return result
    def integer():
        return int.from_bytes(take(4), 'big')
    def string():
        n = integer()
        return take(n)[:-1].decode('cp1251') if n else None
    assert take(5) == b'\x1bLua2'
    native = take(1)[0]
    assert native in (0, 4, 8)
    if native:
        take(native)
    integer()
    string()
    code = take(integer())
    for _ in range(integer()):
        integer(); string()
    constants = []
    for _ in range(integer()):
        kind = take(1)[0]
        if kind == 1:
            constants.append(struct.unpack('<f' if native == 4 else '<d', take(native))[0]
                             if native else float(take(take(1)[0]).decode('ascii')))
        elif kind == 2:
            constants.append(string())
        elif kind == 6:
            constants.append(None)
        else:
            raise ValueError(f'Unsupported constant type {kind}')
    assert offset == len(raw), (offset, len(raw))
    stack, globals_ = [], {}
    pc = 2  # max stack and fixed parameter count
    while pc < len(code):
        op = code[pc]; pc += 1
        if op == 0:
            break
        if op == 37:  # ADDOP; symbolic flag union
            b, a = stack.pop(), stack.pop()
            stack.append(a+b if isinstance(a, (int,float)) and isinstance(b,(int,float)) else f'{a}+{b}')
            continue
        widths = {6:2,7:1,8:2,9:1,10:2,11:1,14:2,15:1,21:2,22:1,24:2,25:1,28:2,29:1,30:1}
        if op not in widths:
            raise ValueError(f'Unsupported opcode {op} at {pc-1}')
        width = widths[op]
        arg = int.from_bytes(code[pc:pc+width], 'big'); pc += width
        if op in (6,7,8,9): stack.append(arg if op < 8 else -arg)
        elif op in (10,11): stack.append(constants[arg])
        elif op in (14,15): stack.append(globals_.get(constants[arg], constants[arg]))
        elif op in (21,22): stack.append({})
        elif op in (24,25): globals_[constants[arg]] = stack.pop()
        elif op in (28,29):
            n = code[pc]; pc += 1
            table = stack[-n-1]
            for i in range(n,0,-1): table[arg*64+i] = stack.pop()
        elif op == 30:
            table = stack[-2*(arg+1)-1]
            for _ in range(arg+1):
                value, key = stack.pop(), stack.pop()
                table[key] = value
    assert not stack
    def normalize(value):
        if isinstance(value, dict):
            if value and set(value) == set(range(1,len(value)+1)):
                return [normalize(value[i]) for i in range(1,len(value)+1)]
            return {k:normalize(v) for k,v in value.items()}
        return value
    return {k:normalize(globals_[k]) for k in ('duration','entities','events')}

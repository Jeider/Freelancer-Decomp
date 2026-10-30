"""Decompile selected Beta functions and their immediate local callees in IDA."""
from pathlib import Path
import ida_auto, ida_funcs, ida_hexrays, ida_pro, idautils, idc
out = Path('D:/work/Freelancer-Decomp/src/obj/route_autopilot/beta')
ida_auto.auto_wait()
ida_hexrays.init_hexrays_plugin()
roots = [int(arg, 16) for arg in idc.ARGV[1:]]
import json
names = [(hex(ea), name) for ea, name in idautils.Names() if 'MiniPath' in name]
(out/'mini_names.json').write_text(json.dumps(names, indent=2))
for ea, name in names:
    address = int(ea, 16)
    if 'vftable' in name or '??_7MiniPath' in name:
        for ref in idautils.DataRefsTo(address):
            func = ida_funcs.get_func(ref)
            if func: roots.append(func.start_ea)
        for offset in range(0, 32, 4):
            func = ida_funcs.get_func(idc.get_wide_dword(address + offset))
            if func: roots.append(func.start_ea)
todo = set(roots)
for ea in roots:
    for addr in idautils.FuncItems(ea):
        if idc.print_insn_mnem(addr) == 'call':
            for target in idautils.CodeRefsFrom(addr, False):
                if ida_funcs.get_func(target) and 0x6E00000 <= target < 0x6F40000:
                    todo.add(target)
for ea in sorted(todo):
    try:
        text = '// %s\n%s' % (hex(ea), ida_hexrays.decompile(ea))
    except Exception as exc:
        text = '// %s: %s' % (hex(ea), exc)
    (out/('%08x.c' % ea)).write_text(text)
ida_pro.qexit(0)

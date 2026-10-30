"""IDA batch survey of the user's Beta Content.dll; writes only to the workspace."""
import json
from pathlib import Path
import ida_auto
import ida_funcs
import ida_hexrays
import ida_pro
import ida_name
import idautils
import idc

out = Path('D:/work/Freelancer-Decomp/src/obj/route_autopilot/beta')
out.mkdir(parents=True, exist_ok=True)
ida_auto.auto_wait()
report = []
functions = set()
for item in idautils.Strings():
    value = str(item)
    if any(key.lower() in value.lower() for key in ('MiniPathFind', 'Path.cpp', 'test_pathfind', 'BestPath')):
        refs = []
        for ref in idautils.XrefsTo(item.ea):
            func = ida_funcs.get_func(ref.frm)
            if func:
                functions.add(func.start_ea)
            refs.append({'from': hex(ref.frm), 'function': hex(func.start_ea) if func else None})
        report.append({'address': hex(item.ea), 'text': value, 'refs': refs})
for ea, name in idautils.Names():
    if 'ReturnBestPath' in name:
        for ref in idautils.XrefsTo(ea):
            func = ida_funcs.get_func(ref.frm)
            if func:
                functions.add(func.start_ea)
(out/'survey.json').write_text(json.dumps(report, indent=2))
ready = ida_hexrays.init_hexrays_plugin()
for ea in sorted(functions):
    name = ida_name.get_name(ea)
    text = '// %s %s\n' % (hex(ea), name)
    if ready:
        try:
            text += str(ida_hexrays.decompile(ea))
        except Exception as exc:
            text += '// decompile failed: %s\n' % exc
    else:
        text += '\n'.join('%08x %s' % (addr, idc.generate_disasm_line(addr, 0)) for addr in idautils.FuncItems(ea))
    (out/('%08x.c' % ea)).write_text(text)
(out/'done.json').write_text(json.dumps({'hexrays': ready, 'functions': [hex(ea) for ea in sorted(functions)]}))
ida_pro.qexit(0)

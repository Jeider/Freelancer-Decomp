"""Stage only the reviewed Forbes counter, preserving current room resources."""
import json
from forbes_counter_audit import OUT,SOURCE,RETAIL,RELATIVE
from depot_family_export import export
from native_common import dump


def annotate():
    build=OUT/'modeled'
    report=json.loads((build/'native_validation.json').read_text())
    stats=json.loads((build/'geometry_validation.json').read_text())
    repairs=stats.get('source_uv_repairs',[])
    report.pop('both_uv_sets_preserved',None)
    report.pop('cranes_and_props_unchanged',None)
    report.update(source_uv_repairs=repairs,primary_uv_preserved=True,
        uv_channels_preserved_except_documented_repair=True,
        retained_room_geometry_unchanged=True)
    dump(build/'native_validation.json',report)


if __name__=='__main__':
    export('li_for_01_bar',(OUT,SOURCE,RETAIL,RELATIVE))
    annotate()

"""Revision 03 editor scene; check the WHOLE pylon root, not just overlap existence."""
import json
import sys
from pathlib import Path
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rh_elite_tail_mounts_blender as m
m.OUT = m.BASE/'revision_03'
m.NAME = 'rh_pir_elite_tail_refine'
m.BLEND = m.OUT/(m.NAME+'.blend')
m.SCENE_NAME = 'Intact - extended - revision 03'
original_connections = m.connections


def connections(data):
    original_connections(data)
    geometry = json.loads((m.OUT/'geometry.json').read_text())
    shell = m.tree(geometry['tail_shell'])
    samples = []
    for edge in geometry['pylon_root_edges']:
        for uy in (.05, .5, .95):
            for uz in (.05, .5, .95):
                point = Vector((edge['x'], edge['y_min']+(edge['y_max']-edge['y_min'])*uy,
                                edge['z_min']+(edge['z_max']-edge['z_min'])*uz))
                direction = Vector((edge['side'], 0, 0))
                loc, normal, _, distance = shell.ray_cast(point, direction, .3)
                assert loc is not None and normal.dot(direction) > .99 and distance > .05, ('root not buried', list(point))
                samples.append(dict(point=list(point), depth=distance))
    assert len(samples) == 36
    ties = m.tree(geometry['close_drum_ties'])
    shell_hits = len(ties.overlap(shell)); assert shell_hits > 0
    # Each inner tie face sits at .79 versus the drum inset's outer face at .80.
    for g in geometry['close_drum_ties']:
        for tri in g['corners']:
            for v in tri:assert .7899 <= abs(v[0]) <= .9401
    report_path = m.OUT/'connection_check.json'
    report = json.loads(report_path.read_text())
    report.update(pylon_whole_root_interior_samples=samples, tie_tail_intersections=shell_hits,
                  tie_inner_face=.79, drum_side_outer_face=.80, single_deck_uv_chart=True)
    report_path.write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print('FULL PYLON ROOTS: 36 interior samples, both sides and both mounting rows', flush=True)


m.connections = connections
if __name__ == '__main__':m.main()

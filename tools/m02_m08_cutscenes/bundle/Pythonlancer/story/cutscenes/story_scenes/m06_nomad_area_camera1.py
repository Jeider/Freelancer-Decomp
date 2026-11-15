"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm06_nomad_area_camera1'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(25.0)
        obj_Path_1 = MotionPath(root=self, name='Path_1', point_name='Path_1', path_data='{-16000, -100, -26000}, {0.5,0,-0.5,0}, {-11400, 300, -25850}, {0.4,0,-0.6,0}')
        preserve_entity(obj_Path_1, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-16000, -100, -26000}, {0.5,0,-0.5,0}, {-11400, 300, -25850}, {0.4,0,-0.6,0},'}})
        obj_Shot06_Camera_0 = StaticCamera(root=self, name='Shot06_Camera_0', fov=35, farplane=100000)
        preserve_entity(obj_Shot06_Camera_0, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Shot06_Camera_0')
        # source event 1, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Shot06_Camera_0', 'Path_1'], duration=7, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION+ORIENTATION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        restore_dialogue(self)

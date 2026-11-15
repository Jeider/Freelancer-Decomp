"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_tortuga_wp_camera'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(10000.0)
        obj_Shot06_Camera_0 = LookAtCamera(root=self, name='Shot06_Camera_0', fov=35, farplane=100000, look_duration=30)
        preserve_entity(obj_Shot06_Camera_0, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Path_Camera = MotionPath(root=self, name='Path_Camera', point_name='Path_Camera', path_data='{19920, -1980, 5000}, {1,0,0,0}, {19990, -2000, 5000}, {1,0,0,0}')
        preserve_entity(obj_Path_Camera, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {19920, -1980, 5000}, {1,0,0,0}, {19990, -2000, 5000}, {1,0,0,0}'}})
        obj_Path_Marker = MotionPath(root=self, name='Path_Marker', point_name='Path_Marker', path_data='{19020, -1980, 5000}, {1,0,0,0}, {19090, -2000, 5000}, {1,0,0,0}')
        preserve_entity(obj_Path_Marker, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {19020, -1980, 5000}, {1,0,0,0}, {19090, -2000, 5000}, {1,0,0,0}'}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Shot06_Camera_0')
        # source event 2, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Shot06_Camera_0', 'Path_Camera'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 3, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Shot06_Camera_0_focus', 'Path_Marker'], duration=10, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        restore_dialogue(self)

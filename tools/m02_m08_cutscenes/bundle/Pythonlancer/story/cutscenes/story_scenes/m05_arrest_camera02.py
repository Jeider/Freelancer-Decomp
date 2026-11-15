"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_arrest_camera02'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(300.0)
        obj_Shot06_Camera_1 = LookAtCamera(root=self, name='Shot06_Camera_1', fov=35, farplane=100000, look_duration=50)
        preserve_entity(obj_Shot06_Camera_1, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 35, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Camera_1 = StaticCamera(root=self, name='Camera_1', fov=45, farplane=100000)
        preserve_entity(obj_Camera_1, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 45, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Path_1 = MotionPath(root=self, name='Path_1', point_name='Path_1', path_data='{-25,5,-5}, {1,0,0,0}, {-25,50,200}, {1,0,0,0}')
        preserve_entity(obj_Path_1, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {-25,5,-5}, {1,0,0,0}, {-25,50,200}, {1,0,0,0}, '}})
        obj_Path_mrk = MotionPath(root=self, name='Path_mrk', point_name='Path_mrk', path_data='{0, 0, 0}, {1,0,0,0}, {0,0,-50}, {1,0,0,0}')
        preserve_entity(obj_Path_mrk, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 0, 0}, {1,0,0,0}, {0,0,-50}, {1,0,0,0}, '}})
        obj_Path_mrk_static = MotionPath(root=self, name='Path_mrk_static', point_name='Path_mrk_static', path_data='{0, 0.1, 0}, {1,0,0,0}, {0,0,0}, {1,0,0,0}')
        preserve_entity(obj_Path_mrk_static, {'template_name': '', 'template_id': 0, 'pathprops': {'path_type': 'CV_CROrientationSplinePath', 'path_data': 'OPEN, {0, 0.1, 0}, {1,0,0,0}, {0,0,0}, {1,0,0,0}, '}})
        preserve_entity(self.get_entity('automarker_main_object'), userprops={'main_object': 'main_object'})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Shot06_Camera_1')
        # source event 2, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Path_1', 'automarker_main_object'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 3, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Path_mrk', 'automarker_main_object'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 4, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Path_mrk_static', 'automarker_main_object'], duration=50, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 5, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Shot06_Camera_1', 'Path_1'], duration=20, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        # source event 6, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Shot06_Camera_1_focus', 'Path_mrk'], duration=30, start_percent=0, stop_percent=1, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', flags='POSITION', param_curve={'CLSID': 'FreeFormPCurve', 'points': [[0, 0, 0, 0], [1, 1, 0, 0]]}, pcurve_period=-1000)
        restore_dialogue(self)

"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_rh_cruiser_1(Ship):
    COMPOUND_TEMPLATE_NAME = 'rh_cruiser'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm01b_armored_trap_camera'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(54.375)
        obj_CnB_Camera_00 = StaticCamera(root=self, name='CnB_Camera_00', fov=35, farplane=100000.0)
        preserve_entity(obj_CnB_Camera_00, {'cameraprops': {'farplane': 100000.0, 'nearplane': 0.1, 'hvaspect': 1.333333, 'fovh': 35}, 'template_id': 0, 'template_name': ''})
        obj_CnB_Camera_01 = StaticCamera(root=self, name='CnB_Camera_01', fov=35, farplane=100000.0)
        preserve_entity(obj_CnB_Camera_01, {'cameraprops': {'farplane': 100000.0, 'nearplane': 0.1, 'hvaspect': 1.333333, 'fovh': 35}, 'template_id': 0, 'template_name': ''})
        obj_aa_depot_Path = MotionPath(root=self, name='aa_depot_Path', point_name='aa_depot_Path', path_data='{85.947334,45.790657,136.607208}, {0.269080,0.925089,-0.113638,-0.242676}, {-50.846935,23.158363,185.705719}, {0.269080,0.925089,-0.113638,-0.242676}, {-162.610107,-15.626595,-2.601044}, {0.269080,0.925089,-0.113638,-0.242676}, {-110.065521,-45.919487,-117.121704}, {0.269080,0.925089,-0.113638,-0.242676}')
        preserve_entity(obj_aa_depot_Path, {'pathprops': {'path_data': 'OPEN, {85.947334,45.790657,136.607208}, {0.269080,0.925089,-0.113638,-0.242676}, {-50.846935,23.158363,185.705719}, {0.269080,0.925089,-0.113638,-0.242676}, {-162.610107,-15.626595,-2.601044}, {0.269080,0.925089,-0.113638,-0.242676}, {-110.065521,-45.919487,-117.121704}, {0.269080,0.925089,-0.113638,-0.242676}, ', 'path_type': 'CV_CROrientationSplinePath'}, 'template_id': 0, 'template_name': ''})
        obj_Path_Camera_1 = LookAtCamera(root=self, name='Path_Camera_1', fov=45, farplane=100000.0, look_duration=50)
        preserve_entity(obj_Path_Camera_1, {'cameraprops': {'farplane': 100000.0, 'nearplane': 0.1, 'hvaspect': 1.333333, 'fovh': 45}, 'template_id': 0, 'template_name': ''})
        obj_rh_cruiser_1 = Asset_obj_rh_cruiser_1(root=self, name='rh_cruiser_1', light_group=0, init_point='rh_cruiser_1', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_rh_cruiser_1, {'userprops': {'category': 'Spaceship'}, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'template_id': 0, 'template_name': 'rh_cruiser'})
        preserve_entity(self.get_entity('automarker_Path_Camera_1_focus'), userprops={'main_object': 'main_object'})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Path_Camera_1')
        # source event 1, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['CnB_Camera_01', 'automarker_Marker_2'], flags='POSITION', target_type='ROOT', target_part='', front='NEG_Z_AXIS', up='Y_AXIS', offset=[0, 0, 0], duration=56.200001)
        # source event 2, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_Marker_2', 'automarker_Marker_1'], flags='POSITION+ORIENTATION+ENTITY_RELATIVE', target_type='ROOT', target_part='', front='NEG_Z_AXIS', up='Y_AXIS', offset=[0, 0, 300], duration=54.400002)
        # source event 4, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['aa_depot_Path', 'automarker_Path_Camera_1_focus'], flags='POSITION+ORIENTATION+ENTITY_RELATIVE', target_type='ROOT', target_part='', front='NEG_Z_AXIS', up='Y_AXIS', offset=[0, 0, 0], duration=67.800003)
        # source event 5, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['rh_cruiser_1', 'automarker_Path_Camera_1_focus'], flags='POSITION+ORIENTATION+ENTITY_RELATIVE', target_type='ROOT', target_part='', front='NEG_Z_AXIS', up='Y_AXIS', offset=[0, 0, 0], duration=0)
        # source event 6, 0s
        SourcePathEvent(root=self, group=MAIN, time_delay=t, targets=['Path_Camera_1', 'aa_depot_Path'], pcurve_period=-1000, param_curve={'points': [[0, 0, 0, 0], [1, 1, 0, 0]], 'CLSID': 'FreeFormPCurve'}, flags='POSITION', front='NEG_Z_AXIS', up='Y_AXIS', offset=[0, 0, 0], stop_percent=1, start_percent=0, duration=40)
        t += 0.75
        # source event 7, 0.75s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['CnB_Camera_00', 'automarker_Path_Camera_1_focus'], flags='LOOK_AT', target_type='ROOT', target_part='', front='NEG_Z_AXIS', up='Y_AXIS', offset=[0, 0, 0], duration=0)
        restore_dialogue(self)

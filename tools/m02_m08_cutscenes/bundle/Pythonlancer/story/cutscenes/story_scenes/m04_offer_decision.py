"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm04_offer_decision'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(5555.0)
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Player', 'category': 'Character'}})
        obj_Char_jacobo = Character(root=self, actor=actors.Jacobo, light_group=0, init_point='Char_jacobo', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_jacobo, {'template_name': 'jacobo', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'category': 'Character', 'actor': 'jacobo'}})
        obj_cam_table = LookAtCamera(root=self, name='cam_table', fov=20, farplane=5000, look_duration=300)
        preserve_entity(obj_cam_table, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 20, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_table')
        # source event 2, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRF_IDLE_000LV_XA_06, duration=5555, time_scale=1, start_time=0, loop=True, trans_time=None)
        # source event 3, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_jacobo', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=5555, time_scale=1, start_time=0, loop=True, trans_time=None)
        restore_dialogue(self)

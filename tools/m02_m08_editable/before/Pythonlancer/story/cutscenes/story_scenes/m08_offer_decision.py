"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Actor_obj_Char_kaytlin(actors.Actor):
    NAME = 'kaytlin'
    TYPE = 'male'
    CUTSCENE_APPEARANCE = 'kaytlin'
    GAME_ACTOR = 'Kaytlin'


class ReconstructedScene(Scene):
    DUMP_FILE = 'm08_offer_decision'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(267111111.0)
        obj_Char_kaytlin = Character(root=self, actor=Actor_obj_Char_kaytlin, light_group=0, init_point='Char_kaytlin', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_kaytlin, {'template_name': 'kaytlin', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Kaytlin', 'category': 'Character'}})
        obj_Char_brighton = Character(root=self, actor=actors.Brighton, light_group=0, init_point='Char_brighton', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_brighton, {'template_name': 'brighton', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'actor': 'Brighton', 'category': 'Character'}})
        obj_Char_darcy = Character(root=self, actor=actors.Darcy, light_group=0, init_point='Char_darcy', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_darcy, {'template_name': 'darcy', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Darcy', 'category': 'Character'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True, use_ambient=False, floor_height=0)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC', 'compoundprops': {'floor_height': 0}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_cam_trent_far = LookAtCamera(root=self, name='cam_trent_far', fov=18, farplane=5000, look_duration=710)
        preserve_entity(obj_cam_trent_far, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 18, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        t = 0
        # source event 1, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', anim=Female.Sc_FMBODY_CHRF_IDLE_000LV_XA_05, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 3, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaytlin', anim=Female.Sc_FMBODY_CHRF_IDLE_000LV_XA_05, duration=10, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 7, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_CHRB_IDLE_000LV_XA_05, duration=100, time_scale=0.6, start_time=0, loop=True, trans_time=None)
        # source event 9, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_trent_far')
        t += 0.01
        # source event 2, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_darcy', angle=-25, axis='Y_AXIS', duration=0, smooth=False)
        # source event 4, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_kaytlin', angle=-125, axis='Y_AXIS', duration=0, smooth=False)
        # source event 6, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_brighton', angle=10, axis='Y_AXIS', duration=0, smooth=False)
        # source event 8, 0.01s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', angle=20, axis='Y_AXIS', duration=0, smooth=False)
        restore_dialogue(self)

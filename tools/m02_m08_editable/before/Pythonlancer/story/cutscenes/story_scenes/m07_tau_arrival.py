"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class Asset_obj_ambi_skydome_clouds_snow(Prop):
    COMPOUND_TEMPLATE_NAME = 'exclusion_barrier_m7'
    SRT_GRP = -100
    USR_FLG = 2


class Asset_obj_the_cockpit(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_cockpit'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_chair(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_pilot_chair'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_case(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_case'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_transponder_root(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_transponder_root'
    SRT_GRP = 0
    USR_FLG = 0


class Asset_obj_transponder_crystals(Prop):
    COMPOUND_TEMPLATE_NAME = 'm7_transponder_crystals'
    SRT_GRP = 0
    USR_FLG = 0


class ReconstructedScene(Scene):
    DUMP_FILE = 'm07_tau_arrival'
    SCENE_AMBIENT = [0, 0, 0]

    def action(self):
        main_group = self.get_group(MAIN)
        obj_ambi_LtG11_Puffs_Amb = Light(root=self, name='ambi_LtG11_Puffs_Amb', point_name='ambi_LtG11_Puffs_Amb', extra_name='', light_group=11, diffuse=[0, 0, 0], ambient=[0.5, 0.5, 0.55], direction=[0, 0, 1], light_type='L_DIRECT', on=True, range=2000, cutoff=98.999977, theta=90, color=[255, 255, 255], attenuation=[1, 0, 0])
        preserve_entity(obj_ambi_LtG11_Puffs_Amb, {'lt_grp': 11, 'lightprops': {'on': 'Y', 'cutoff': 98.999977, 'direction': [0, 0, 1], 'range': 2000, 'ambient': [0.5, 0.5, 0.55], 'specular': [0, 0, 0], 'type': 'L_DIRECT', 'diffuse': [0, 0, 0], 'atten': [1, 0, 0], 'color': [255, 255, 255], 'theta': 90}, 'template_name': '', 'usr_flg': 0, 'srt_grp': 0})
        obj_ambi_skydome_clouds_snow = Asset_obj_ambi_skydome_clouds_snow(root=self, name='ambi_skydome_clouds_snow', light_group=23, init_point='ambi_skydome_clouds_snow', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_ambi_skydome_clouds_snow, {'lt_grp': 23, 'flags': 4, 'userprops': {'category': 'Prop', 'NoFog': 'Y'}, 'template_name': 'exclusion_barrier_m7', 'usr_flg': 2, 'srt_grp': -100})
        obj_LIGHT_cockpit_main = Light(root=self, name='LIGHT_cockpit_main', point_name='LIGHT_cockpit_main', extra_name='', light_group=5, diffuse=[0.8, 0.8, 0.8], ambient=[0.3, 0.3, 0.3], direction=[-1, 0, 0], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_cockpit_main, {'template_name': '', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [0.8, 0.8, 0.8], 'specular': [0, 0, 0], 'ambient': [0.3, 0.3, 0.3], 'direction': [-1, 0, 0], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_LIGHT_trent_inner_objs = Light(root=self, name='LIGHT_trent_inner_objs', point_name='LIGHT_trent_inner_objs', extra_name='', light_group=6, diffuse=[1, 1, 1], ambient=[0.2, 0.2, 0.2], direction=[0, -0.3, -1], light_type='L_DIRECT', on=True, range=150555, cutoff=30, theta=26.999985, color=[255, 255, 255], attenuation=[1, 0, 0.003])
        preserve_entity(obj_LIGHT_trent_inner_objs, {'template_name': '', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'lightprops': {'on': 'Y', 'color': [255, 255, 255], 'diffuse': [1, 1, 1], 'specular': [0, 0, 0], 'ambient': [0.2, 0.2, 0.2], 'direction': [0, -0.3, -1], 'range': 150555, 'cutoff': 30, 'type': 'L_DIRECT', 'theta': 26.999985, 'atten': [1, 0, 0.003]}})
        obj_the_cockpit = Asset_obj_the_cockpit(root=self, name='the_cockpit', light_group=5, init_point='the_cockpit', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_the_cockpit, {'template_name': 'm7_cockpit', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_Char_trent = Character(root=self, actor=actors.Trent, light_group=6, init_point='Char_trent', rotate_from_quat=True, use_ambient=True, floor_height=-1)
        preserve_entity(obj_Char_trent, {'template_name': 'trent', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'compoundprops': {'floor_height': -1}, 'userprops': {'Actor': 'Player', 'category': 'Character'}})
        obj_chair = Asset_obj_chair(root=self, name='chair', light_group=6, init_point='chair', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_chair, {'template_name': 'm7_pilot_chair', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_case = Asset_obj_case(root=self, name='case', light_group=5, init_point='case', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_case, {'template_name': 'm7_case', 'lt_grp': 5, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_transponder_root = Asset_obj_transponder_root(root=self, name='transponder_root', light_group=6, init_point='transponder_root', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_transponder_root, {'template_name': 'm7_transponder_root', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_transponder_crystals = Asset_obj_transponder_crystals(root=self, name='transponder_crystals', light_group=6, init_point='transponder_crystals', rotate_from_quat=True, use_ambient=True)
        preserve_entity(obj_transponder_crystals, {'template_name': 'm7_transponder_crystals', 'lt_grp': 6, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'LIT_DYNAMIC+LIT_AMBIENT', 'userprops': {'category': 'Prop'}})
        obj_cam_start = LookAtCamera(root=self, name='cam_start', fov=7, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_start, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 7, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_stand = LookAtCamera(root=self, name='cam_stand', fov=7, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_stand, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 7, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_cam_chair = LookAtCamera(root=self, name='cam_chair', fov=7, farplane=5000, look_duration=70)
        preserve_entity(obj_cam_chair, {'template_name': '', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'flags': 'HIDDEN', 'cameraprops': {'fovh': 7, 'hvaspect': 1.85, 'nearplane': 0.2, 'farplane': 5000}})
        obj_click1 = Sound(root=self, name='click1', sound='sfx_ui_react_accept02', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_click1, {'template_name': 'sfx_ui_react_accept02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_click2 = Sound(root=self, name='click2', sound='sfx_ui_react_data01', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_click2, {'template_name': 'sfx_ui_react_data01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_click3 = Sound(root=self, name='click3', sound='sfx_ui_react_data02', attenuation=-15, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_click3, {'template_name': 'sfx_ui_react_data02', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -15, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_init_systems = Sound(root=self, name='init_systems', sound='sfx_ui_react_request01', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_init_systems, {'template_name': 'sfx_ui_react_request01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_system_error1 = Sound(root=self, name='system_error1', sound='sfx_ui_react_accept01', attenuation=-10, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_system_error1, {'template_name': 'sfx_ui_react_accept01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -10, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_system_error2 = Sound(root=self, name='system_error2', sound='sfx_ui_react_denied01', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_system_error2, {'template_name': 'sfx_ui_react_denied01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_system_success = Sound(root=self, name='system_success', sound='sfx_ui_react_processing01', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_system_success, {'template_name': 'sfx_ui_react_processing01', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        obj_music_main = Sound(root=self, name='music_main', sound='zone_field_ice', attenuation=-5, dmin=50, dmax=300, priority='Story_Sound_1')
        preserve_entity(obj_music_main, {'template_name': 'zone_field_ice', 'lt_grp': 0, 'srt_grp': 0, 'usr_flg': 0, 'audioprops': {'attenuation': -5, 'pan': 0, 'dmin': 50, 'dmax': 300, 'ain': 360, 'aout': 360, 'atout': 0, 'rmix': 0}, 'userprops': {'category': 'Audio', 'Priority': 'Story_Sound_1'}})
        t = 0
        # source event 5, 0s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_spcbody_s010x_trent_xf_prone_000up_13, duration=0.001, time_scale=1, start_time=0, loop=False, trans_time=None)
        # source event 43, 0s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=60, start_time=0, loop=True)
        t += 0.01
        # source event 9, 0.01s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_start')
        t += 0.99
        # source event 10, 1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_start', target_name='automarker_cam_start_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 11, 1s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_start_focus', target_name='automarker_cam_start_marker_pos2', duration=10, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 2
        # source event 6, 3s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_spcbody_s010x_trent_xf_prone_000up_13, duration=25, time_scale=0.7, start_time=0, loop=False, trans_time=None)
        t += 9
        # source event 7, 12s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_spcbody_s010x_trent_xf_prone_000up_13, duration=25, time_scale=1, start_time=7, loop=False, trans_time=None)
        # source event 12, 12s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_stand')
        # source event 13, 12s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='cam_stand', target_name='automarker_cam_stand_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        # source event 14, 12s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_cam_stand_focus', target_name='automarker_cam_stand_marker_pos2', duration=7, smooth=True, adjust_pos=True, adjust_orient=True)
        t += 6
        # source event 8, 18s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_MLBODY_WLKG_000LV_XA_01, duration=2.5, time_scale=1, start_time=0, loop=True, trans_time=1)
        t += 2
        # source event 22, 20s
        AudioAnimEvent(root=self, group=MAIN, time_delay=t, sound_name='music_main', duration=5, attenuation=-15)
        t += 0.5
        # source event 15, 20.5s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='cam_chair')
        # source event 16, 20.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='chair', target_name='automarker_point_chair', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 17, 20.5s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', target_name='automarker_point_trent_chair', duration=0, smooth=False, adjust_pos=True, adjust_orient=True)
        # source event 20, 20.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_SPCBODY_s027x_Trent_XB_CHRF_000DN_03, duration=18, time_scale=0.47, start_time=0.5, loop=False, trans_time=None)
        t += 1.0
        # source event 23, 21.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='init_systems', duration=5, start_time=0, loop=False)
        t += 1.2
        # source event 29, 22.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click1', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 24, 23s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='system_error2', duration=5, start_time=0, loop=False)
        t += 0.4
        # source event 30, 23.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click2', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 31, 24.1s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 32, 24.8s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click1', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 25, 25s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='system_error2', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 33, 25.5s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click2', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 34, 26.2s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click3', duration=5, start_time=0, loop=False)
        t += 0.5
        # source event 35, 26.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click1', duration=5, start_time=0, loop=False)
        main_group.append_time(27)

        # Line 100: source 27s; allocated facial window 12s.
        t = 0
        # source event 26, 27s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='system_error2', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 36, 27.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click2', duration=5, start_time=0, loop=False)
        t += 0.2
        # source event 21, 27.5s
        MotionEvent(root=self, group=MAIN, time_delay=t, object_name='Char_trent', anim=Male.Sc_SPCBODY_s027x_Trent_XB_CHRF_000DN_03, duration=18, time_scale=0.5, start_time=1.5, loop=False, trans_time=1)
        t += 0.4
        # source event 37, 27.9s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click3', duration=5, start_time=0, loop=False)
        t += 0.1
        # source event 27, 28s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='system_error2', duration=5, start_time=0, loop=False)
        t += 0.6
        # source event 38, 28.6s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click1', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 39, 29.3s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click2', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 40, 30s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click3', duration=5, start_time=0, loop=False)
        t += 0.7
        # source event 41, 30.7s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click1', duration=5, start_time=0, loop=False)
        t += 0.3
        # source event 28, 31s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='system_success', duration=5, start_time=0, loop=False)
        t += 0.4
        # source event 42, 31.4s
        StartSoundEvent(root=self, group=MAIN, time_delay=t, sound_name='click2', duration=5, start_time=0, loop=False)
        select_dialogue(self, 7, 'Msn7Omega13', 'm07_omega13')
        self.groups.pop('motion_100', None)
        obj_Char_trent.facial(group=MAIN, index=100, append=True, auto_lip=True, extra_delay=0)
        t = 0
        main_group.append_time(-7.0)
        preserve_spatial(self.get_entity('ambi_skydome_clouds_snow'), source_basis=[[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]], reference_orientation=[1.0, -0.0, -0.0, -0.0])
        restore_dialogue(self)

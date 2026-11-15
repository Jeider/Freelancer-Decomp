from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story import actors


class BerlinScene(Scene):
    DUMP_FILE = 'm01_berlin'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)

        cam_entry = LookAtCamera(root=self, name='cam_entry', fov=35, look_duration=200)
        cam_stand = LookAtCamera(root=self, name='cam_stand', fov=22, look_duration=200)
        cam_adelmar = LookAtCamera(root=self, name='cam_adelmar', fov=20, look_duration=200)
        cam_trent = LookAtCamera(root=self, name='cam_trent', fov=15, look_duration=200)
        cam_luc = LookAtCamera(root=self, name='cam_luc', fov=20, look_duration=200)

        trent = Character(root=self, actor=actors.Trent, light_group=0, init_point='Char_trent', rotate_from_quat=True)
        alaric = Character(root=self, actor=actors.Alaric, light_group=0, init_point='Char_alaric', rotate_from_quat=True)
        luc = Character(root=self, actor=actors.Luc, light_group=0, init_point='Char_luc', rotate_from_quat=True)
        adelmar = Character(root=self, actor=actors.Adelmar, light_group=0, init_point='Char_adelmar', rotate_from_quat=True)

        t = 0
        cam_entry.set(group=MAIN, time_delay=t)
        cam_entry.move_cam(group=MAIN, index=2, duration=4, smooth=True, time_delay=t)
        cam_entry.move_focus(group=MAIN, index=2, duration=4, smooth=True, time_delay=t)
        self._m(adelmar, 'Sc_MLHEAD_HAPPY_SMILE_PLEASD_000LV_XA_%', t, 1, loop=True)
        self._m(adelmar, 'Sc_MLBODY_CHRB_IDLE_MED_000LV_XA_07', t, 25, loop=True)
        self._m(luc, 'Sc_MLBODY_CHRB_TWSTS_LOOK_090LV_XA_02', t, 25)
        self._m(alaric, 'Sc_MLBODY_WLKG_000LV_XA_01', t, 4, start=1.1, loop=True)
        self._m(trent, 'Sc_MLBODY_WLKG_000LV_XA_01', t, 4, start=1.1, loop=True)
        NeckIkEvent(root=self, group=MAIN, char_name='Char_trent', target_name='Char_adelmar', duration=4, time_delay=t, target_type=TARGET_HARDPOINT, target_part='hp_neck')
        NeckIkEvent(root=self, group=MAIN, char_name='Char_alaric', target_name='alaric_stand_ik', duration=15, time_delay=t, target_type=TARGET_ROOT)
        t = 1
        NeckIkEvent(root=self, group=MAIN, char_name='Char_adelmar', target_name='head_alaric', duration=7, time_delay=t, target_type=TARGET_ROOT)
        MoveFastEvent(root=self, group=MAIN, object_name='head_alaric', target_name=self.get_automarker_name('head_alaric2'), time_delay=t)
        t = 2
        NeckIkEvent(root=self, group=MAIN, char_name='Char_luc', target_name='head_alaric', duration=9, time_delay=t, target_type=TARGET_ROOT)
        t = 4
        self._m(luc, 'Sc_MLBODY_CHRB_TWSTS_FROM_090LV_XA_04', t, 25)
        cam_stand.set(group=MAIN, time_delay=t)
        cam_stand.move_cam(group=MAIN, index=2, duration=8, smooth=True, time_delay=t)
        cam_stand.move_focus(group=MAIN, index=2, duration=8, smooth=True, time_delay=t)
        MoveFastEvent(root=self, group=MAIN, object_name='Char_trent', target_name=self.get_automarker_name('trent_pos_table'), time_delay=t)
        MoveFastEvent(root=self, group=MAIN, object_name='Char_alaric', target_name=self.get_automarker_name('alaric_pos_table'), time_delay=t)
        self._m(alaric, 'Sc_MLBODY_STND_IDLE_000LV_xa_04', t, 10)
        self._m(trent, 'Sc_MLBODY_STND_IDLE_000LV_xa_04', t, 10)
        t = 5
        MoveFastEvent(root=self, group=MAIN, object_name='alaric_stand_ik', target_name=self.get_automarker_name('head_luc'), time_delay=t)
        main_group.append_time(5.5)

        t = 0
        t += 0.7
        self._m(alaric, 'Sc_MLBODY_STND_GESTL_LEFT_000LV_XA_02', t, 10)
        t += 0.8
        NeckIkEvent(root=self, group=MAIN, char_name='Char_trent', target_name='trents_stand_ik', duration=5, time_delay=t, target_type=TARGET_ROOT)
        t += 1
        NeckIkEvent(root=self, group=MAIN, char_name='Char_adelmar', target_name='Char_alaric', duration=3, time_delay=t, target_type=TARGET_HARDPOINT, target_part='hp_neck')
        t += 2
        EyeIkEvent(root=self, group=MAIN, char_name='Char_trent', target_name='head_adelmar', duration=5, time_delay=t, target_type=TARGET_ROOT)
        t += 0.5
        MoveFastEvent(root=self, group=MAIN, object_name='trents_stand_ik', target_name=self.get_automarker_name('head_adelmar'), time_delay=t)
        t += 1
        MoveFastEvent(root=self, group=MAIN, object_name='alaric_stand_ik', target_name=self.get_automarker_name('head_adelmar'), time_delay=t)
        started = main_group.get_time()
        alaric.facial(group=MAIN, index=10, auto_lip=True)
        self._hold(started, 6)

        t = 0
        cam_adelmar.set(group=MAIN, time_delay=t)
        EyeIkEvent(root=self, group=MAIN, char_name='Char_adelmar', target_name='adelmar_ik', duration=5, time_delay=t, target_type=TARGET_ROOT)
        t += 1
        MoveFastEvent(root=self, group=MAIN, object_name='adelmar_ik', target_name=self.get_automarker_name('head_trent'), time_delay=t)
        t += 2
        MoveFastEvent(root=self, group=MAIN, object_name='adelmar_ik', target_name=self.get_automarker_name('head_alaric'), time_delay=t)
        started = main_group.get_time()
        adelmar.facial(group=MAIN, index=20, auto_lip=True)
        self._hold(started, 5.5)

        t = 0
        cam_trent.set(group=MAIN, time_delay=t)
        self._m(trent, 'Sc_MLBODY_STND_TILT_HEAD_QUZZCLLY_000LV_XA_03', t, 2, trans=1)
        MoveFastEvent(root=self, group=MAIN, object_name='trent_table_ik', target_name=self.get_automarker_name('head_luc'), time_delay=t)
        EyeIkEvent(root=self, group=MAIN, char_name='Char_trent', target_name='trent_mega_ik', duration=4, time_delay=t, target_type=TARGET_ROOT)
        MoveFastEvent(root=self, group=MAIN, object_name='trent_mega_ik', target_name=self.get_automarker_name('table_top'), time_delay=t)
        t += 1
        MoveFastEvent(root=self, group=MAIN, object_name='trent_mega_ik', target_name=self.get_automarker_name('head_luc'), time_delay=t)
        t += 0.5
        self._m(trent, 'Sc_MLBODY_STND_000LV_E_20', t, 10, trans=1)
        t += 0.5
        NeckIkEvent(root=self, group=MAIN, char_name='Char_luc', target_name='luc_ik', duration=10, time_delay=t, target_type=TARGET_ROOT)
        started = main_group.get_time()
        trent.facial(group=MAIN, index=30, auto_lip=True)
        self._hold(started, 6)

        t = 0
        MoveFastEvent(root=self, group=MAIN, object_name='luc_ik', target_name=self.get_automarker_name('head_adelmar'), time_delay=t)
        cam_luc.set(group=MAIN, time_delay=t)
        self._m(luc, 'Sc_MLBODY_CHRB_SHRG_SHLDRS_BIG_000LV_XA_03', t, 25, trans=0.5)
        t += 2.5
        self._m(luc, 'Sc_MLBODY_CHRB_STNDCR_TRNS_090LV_XA_05', t, 25, trans=0.5)
        started = main_group.get_time()
        luc.facial(group=MAIN, index=40, auto_lip=True)
        self._hold(started, 6)

    def _hold(self, started, window):
        group = self.get_group(MAIN)
        end = started + window
        if group.get_time() < end:
            group.append_time(end - group.get_time())

    def _m(self, char, anim, delay, duration, scale=1, start=0, trans=None, loop=False):
        char.motion(group=MAIN, anim=anim, duration=duration, time_delay=delay,
                    time_scale=scale, start_time=start, trans_time=trans, loop=loop)

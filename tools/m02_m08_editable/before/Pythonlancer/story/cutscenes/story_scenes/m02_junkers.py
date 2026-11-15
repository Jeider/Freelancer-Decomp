"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm02_junkers'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(33.5)
        obj_Camera_1 = LookAtCamera(root=self, name='Camera_1', fov=45, farplane=100000, look_duration=30)
        preserve_entity(obj_Camera_1, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 45, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        obj_Camera_2 = LookAtCamera(root=self, name='Camera_2', fov=45, farplane=100000, look_duration=30)
        preserve_entity(obj_Camera_2, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 45, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_1')
        # source event 4, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Camera_1', target_name='automarker_mark_cam_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 5, 0s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_Camera_1_focus', target_name='automarker_mark_obj_pos2', duration=15, smooth=True, adjust_pos=True, adjust_orient=False)
        t += 16
        # source event 6, 16s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_2')
        # source event 7, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='Camera_2', target_name='automarker_mark_cam2_pos2', duration=11, smooth=True, adjust_pos=True, adjust_orient=False)
        # source event 8, 16s
        MoveEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_Camera_2_focus', target_name='automarker_mark_obj2_pos2', duration=11, smooth=True, adjust_pos=True, adjust_orient=False)
        restore_dialogue(self)

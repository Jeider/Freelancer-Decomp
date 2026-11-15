"""Editable reconstruction; source and event audit in the accompanying report.json."""
from story.cutscenes.scene import Scene
from story.cutscenes.content import *
from story.cutscenes.anim import *
from story.cutscenes.source_extensions import *
from story import actors


class ReconstructedScene(Scene):
    DUMP_FILE = 'm05_arrest_camera07'
    SCENE_AMBIENT = [128, 128, 128]

    def action(self):
        main_group = self.get_group(MAIN)
        self.set_duration(600.0)
        obj_Camera_1 = LookAtCamera(root=self, name='Camera_1', fov=45, farplane=100000, look_duration=60)
        preserve_entity(obj_Camera_1, {'template_name': '', 'template_id': 0, 'cameraprops': {'fovh': 45, 'hvaspect': 1.333333, 'nearplane': 0.1, 'farplane': 100000}})
        t = 0
        # source event 0, 0s
        SetCameraEvent(root=self, group=MAIN, time_delay=t, camera_name='Camera_1')
        # source event 1, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_CoreMarker', 'automarker_Camera_1_focus'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION')
        # source event 2, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['automarker_CameraMarker', 'automarker_CoreMarker'], duration=60, offset=[50, 100, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION+ENTITY_RELATIVE')
        # source event 3, 0s
        SourceAttachEvent(root=self, group=MAIN, time_delay=t, targets=['Camera_1', 'automarker_CameraMarker'], duration=60, offset=[0, 0, 0], up='Y_AXIS', front='NEG_Z_AXIS', target_part='', target_type='ROOT', flags='POSITION+ORIENTATION')
        # source event 5, 0s
        RotateAxisEvent(root=self, group=MAIN, time_delay=t, object_name='automarker_CoreMarker', angle=360, axis='Y_AXIS', duration=60, smooth=False)
        restore_dialogue(self)

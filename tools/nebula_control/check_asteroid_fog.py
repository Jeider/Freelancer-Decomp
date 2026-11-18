"""Audit small depth-writing asteroid coverage with the actual installed nebula shaders."""
import check_object_volume as probe

probe.OUT = probe.ROOT / 'out/graphics_settings/nebula_asteroid_mesh/fog_surface'
probe.PROBE = probe.OUT / 'probe'
probe.BUILD = probe.OUT / 'build'
probe.CASES = 'tools/nebula_control/asteroid_fog_cases.inl'
probe.ALLOW_SHADER_CHANGES = ('nebula_composite.hlsl',)
probe.REPAIR_OBJECT_DEPTH = True
probe.COMPARE_INSTALLED_COMPOSITE = True
probe.EXTRA_SOURCES = ['tools/nebula_control/check_asteroid_fog.py']

if __name__ == '__main__':
    probe.main()
    # Existing surface-contrast and exclusion checks, sharing the built client.
    probe.OUT = probe.OUT / 'surfaces'
    probe.PROBE = probe.OUT / 'probe'
    probe.CASES = 'tools/nebula_control/object_volume_cases.inl'
    probe.COMPARE_INSTALLED_COMPOSITE = False
    probe.main()

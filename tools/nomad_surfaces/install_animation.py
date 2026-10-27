"""Stage/apply only the ET animation HLSL; never builds or copies executable files."""
import install

if __name__ == '__main__':
    install.STAGE = install.REPO / 'src/obj/nomad_surfaces/animation_install'
    install.PAYLOAD = ('DATA_EXTRA/SHADERS/surface_material.hlsl',)
    install.SCOPE = 'ET-only interior organic animation; shader source only; compilation deferred at user request'
    install.main()

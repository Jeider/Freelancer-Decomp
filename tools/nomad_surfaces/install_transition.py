"""Install the Nomad close-up relief continuity fix and verify the game shader cache."""
import install

if __name__ == '__main__':
    install.STAGE = install.REPO / 'src/obj/nomad_transition/install'
    install.PAYLOAD = ('DATA_EXTRA/SHADERS/surface_material.hlsl',)
    install.SCOPE = 'Original Nomad 12-step relief with scale-independent close-up tangent validity'
    install.main()

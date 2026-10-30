"""Stage/apply the lair material and ice finish revision, preserving the client executable."""
import install

if __name__ == '__main__':
    install.STAGE = install.REPO / 'src/obj/nomad_lair_revision/install'
    install.PAYLOAD = ('bin/RP9.dll', 'bin/RP9.pdb', 'bin/Shading.dll', 'bin/Shading.pdb',
        'DATA_EXTRA/SHADERS/surface_material.hlsl') + tuple(
        f'DATA_EXTRA/TEXTURES/lair_bone{i}.dds' for i in range(1,6))
    install.SCOPE = 'Lair: shared asteroid stone, authored bone masks, six organic depth layers by ET with stronger relief and wet gloss; coloured ice reflections'
    install.main()

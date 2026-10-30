"""Install restored original Nomad materials, retaining unrelated renderer changes."""
import install

if __name__ == '__main__':
    install.STAGE = install.REPO / 'src/obj/nomad_original_restore/install'
    install.PAYLOAD = ('bin/Shading.dll', 'bin/Shading.pdb',
                       'DATA_EXTRA/SHADERS/surface_material.hlsl',
                       'DATA_EXTRA/TEXTURES/nomad_layers.dds')
    install.SCOPE = 'Original Nomad 12-step parallax, layered relief and organic atlas; retain current ice and renderer'
    install.main()

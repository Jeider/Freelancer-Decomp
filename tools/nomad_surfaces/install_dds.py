"""Install the verified DXT mip-cursor fix; restore native membrane draw states."""
import install
if __name__=='__main__':
    install.STAGE=install.REPO/'src/obj/nomad_dds/install'
    install.PAYLOAD=('bin/Shading.dll','bin/Shading.pdb')
    install.SCOPE='DXT mip byte sizes derived from block grids, independent of omitted DDS linear size; native membrane states restored'
    install.main()

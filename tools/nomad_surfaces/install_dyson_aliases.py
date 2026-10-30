"""Install ANM vdyson material classification; preserve all assets and INI settings."""
import install

if __name__=='__main__':
    install.STAGE=install.REPO/'src/obj/dyson_bump/aliases_install'
    install.PAYLOAD=('bin/Shading.dll','bin/Shading.pdb')
    install.SCOPE='Recognize ANM vdyson1/2/3 texture aliases as Dyson bump; nomad_land unchanged'
    install.main()

"""Disable custom surface shading for all Dyson texture/material uses and cube fields."""
import install

if __name__=='__main__':
    install.STAGE=install.REPO/'src/obj/dyson_native/install'
    install.PAYLOAD=('bin/RP9.dll','bin/RP9.pdb','bin/Shading.dll','bin/Shading.pdb')
    install.SCOPE='Native Dyson rendering: texture aliases, transparent variants, atlas and direct cube-field profile; BEAST stays native'
    install.main()

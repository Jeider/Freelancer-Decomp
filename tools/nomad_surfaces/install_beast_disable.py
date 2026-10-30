"""Disable BEAST's surface shader for an in-game FPS comparison."""
import install

if __name__=='__main__':
    install.STAGE=install.REPO/'src/obj/beast_relief/disable_install'
    install.PAYLOAD=('bin/Shading.dll','bin/Shading.pdb')
    install.SCOPE='Force BEAST material to Legacy: no custom bump or automatic surface shader; other materials unchanged'
    install.main()

"""Install scoped native membrane depth/alpha/cull fix; keep all current artwork."""
import install
if __name__=='__main__':
    install.STAGE=install.REPO/'src/obj/nomad_web_alpha/install'
    install.PAYLOAD=('bin/Shading.dll','bin/Shading.pdb')
    install.SCOPE='Native membrane alpha cutout only: discard empty texels on both passes; preserve original depth writes and culling'
    install.main()

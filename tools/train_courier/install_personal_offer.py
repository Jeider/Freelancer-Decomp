"""Install checked Content/client for personal campaign offers; preserve Server/Common/DATA."""
import install_local_triggers as installer
installer.__doc__=__doc__
installer.OUT=installer.ROOT/'out/personal_offer'
installer.NAMES=('Content.dll','Content.pdb','freelancer.exe','freelancer.pdb')
if __name__=='__main__':installer.main()

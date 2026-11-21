"""Client-only correction of physical asteroid fog scheduling and range."""
import sys
import install_asteroid_fog as installer

installer.OUT=installer.ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/physical_order'
installer.BUILD=installer.OUT/'build';installer.PLAN=installer.OUT/'install.json'
installer.base.OUT,installer.base.BUILD=installer.OUT,installer.BUILD
installer.SHADERS=[];installer.REPORTS=('checks.json',)
installer.FILES={'bin/'+name:installer.BUILD/'bin'/name for name in ('freelancer.exe','freelancer.pdb')}
installer.SCOPE='Physical Omega-15 asteroid queue and camera fog range; unchanged shaders, nebula and content'

if __name__=='__main__':
    installer.apply() if '--apply' in sys.argv else installer.prepare()

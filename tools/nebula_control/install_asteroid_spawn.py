"""Install verified material-preserving physical asteroid spawning."""
import sys
import install_surface_scatter as transaction

installer=transaction.installer
installer.OUT=installer.ROOT/'out/graphics_settings/nebula_asteroid_mesh/spawn_fade'
installer.BUILD=installer.OUT/'build';installer.PLAN=installer.OUT/'install.json'
installer.base.OUT,installer.base.BUILD=installer.OUT,installer.BUILD
installer.SHADERS=[];installer.REPORTS=('checks.json',)
installer.BINARIES=('RP9.dll','freelancer.exe')
installer.SCOPE='Physical asteroid spawn coverage preserves original materials, fog and depth; no cloud or shader file edits'
installer.FILES={'bin/'+name:installer.BUILD/'bin'/name for name in ('RP9.dll','RP9.pdb','freelancer.exe','freelancer.pdb')}

if __name__=='__main__':
    transaction.apply() if '--apply' in sys.argv else installer.prepare()

"""Install checked asteroid pixel fog, preserving cloud/content configuration."""
import sys
import install_surface_scatter as transaction

installer=transaction.installer
installer.OUT=installer.ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage'
installer.BUILD=installer.OUT/'build';installer.PLAN=installer.OUT/'install.json'
installer.base.OUT,installer.base.BUILD=installer.OUT,installer.BUILD
installer.SHADERS=['far_rocks.hlsl','surface_material.hlsl'];installer.REPORTS=('checks.json',)
installer.BINARIES=('RP9.dll','freelancer.exe')
installer.SCOPE='Omega-15 asteroid fog via a fixed pixel grid retaining texture, combined with birth/range coverage; no nebula/profile changes'
installer.FILES={**{'bin/'+name:installer.BUILD/'bin'/name for name in ('RP9.dll','RP9.pdb','freelancer.exe','freelancer.pdb')},
    **{'DATA_EXTRA/SHADERS/'+name:installer.ROOT/'DATA_EXTRA/SHADERS'/name for name in installer.SHADERS}}

if __name__=='__main__':
    transaction.apply() if '--apply' in sys.argv else installer.prepare()

"""Install prepared Nomad membrane texture banks with hash checks and backup."""
import sys
import install
import prepare_membrane as prepared

if __name__=='__main__':
    if '--restore' not in sys.argv:
        raise SystemExit('Texture repaint was rejected. Use install_energy.py for original artwork plus runtime effects. This archived installer only permits --restore BACKUP.')
    if '--apply' not in sys.argv and '--restore' not in sys.argv:
        prepared.main()
    else:
        install.STAGE=prepared.STAGE
        install.PAYLOAD=tuple('DATA/SOLAR/'+n for n in prepared.LIBRARIES)
        install.SCOPE=prepared.SCOPE
        install.main()

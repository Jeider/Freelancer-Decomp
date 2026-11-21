"""Read Dietrich's installed materials into an isolated offline reference folder."""
import json
import hassler_prepare as native


def main():
    native.OUT = native.OUT / 'native_upper/source/dietrich'
    native.ASSETS = {'dietrich': 'BODIES/rh_deidrich_body.dfm'}
    native.main()


if __name__ == '__main__':
    main()

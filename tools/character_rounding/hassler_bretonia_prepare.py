"""Pin the current Bretonia elite reference for Hassler's trousers and belt."""
import hassler_prepare as native

if __name__=='__main__':
    native.OUT=native.OUT/'native_upper/source/bretonia'
    native.ASSETS={'bretonia':'BODIES/br_male_elite_body.dfm'}
    native.main()

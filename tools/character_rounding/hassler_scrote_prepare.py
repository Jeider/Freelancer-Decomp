"""Pin the user's native Scrote vest reference, without changing game assets."""
import hassler_prepare as native

if __name__=='__main__':
    native.OUT=native.OUT/'native_upper/source/scrote'
    native.ASSETS={'scrote':'BODIES/li_scrote_body.dfm'}
    native.main()

import cfgai as cfg
import spotipy
import spotipy.util as util

user = cfg.SPOTIFY_USER
CACHE = '.spotipyoauthcache'

token = util.prompt_for_user_token(user, scope='playlist-modify-private playlist-modify-public user-read-currently-playing',
        client_id = cfg.SPOTIFY_ID, client_secret = cfg.SPOTIFY_SECRET,
        redirect_uri=cfg.SPOTIFY_REDIRECT, cache_path=CACHE)

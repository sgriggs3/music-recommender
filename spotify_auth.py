from spotipy.oauth2 import SpotifyOAuth
from flask import jsonify, request, session, url_for
from functools import wraps
import os
import logging

logger = logging.getLogger(__name__)

SPOTIPY_CLIENT_ID = os.getenv('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.getenv('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.getenv('SPOTIPY_REDIRECT_URI')

scope = ('user-read-playback-state user-modify-playback-state '
         'user-read-currently-playing playlist-read-private '
         'playlist-read-collaborative playlist-modify-private '
         'playlist-modify-public user-read-recently-played '
         'user-library-read streaming user-top-read user-library-modify user-read-email')

auth_manager = SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                            client_secret=SPOTIPY_CLIENT_SECRET,
                            redirect_uri=SPOTIPY_REDIRECT_URI,
                            scope=scope,
                            show_dialog=True)

def auth():
    """Generate Spotify authorization URL."""
    auth_url = auth_manager.get_authorize_url()
    return jsonify(url=auth_url)

def callback():
    """Handle Spotify callback after authorization."""
    code = request.args.get('code')
    try:
        token_info = auth_manager.get_access_token(code)
        session['token_info'] = token_info
        return jsonify(message="You are now authenticated!", token=token_info)
    except Exception as e:
        logger.error(f"Error during Spotify callback: {str(e)}")
        return jsonify(error="An error occurred during authentication"), 500

def require_spotify_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token_info = session.get('token_info', None)
        if token_info is None:
            return jsonify(error="Spotify authentication required"), 401
        
        if auth_manager.is_token_expired(token_info):
            try:
                token_info = auth_manager.refresh_access_token(token_info['refresh_token'])
                session['token_info'] = token_info
            except Exception as e:
                logger.error(f"Error refreshing Spotify token: {str(e)}")
                return jsonify(error="Failed to refresh Spotify token"), 401
        
        return f(*args, **kwargs)
    return decorated_function

def get_spotify_client():
    token_info = session.get('token_info', None)
    if token_info:
        return spotipy.Spotify(auth=token_info['access_token'])
    return None
# spotify_integration.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import session
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

def get_spotify_client():
    token_info = session.get('token_info', None)
    if token_info:
        return spotipy.Spotify(auth=token_info['access_token'])
    return None

def refresh_token_if_expired():
    token_info = session.get('token_info', None)
    if token_info and auth_manager.is_token_expired(token_info):
        try:
            new_token = auth_manager.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = new_token
            return True
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False
    return True

def get_user_profile():
    spotify = get_spotify_client()
    if spotify:
        return spotify.current_user()
    return None

def get_user_top_tracks(time_range='medium_term', limit=20):
    spotify = get_spotify_client()
    if spotify:
        return spotify.current_user_top_tracks(time_range=time_range, limit=limit)
    return None

def get_user_top_artists(time_range='medium_term', limit=20):
    spotify = get_spotify_client()
    if spotify:
        return spotify.current_user_top_artists(time_range=time_range, limit=limit)
    return None

def get_user_playlists(limit=50):
    spotify = get_spotify_client()
    if spotify:
        return spotify.current_user_playlists(limit=limit)
    return None

def create_playlist(name, description=""):
    spotify = get_spotify_client()
    if spotify:
        user_id = spotify.me()['id']
        return spotify.user_playlist_create(user_id, name, public=False, description=description)
    return None

def add_tracks_to_playlist(playlist_id, track_uris):
    spotify = get_spotify_client()
    if spotify:
        return spotify.playlist_add_items(playlist_id, track_uris)
    return None
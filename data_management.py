import pandas as pd
from sqlalchemy.exc import SQLAlchemyError
from app import db
from models import ListeningHistory, AudioFeatures, User
import logging
import spotipy
from spotipy.oauth2 import SpotifyOAuth

logger = logging.getLogger(__name__)

def load_extended_history(filepath):
    try:
        df = pd.read_csv(filepath, encoding='utf-8')
        df['timestamp'] = pd.to_datetime(df['ts'])

        batch_size = 1000
        total_rows = len(df)

        for start in range(0, total_rows, batch_size):
            end = min(start + batch_size, total_rows)
            batch = df.iloc[start:end]

            history_entries = []
            audio_features_entries = []

            for _, row in batch.iterrows():
                history_entry = ListeningHistory(
                    timestamp=row['timestamp'],
                    username=row['username'],
                    track_id=row['track_id'],
                    track_name=row['track_name'],
                    artist_name=row['artist_name'],
                    album_name=row['album_name'],
                    duration_ms=row['duration_ms'],
                    location=row['location'],
                    skipped=row['skipped']
                )
                history_entries.append(history_entry)

                audio_features = AudioFeatures(
                    track_id=row['track_id'],
                    valence=row['valence'],
                    tempo=row['tempo'],
                    danceability=row['danceability'],
                    energy=row['energy'],
                    instrumentalness=row['instrumentalness'],
                    acousticness=row['acousticness']
                )
                audio_features_entries.append(audio_features)

            try:
                db.session.bulk_save_objects(history_entries)
                db.session.bulk_save_objects(audio_features_entries)
                db.session.commit()
                logger.info(f"Processed {end}/{total_rows} rows")
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Error in batch {start}-{end}: {str(e)}")

        logger.info("Extended history loading completed successfully")
    except Exception as e:
        logger.error(f"Error loading extended history: {str(e)}")

def update_listening_history(spotify_client):
    recent_tracks = spotify_client.current_user_recently_played(limit=50)

    for item in recent_tracks['items']:
        track = item['track']
        timestamp = item['played_at']

        history_entry = ListeningHistory(
            timestamp=timestamp,
            username=spotify_client.me()['id'],
            track_id=track['id'],
            track_name=track['name'],
            artist_name=track['artists'][0]['name'],
            album_name=track['album']['name'],
            duration_ms=track['duration_ms']
        )

        db.session.add(history_entry)

    db.session.commit()
    logger.info("Listening history updated from Spotify API")

def fetch_and_store_audio_features(spotify_client):
    tracks_without_features = db.session.query(ListeningHistory.track_id).outerjoin(
        AudioFeatures, ListeningHistory.track_id == AudioFeatures.track_id
    ).filter(AudioFeatures.track_id == None).distinct().limit(100).all()

    track_ids = [track.track_id for track in tracks_without_features]

    if not track_ids:
        logger.info("No new tracks to fetch audio features for")
        return

    audio_features = spotify_client.audio_features(track_ids)

    for feature in audio_features:
        if feature:
            audio_feature_entry = AudioFeatures(
                track_id=feature['id'],
                valence=feature['valence'],
                tempo=feature['tempo'],
                danceability=feature['danceability'],
                energy=feature['energy'],
                instrumentalness=feature['instrumentalness'],
                acousticness=feature['acousticness']
            )
            db.session.add(audio_feature_entry)

    db.session.commit()
    logger.info(f"Audio features fetched and stored for {len(audio_features)} tracks")

def initialize_spotify_client():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope="user-read-recently-played user-top-read",
        redirect_uri="http://localhost:8888/callback"
    ))

def sync_spotify_data():
    spotify_client = initialize_spotify_client()
    update_listening_history(spotify_client)
    fetch_and_store_audio_features(spotify_client)
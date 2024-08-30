# recommendation_engine.py

import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from app import db
from models import ListeningHistory, AudioFeatures
import logging

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        self.df = None
        self.feature_columns = ['valence', 'tempo', 'danceability', 'energy', 'instrumentalness', 'acousticness']

    def prepare_data(self):
        query = db.session.query(ListeningHistory, AudioFeatures).join(
            AudioFeatures, ListeningHistory.track_id == AudioFeatures.track_id
        )
        df = pd.read_sql(query.statement, db.session.bind)
        
        # Prepare features
        features = df[self.feature_columns]
        scaler = StandardScaler()
        scaled_features = scaler.fit_transform(features)
        
        self.df = pd.DataFrame(scaled_features, columns=self.feature_columns)
        self.df['track_id'] = df['track_id']
        self.df['track_name'] = df['track_name']
        self.df['artist_name'] = df['artist_name']

    def get_recommendations(self, track_id, n=10):
        if self.df is None:
            self.prepare_data()
        
        track_features = self.df[self.df['track_id'] == track_id][self.feature_columns].values
        if len(track_features) == 0:
            logger.warning(f"No features found for track_id: {track_id}")
            return []
        
        similarities = cosine_similarity(track_features, self.df[self.feature_columns])
        similar_indices = similarities[0].argsort()[::-1][1:n+1]  # Exclude the input track
        
        recommendations = self.df.iloc[similar_indices][['track_id', 'track_name', 'artist_name']]
        return recommendations.to_dict('records')

    def get_personalized_recommendations(self, user_id, n=20):
        # Get user's listening history
        user_history = db.session.query(ListeningHistory).filter_by(username=user_id).all()
        
        # Get top N most listened tracks
        track_counts = pd.DataFrame(user_history).groupby('track_id').size().sort_values(ascending=False).head(10)
        
        recommendations = []
        for track_id in track_counts.index:
            recommendations.extend(self.get_recommendations(track_id, n=5))
        
        # Remove duplicates and sort by frequency
        recommendations_df = pd.DataFrame(recommendations)
        recommendations_df = recommendations_df.drop_duplicates(subset='track_id')
        recommendations_df['frequency'] = recommendations_df['track_id'].map(recommendations_df['track_id'].value_counts())
        recommendations_df = recommendations_df.sort_values('frequency', ascending=False).head(n)
        
        return recommendations_df[['track_id', 'track_name', 'artist_name']].to_dict('records')

recommendation_engine = RecommendationEngine()
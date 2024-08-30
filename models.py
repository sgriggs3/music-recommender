from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ListeningHistory(db.Model):
    __tablename__ = 'listening_history'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    username = db.Column(db.String(100), index=True)
    track_id = db.Column(db.String(100), nullable=False)
    track_name = db.Column(db.String(200))
    artist_name = db.Column(db.String(200))
    album_name = db.Column(db.String(200))
    duration_ms = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<ListeningHistory {self.id}: {self.username} - {self.track_name}>'

class RecommendationFeedback(db.Model):
    __tablename__ = 'recommendation_feedback'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False, index=True)
    recommendation_id = db.Column(db.Integer, nullable=False, index=True)
    feedback = db.Column(db.Text)
    interaction_type = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<RecommendationFeedback {self.id}: User {self.user_id} - Recommendation {self.recommendation_id}>'

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.username}>'
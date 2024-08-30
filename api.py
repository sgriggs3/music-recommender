from flask import Blueprint, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import RecommendationFeedback, db
from recommendation_system import get_personalized_recommendations
import logging

api = Blueprint('api', __name__)
limiter = Limiter(key_func=get_remote_address)

logger = logging.getLogger(__name__)

@api.route('/feedback', methods=['POST'])
@limiter.limit("10/minute")
def record_feedback():
    data = request.get_json()

    required_fields = ['user_id', 'recommendation_id']
    for field in required_fields:
        if field not in data:
            return jsonify(error=f"Missing required field: {field}"), 400

    try:
        feedback_entry = RecommendationFeedback(
            user_id=data['user_id'],
            recommendation_id=data['recommendation_id'],
            feedback=data.get('feedback', ''),
            interaction_type=data.get('interaction_type', '')
        )
        db.session.add(feedback_entry)
        db.session.commit()
        return jsonify(message="Feedback recorded"), 201
    except Exception as e:
        logger.error(f"Error recording feedback: {str(e)}")
        db.session.rollback()
        return jsonify(error="An error occurred while recording feedback"), 500

@api.route('/recommendations', methods=['GET'])
@limiter.limit("5/minute")
def get_recommendations():
    username = request.args.get('username')
    if not username:
        return jsonify(error="Username is required"), 400

    try:
        recommendations = get_personalized_recommendations(username)
        return jsonify(recommendations=recommendations), 200
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        return jsonify(error="An error occurred while fetching recommendations"), 500

@api.route('/sync', methods=['POST'])
@limiter.limit("1/hour")
def sync_spotify_data():
    from data_management import sync_spotify_data
    try:
        sync_spotify_data()
        return jsonify(message="Spotify data synced successfully"), 200
    except Exception as e:
        logger.error(f"Error syncing Spotify data: {str(e)}")
        return jsonify(error="An error occurred while syncing Spotify data"), 500

@api.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded"), 429
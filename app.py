import os
from flask import Flask, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from datetime import datetime
import logging

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['CACHE_TYPE'] = 'simple'

db = SQLAlchemy(app)
cache = Cache(app)
bcrypt = Bcrypt(app)
limiter = Limiter(app, key_func=get_remote_address)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from models import ListeningHistory, AudioFeatures, User, RecommendationFeedback
from spotify_auth import auth, callback
from data_management import load_extended_history
from api import api as api_blueprint

app.register_blueprint(api_blueprint, url_prefix='/api')

# Spotify Auth
app.add_url_rule('/auth', 'auth', auth)
app.add_url_rule('/callback', 'callback', callback)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    # Load data outside of application context for better performance
    load_extended_history('extended_spotify_history.csv')
    app.run(debug=False, host="0.0.0.0")
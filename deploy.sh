#!/bin/bash

# Update system packages
sudo apt-get update
sudo apt-get upgrade -y

# Install required system dependencies
sudo apt-get install -y python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools

# Install PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib

# Create a PostgreSQL user and database
sudo -u postgres psql -c "CREATE USER music_recommender WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "CREATE DATABASE music_recommender_db OWNER music_recommender;"

# Clone the repository (replace with your actual repository URL)
git clone https://github.com/yourusername/music-recommender.git
cd music-recommender

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables (replace with your actual values)
echo "export DATABASE_URL='postgresql://music_recommender:your_password@localhost/music_recommender_db'" >> ~/.bashrc
echo "export SECRET_KEY='your_secret_key'" >> ~/.bashrc
echo "export SPOTIPY_CLIENT_ID='your_spotify_client_id'" >> ~/.bashrc
echo "export SPOTIPY_CLIENT_SECRET='your_spotify_client_secret'" >> ~/.bashrc
echo "export SPOTIPY_REDIRECT_URI='http://your_domain:5000/callback'" >> ~/.bashrc
source ~/.bashrc

# Set up Gunicorn systemd service
sudo tee /etc/systemd/system/music-recommender.service > /dev/null <<EOT
[Unit]
Description=Music Recommender Gunicorn service
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=/home/$USER/music-recommender
Environment="PATH=/home/$USER/music-recommender/venv/bin"
ExecStart=/home/$USER/music-recommender/venv/bin/gunicorn --workers 3 --bind unix:music-recommender.sock -m 007 app:app

[Install]
WantedBy=multi-user.target
EOT

# Start and enable the Gunicorn service
sudo systemctl start music-recommender
sudo systemctl enable music-recommender

# Install and configure Nginx
sudo apt-get install -y nginx

# Configure Nginx to proxy requests to Gunicorn
sudo tee /etc/nginx/sites-available/music-recommender > /dev/null <<EOT
server {
    listen 80;
    server_name your_domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/$USER/music-recommender/music-recommender.sock;
    }
}
EOT

# Enable the Nginx configuration
sudo ln -s /etc/nginx/sites-available/music-recommender /etc/nginx/sites-enabled

# Test Nginx configuration and restart
sudo nginx -t
sudo systemctl restart nginx

echo "Deployment complete. Your Music Recommender should now be running on your VPS!"
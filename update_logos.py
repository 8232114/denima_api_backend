#!/usr/bin/env python3

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models.user import Service, db
from src.main import app

def update_service_logos():
    with app.app_context():
        # Update Netflix
        netflix = Service.query.filter_by(name='Netflix Premium').first()
        if netflix:
            netflix.logo_url = '/uploads/netflix_logo.png'
            
        # Update Spotify
        spotify = Service.query.filter_by(name='Spotify Premium').first()
        if spotify:
            spotify.logo_url = '/uploads/spotify_logo.png'
            
        # Update Shahid VIP
        shahid = Service.query.filter_by(name='Shahid VIP').first()
        if shahid:
            shahid.logo_url = '/uploads/shahid_logo.png'
            
        # Update Amazon Prime Video
        prime = Service.query.filter_by(name='Amazon Prime Video').first()
        if prime:
            prime.logo_url = '/uploads/prime_logo.png'
            
        db.session.commit()
        print("Updated service logos successfully!")

if __name__ == '__main__':
    update_service_logos()


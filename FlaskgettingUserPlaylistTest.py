from flask import Flask, redirect, request, session, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Spotify OAuth Configuration
sp_oauth = SpotifyOAuth(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    redirect_uri=os.getenv('REDIRECT_URI', 'http://127.0.0.1:5000/callbacks'),
    scope='streaming app-remote-control user-read-private user-read-email user-read-playback-state user-modify-playback-state user-read-currently-playing user-read-recently-played playlist-read-private playlist-modify-public playlist-modify-private user-top-read'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    # Generate Spotify authorization URL
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callbacks')
def callback():
    # Handle the callback from Spotify
    try:
        # Get the authorization code from the request
        code = request.args.get('code')
        
        # Exchange the code for a token
        token_info = sp_oauth.get_access_token(code)
        
        # Store token information in session
        session['token_info'] = token_info
        
        return redirect('/sdk')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/get_access_code')
def get_access_code():
    token_info = session.get('token_info', None)
    
    if not token_info:
        return redirect('/login')
    
    # Check if token is expired
    if sp_oauth.is_token_expired(token_info):
        return redirect('/refresh_token')
    
    return token_info['access_token']

@app.route('/refresh_token')
def refresh_token():
    token_info = session.get('token_info', None)
    
    if not token_info:
        return redirect('/login')
    
    try:
        # Refresh the token
        new_token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        
        # Update session with new token
        session['token_info'] = new_token_info
        
        return redirect('/currentlyPlaying')
    
    except Exception as e:
        return redirect('/login')

@app.route('/playlists')
def get_playlists():
    # Create Spotify client
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
        # Fetch user's playlists
        playlists = sp.current_user_playlists()
        playlist_names = [playlist['name'] for playlist in playlists['items']]
        
        return jsonify(playlist_names)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/currentlyPlaying')
def currently_playing():
    # Create Spotify client
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
        # Get currently playing track
        current_track = sp.current_user_playing_track()
        
        if not current_track:
            return jsonify({'message': 'No track is currently playing.'})
        
        track_name = current_track['item']['name']
        artist_name = current_track['item']['artists'][0]['name']
        track_url = current_track['item']['external_urls']['spotify']
        playing = current_track['is_playing']
        
        # Store in session for SDK route
        session['track_name'] = track_name
        session['artist_name'] = artist_name
        
        return jsonify({
            'track_name': track_name,
            'artist_name': artist_name,
            'track_url': track_url,
            'playing': playing
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_devices')
def get_devices():
    # Create Spotify client
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
        # Fetch user's devices
        devices = sp.devices()
        
        if not devices['devices']:
            return jsonify({'error': 'No devices found'}), 404
        
        user_devices = [
            {
                'device_name': device['name'],
                'device_id': device['id'],
                'device_active': device['is_active']
            } for device in devices['devices']
        ]
        
        return jsonify(user_devices)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get_current_playing_device')
def get_current_playing_device():
    # Create Spotify client
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
        # Get current playback state
        current_playback = sp.current_playback()
        
        if not current_playback:
            return jsonify({'message': 'No Device is currently playing.'})
        
        device_name = current_playback['device']['name']
        device_id = current_playback['device']['id']
        
        # Store in session for SDK route
        session['device_id'] = device_id
        session['device_name'] = device_name
        
        return jsonify({
            'device_name': device_name,
            'device_id': device_id
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/sdk')
def sdk():
    # Create Spotify client
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    # Fetch required information
    currently_playing()
    get_current_playing_device()
    
    access_token = session.get('token_info', {}).get('access_token')
    current_track_name = session.get('track_name')
    current_artist_name = session.get('artist_name')
    current_device_name = session.get('device_name')
    current_device_id = session.get('device_id')
    
    return render_template('sdk.html', 
                           access_token=access_token,
                           current_track_name=current_track_name,
                           current_artist_name=current_artist_name,
                           current_device_name=current_device_name,
                           current_device_id=current_device_id)

@app.route('/user_profile')
def user_profile():
    # Create Spotify client
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
        # Fetch user profile
        user_profile = sp.me()
        
        return jsonify({
            "product": user_profile.get('product')
        })
    
    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500

def get_spotify_client():
    # Helper function to create Spotify client
    token_info = session.get('token_info', None)
    
    if not token_info:
        return None
    
    # Check if token is expired and refresh if necessary
    if sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
        except Exception:
            return None
    
    # Create and return Spotify client
    return spotipy.Spotify(auth=token_info['access_token'])

if __name__ == '__main__':
    app.run(debug=True)
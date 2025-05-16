from flask import Flask, redirect, request, session, jsonify, render_template
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callbacks')
def callback():
    try:
        code = request.args.get('code')
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        return redirect('/sdk')
    
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/get_access_code')
def get_access_code():
    token_info = session.get('token_info', None)
    
    if not token_info:
        return redirect('/login')

    if sp_oauth.is_token_expired(token_info):
        return redirect('/refresh_token')
    
    return token_info['access_token']

@app.route('/refresh_token')
def refresh_token():
    token_info = session.get('token_info', None)
    
    if not token_info:
        return redirect('/login')
    
    try:
        new_token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session['token_info'] = new_token_info
        return redirect('/currentlyPlaying')
    
    except Exception as e:
        return redirect('/login')

@app.route('/playlists')
def get_playlists():
    sp = get_spotify_client()
    if not sp:
        return redirect('/login')
    
    try:
        playlists = sp.current_user_playlists()
        playlist_names = [playlist['name'] for playlist in playlists['items']]
        
        return jsonify(playlist_names)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/currentlyPlaying')
def currently_playing():
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
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
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
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
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')
    
    try:
        current_playback = sp.current_playback()
        
        if not current_playback:
            return jsonify({'message': 'No Device is currently playing.'})
        
        device_name = current_playback['device']['name']
        device_id = current_playback['device']['id']
        
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
    sp = get_spotify_client()
    
    if not sp:
        return redirect('/login')

    currently_playing()
    get_current_playing_device()
    
    access_token = session.get('token_info', {}).get('access_token')
    current_track_name = session.get('track_name')
    current_artist_name = session.get('artist_name')
    current_device_name = session.get('device_name')
    current_device_id = session.get('device_id')
    
    return render_template('visualiser.html', 
                           access_token=access_token,
                           current_track_name=current_track_name,
                           current_artist_name=current_artist_name,
                           current_device_name=current_device_name,
                           current_device_id=current_device_id)

def get_spotify_client():
    token_info = session.get('token_info', None)
    
    if not token_info:
        return None
    
    if sp_oauth.is_token_expired(token_info):
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
        except Exception:
            return None
    return spotipy.Spotify(auth=token_info['access_token'])

if __name__ == '__main__':
    app.run(debug=True)
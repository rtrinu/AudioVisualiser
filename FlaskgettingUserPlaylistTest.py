from flask import Flask, redirect, request, session, jsonify, render_template
import requests
from dotenv import load_dotenv
import os
import urllib.parse
from datetime import datetime, timedelta

load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")
scope = os.getenv("SCOPE")
secret_key=os.urandom(12)

app = Flask(__name__)
app.secret_key = secret_key

REDIRECT_URI = "http://127.0.0.1:5000/callbacks"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"
AUTH_URL = "https://accounts.spotify.com/authorize"

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/login')
def login():
    #scope = "user-read-private user-read-email"
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': 'true' # Optional: show the login dialog every time, delete later
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callbacks')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    if 'code' in request.args:
        req_body = {
            'code':request.args['code'],
            'grant_type':'authorization_code',
            'redirect_uri':REDIRECT_URI,
            'client_id':client_id,
            'client_secret':client_secret
        }
        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token' ]= token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/sdk')

@app.route('/get_access_code')
def get_access_code():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')
    expires_at = session.get('expires_at')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    return access_token

@app.route('/playlists')
def get_playlists():
    # Create a function that checks if the access token is expired and refreshes it if necessary so that
    # i dont have to repeat the same code in multiple places
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')
    expires_at = session.get('expires_at')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()
    playlist_names = [playlist['name'] for playlist in playlists['items']]

    return jsonify(playlist_names)

@app.route('/currentlyPlaying')
def currently_playing():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')
    
    if datetime.now().timestamp() > session.get('expires_at'):
        return redirect('/refresh_token')

    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(API_BASE_URL + 'me/player/currently-playing', headers=headers)

    if response.status_code == 204:
        return jsonify({'message': 'No track is currently playing.'})

    if response.status_code != 200:
        return jsonify({
            'error': 'Failed to fetch current track info',
            'status_code': response.status_code,
            'response_text': response.text
        }), response.status_code

    try:
        current_track_info = response.json()
    except ValueError:
        return jsonify({'error': 'Invalid JSON response from Spotify'}), 500

    if 'item' in current_track_info:
        track_name = current_track_info['item']['name']
        artist_name = current_track_info['item']['artists'][0]['name']
        track_url = current_track_info['item']['external_urls']['spotify']
        playing = current_track_info['is_playing']
        session['track_name'] = track_name
        session['artist_name'] = artist_name
        return jsonify({
            'track_name': track_name,
            'artist_name': artist_name,
            'track_url': track_url,
            'playing': playing
        })
    else:
        return jsonify({'message': 'No track is currently playing.'})

@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    refresh_token = session['refresh_token']
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type':'refresh_token',
            'refresh_token':refresh_token,
            'client_id':client_id,
            'client_secret':client_secret
        }
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']
        
        return redirect('/currentlyPlaying')
    
@app.route('/get_devices')
def get_devices():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')
    
    if datetime.now().timestamp() > session.get('expires_at'):
        return redirect('/refresh_token')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(API_BASE_URL + 'me/player/devices', headers=headers)
    devices = response.json()
    print(devices)
    if 'devices' in devices:
        device_names = [device['name'] for device in devices['devices']]
        device_id = [device['id'] for device in devices['devices']]
        device_active = [device['is_active'] for device in devices['devices']]
        user_devices = []
        for i in range(len(device_names)):
            device_list = {
                'device_name': device_names[i],
                'device_id': device_id[i],
                'device_active': device_active[i]
            }
            user_devices.append(device_list)
        return jsonify(user_devices)
    else:
        return jsonify({'error': 'No devices found'}), 404
    
@app.route('/get_current_playing_device')
def get_current_playing_device():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')
    
    if datetime.now().timestamp() > session.get('expires_at'):
        return redirect('/refresh_token')
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    response = requests.get(API_BASE_URL + 'me/player', headers=headers)
    if response.status_code == 204:
        return jsonify({'message': 'No Device is currently playing.'})
    current_device = response.json()
    if 'device' in current_device:
        device_name = current_device['device']['name']
        device_id = current_device['device']['id']
        session['device_id'] = device_id
        session['device_name'] = device_name
    else:
        return jsonify({'error': 'No active device found'}), 404
    

@app.route('/sdk')
def sdk():
    currently_playing()
    get_current_playing_device()
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')
    expires_at = session.get('expires_at')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')
    current_track_name = session.get('track_name')
    current_artist_name = session.get('artist_name')
    current_device_name = session.get('device_name')
    current_device_id = session.get('device_id') 
    return render_template('sdk.html', access_token=access_token,current_track_name=current_track_name,
                           current_artist_name=current_artist_name,
                           current_device_name=current_device_name,
                           current_device_id=current_device_id)


    
if __name__ == '__main__':
    app.run(debug=True)
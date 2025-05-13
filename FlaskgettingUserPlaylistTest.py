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

REDIRECT_URI = "http://127.0.0.1:5000/callback"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_BASE_URL = "https://api.spotify.com/v1/"
AUTH_URL = "https://accounts.spotify.com/authorize"

@app.route('/')
def index():
    # Create a login link page in html, css, js
    return render_template('index.html')


@app.route('/login')
def login():
    #scope = "user-read-private user-read-email"
    params = {
        'client_id': client_id,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI
        #'show_dialog': 'true' # Optional: show the login dialog every time, delete later
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
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

        return redirect('/currentlyPlaying')

@app.route('/playlists')
def get_playlists():
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
    current_track_info = response.json()
    print(current_track_info)
    if 'item' in current_track_info:
        track_name = current_track_info['item']['name']
        artist_name = current_track_info['item']['artists'][0]['name']
        track_url = current_track_info['item']['external_urls']['spotify']
        playing = current_track_info['is_playing']
        return jsonify({
            'track_name': track_name,
            'artist_name': artist_name,
            'track_url': track_url,
            'playing': playing
        })
    else:
        print(current_track_info)
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


    
if __name__ == '__main__':
    app.run(debug=True)
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, url_for, session, render_template, request

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Required for session management

# Spotify OAuth Configuration
sp_oauth = SpotifyOAuth(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    redirect_uri=os.getenv('REDIRECT_URI', 'http://localhost:5000/authorize/spotify'),
    scope='streaming app-remote-control user-read-playback-state user-modify-playback-state user-read-currently-playing'
)

@app.route('/login/spotify')
def spotify_login():
    # Generate the Spotify authorization URL
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/authorize/spotify')
def spotify_authorize():
    # Get the authorization code from the request
    code = request.args.get('code')
    
    try:
        # Exchange the code for a token
        token_info = sp_oauth.get_access_token(code)
        
        # Store token in session
        session['spotify_token'] = token_info
        
        # Create a Spotify client
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Fetch user profile (optional)
        user_profile = sp.current_user()
        
        # Render template with access token and user profile
        return render_template('spotify_player.html', 
                               access_token=token_info['access_token'], 
                               user_profile=user_profile)
    
    except Exception as e:
        # Handle any errors during authorization
        print(f"Authorization error: {e}")
        return "Authorization failed", 400

@app.route('/refresh-token')
def refresh_token():
    # Check if we have a token in the session
    token_info = session.get('spotify_token', None)
    
    if token_info:
        # Check if the token is expired
        if sp_oauth.is_token_expired(token_info):
            try:
                # Refresh the token
                new_token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                
                # Update the session with the new token
                session['spotify_token'] = new_token_info
                
                return new_token_info['access_token']
            except Exception as e:
                print(f"Token refresh error: {e}")
                return redirect('/login/spotify')
    
    # If no valid token, redirect to login
    return redirect('/login/spotify')

# Optional: Logout route
@app.route('/logout')
def logout():
    # Clear the Spotify token from the session
    session.pop('spotify_token', None)
    return redirect('/')

# Error handler for authorization failures
@app.errorhandler(spotipy.SpotifyException)
def handle_spotify_error(error):
    print(f"Spotify API Error: {error}")
    return "An error occurred with Spotify authentication", 500

if __name__ == '__main__':
    app.run(debug=True)
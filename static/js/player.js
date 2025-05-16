window.onSpotifyWebPlaybackSDKReady = () => {
    const token = document.getElementById('access-token').getAttribute('data-access-token');
    const connectionStatusElement = document.getElementById('connection-status');
    const trackNameElement = document.getElementById('track-name');
    const artistNameElement = document.getElementById('artist-name');
    const togglePlayButton = document.getElementById('togglePlay');
    const previousTrackButton = document.getElementById('previous');
    const nextTrackButton = document.getElementById('next');
    const deviceNameElement = document.getElementById('device-name');
    const deviceIdElement = document.getElementById('device-id');

  const updateConnectionStatus = (status, isConnected) => {
    if (window.statusTimeoutId) {
      clearTimeout(window.statusTimeoutId)
      connectionStatusElement.classList.remove("fading")
    }

    connectionStatusElement.textContent = status
    connectionStatusElement.className = isConnected ? "connected" : "disconnected"
    console.log(`Spotify Connection Status: ${status}`)

    if (!isConnected && status.includes("Error")) {
      window.statusTimeoutId = setTimeout(() => {
        connectionStatusElement.classList.add("fading")

        setTimeout(() => {
          if (connectionStatusElement.classList.contains("fading")) {
            connectionStatusElement.textContent = "Ready"
          }
        }, 1000)
      }, 3000)
    }
  }

    if (!token || token === '') {
        updateConnectionStatus('Error: No access token', false);
        return;
    }

    const player = new Spotify.Player({
        name: 'Web Playback Player', 
        getOAuthToken: cb => { cb(token); },
        volume: 0.5
    });

    player.addListener('ready', ({ device_id }) => {
        updateConnectionStatus('Connected to Spotify', true);
        
        togglePlayButton.disabled = false;

        deviceIdElement.textContent = device_id;
        deviceNameElement.textContent = 'Web Playback SDK';

        console.log('Spotify Device Connected:', {
            deviceId: device_id,
            deviceName: 'Web Playback SDK'
        });
    });

    player.addListener('not_ready', ({ device_id }) => {
        updateConnectionStatus('Disconnected from Spotify', false);
        togglePlayButton.disabled = true;
    });

    const errorHandlers = {
        'initialization_error': 'Initialization Error',
        'authentication_error': 'Authentication Error',
        'account_error': 'Account Error',
        'playback_error': 'Playback Error'
    };

    Object.entries(errorHandlers).forEach(([errorType, errorMessage]) => {
        player.addListener(errorType, ({ message }) => {
            updateConnectionStatus(`${errorMessage}: ${message}`, false);
            console.error(`Spotify ${errorMessage}:`, message);
        });
    });

    player.addListener('player_state_changed', state => {
        if (state) {
            const track = state.track_window.current_track;
            trackNameElement.textContent = track.name;
            artistNameElement.textContent = track.artists.map(artist => artist.name).join(', ');
            
            togglePlayButton.textContent = state.paused ? 'Play' : 'Pause';
        }
    });

    togglePlayButton.onclick = () => {
        player.togglePlay().then(() => {
            console.log('Playback Toggled');
        }).catch(error => {
            console.error('Toggle Play Error:', error);
            updateConnectionStatus(`Play/Pause Error: ${error.message}`, false);
        });
    };

    previousTrackButton.onclick = () => {
        player.previousTrack().then(() => {
            console.log('Previous Track');
        }).catch(error => {
            console.error('Previous Track Error:', error);
        });
    };

    nextTrackButton.onclick = () => {
        player.nextTrack().then(() => {
            console.log('Next Track');
        }).catch(error => {
            console.error('Next Track Error:', error);
        });
    };

    player.connect().then(success => {
        if (success) {
            console.log('Spotify SDK Connection Initiated');
        } else {
            updateConnectionStatus('Failed to Connect to Spotify', false);
        }
    }).catch(error => {
        updateConnectionStatus(`Connection Error: ${error}`, false);
    });
};
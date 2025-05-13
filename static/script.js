fetch('currentlyPlaying')
    .then(response => response.json())
    .then(data => {
        document.getElementById('track-info').innerText = '${data.track} by ${data.artist}';
        });

setInterval(() => {
    fetch('currentlyPlaying')
        .then(response => response.json())
        .then(data => {
            document.getElementById('track-info').innerText = '${data.track} by ${data.artist}';
        });
}, 5000);
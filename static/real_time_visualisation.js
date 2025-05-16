// Initialize the Spotify Playback SDK
var accessToken = document.getElementById('access-token').getAttribute('data-access-token');
const player = new Spotify.Player({
    name: 'Web Playback SDK',
    getOAuthToken: cb => {
        cb(oauthToken);
    },
});

// Add event listeners for the player
player.addListener('player_state_changed', state => {
    if (state.paused) return;

    // Analyze the audio data using Meyda
    const audioContext = new AudioContext();
    const analyzer = Meyda.createMeydaAnalyzer({
        audioContext,
        source: null, // We'll set this later
        bufferSize: 1024,
        featureExtractors: ['rms', 'spectralCentroid'],
    });

    // Create a source node for Meyda analysis
    const source = audioContext.createBufferSource();
    const buffer = audioContext.createBuffer(2, 44100, 44100);
    source.buffer = buffer;
    source.connect(analyzer.context.destination);
    analyzer.setSource(source);
    source.start();

    // Analyze the audio data in real-time
    const features = analyzer.get('rms', 'spectralCentroid');

    // Visualize the features using D3.js
    const svg = d3.select('svg');
    const rmsScale = d3.scaleLinear().domain([0, 1]).range([0, 100]);
    const centroidScale = d3.scaleLinear().domain([0, 10000]).range([0, 100]);

    svg.selectAll('rect')
        .data([features.rms])
        .enter()
        .append('rect')
        .attr('x', 0)
        .attr('y', 0)
        .attr('width', rmsScale(features.rms))
        .attr('height', 20)
        .attr('fill', 'blue');

    svg.selectAll('circle')
        .data([features.spectralCentroid])
        .enter()
        .append('circle')
        .attr('cx', centroidScale(features.spectralCentroid))
        .attr('cy', 50)
        .attr('r', 10)
        .attr('fill', 'red');

    // Update the visualization in real-time
    setInterval(() => {
        const features = analyzer.get('rms', 'spectralCentroid');
        svg.selectAll('rect')
            .data([features.rms])
            .attr('width', rmsScale(features.rms));

        svg.selectAll('circle')
            .data([features.spectralCentroid])
            .attr('cx', centroidScale(features.spectralCentroid));
    }, 100);
});

// Connect to the Spotify playback device
player.connect();

// Start playing a track
player.play({
    uris: ['spotify:track:TRACK_URI'],
});
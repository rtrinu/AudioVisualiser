document.addEventListener("DOMContentLoaded", () => {
  // Example data in the format provided
  const currentSong = {
    artist: "Brent Faiyaz",
    track: "JACKIE BROWN",
  }

  // Function to update the display with song information
  function updateNowPlaying(songData) {
    const trackElement = document.getElementById("track-name")
    const artistElement = document.getElementById("artist-name")

    // Add fade-out effect
    trackElement.style.opacity = 0
    artistElement.style.opacity = 0

    // Update content after a short delay
    setTimeout(() => {
      trackElement.textContent = songData.track
      artistElement.textContent = songData.artist

      // Add fade-in effect
      trackElement.style.opacity = 1
      artistElement.style.opacity = 1
    }, 500)
  }

  // Initial update with the example data
  updateNowPlaying(currentSong)

  // Function to parse and update with new data
  // This would be called when new song data is received
  window.updateSong = (songJson) => {
    try {
      const songData = typeof songJson === "string" ? JSON.parse(songJson) : songJson
      updateNowPlaying(songData)
    } catch (error) {
      console.error("Error parsing song data:", error)
    }
  }

  // Example of how to update with new data (for demonstration)
  // In a real application, this would be triggered by an external event
  // such as a server push, WebSocket message, or API call

  // Simulating song changes for demonstration
  const demoSongs = [
    { artist: "Brent Faiyaz", track: "JACKIE BROWN" },
    { artist: "SZA", track: "Kill Bill" },
    { artist: "Tyler, The Creator", track: "EARFQUAKE" },
    { artist: "Frank Ocean", track: "Pink + White" },
  ]

  const currentIndex = 0

  // Uncomment this to see song changes every 5 seconds
  /*
    setInterval(() => {
        currentIndex = (currentIndex + 1) % demoSongs.length;
        window.updateSong(demoSongs[currentIndex]);
    }, 5000);
    */
})

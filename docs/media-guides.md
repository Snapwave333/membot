---
layout: default
title: Audio & Video Guides
---

# 🧠 Membot: Audio and Video Guides

This section provides embedded audio and video guides inside the docs so users can quickly learn Membot functions without leaving the repo. Guides feature custom controls (Play/Pause, Restart, Fullscreen) for integrated UX.

## 🚀 Embedded Controls
Custom playback uses inline HTML, CSS, and JavaScript. Styles rely on Flexbox, 100% width for scaling, responsive mobile/desktop layout, and high-contrast buttons.

<style>
.media-container { padding: 15px; margin: 15px auto; border: 1px solid #ccc; border-radius: 6px; background: #f9f9f9; font-family: Arial, sans-serif; max-width: 800px; }
.media-container h3 { margin: 0 0 10px; font-size: 1.3em; color: #333; border-bottom: 1px solid #aaa; padding-bottom: 4px; }
.media-element { width: 100%; margin-bottom: 10px; border-radius: 4px; background: #000; display: block; }
.controls { display: flex; gap: 8px; flex-wrap: wrap; }
.control-btn { background: #007bff; color: #fff; border: none; padding: 8px 12px; border-radius: 5px; cursor: pointer; font-weight: bold; font-size: 0.85em; min-width: 70px; }
.control-btn:hover { filter: brightness(0.9); }
.control-btn.fullscreen { background: #28a745; }
.control-btn.fullscreen:hover { filter: brightness(0.9); }
@media (max-width: 600px) { .media-container { padding: 12px; } }
</style>

<div class="media-container">
  <h3>🎥 Video Guide</h3>
  <p>Walkthrough of Membot UI: creating nodes, linking concepts, querying.</p>
  <video id="membotVideo" class="media-element" src="https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4" preload="auto"></video>
  <div class="controls">
    <button id="videoPlayPauseBtn" class="control-btn" onclick="togglePlayback('membotVideo','videoPlayPauseBtn')" aria-label="Play or pause video">Play</button>
    <button class="control-btn" onclick="restartMedia('membotVideo','videoPlayPauseBtn')" aria-label="Restart video">Restart</button>
    <button class="control-btn fullscreen" onclick="toggleFullscreen('membotVideo')" aria-label="Enter fullscreen">Fullscreen</button>
  </div>
</div>

<div class="media-container">
  <h3>🔊 Audio Guide</h3>
  <p>Step-by-step voice setup instructions.</p>
  <audio id="membotAudio" class="media-element" src="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3" preload="auto"></audio>
  <div class="controls">
    <button id="audioPlayPauseBtn" class="control-btn" onclick="togglePlayback('membotAudio','audioPlayPauseBtn')" aria-label="Play or pause audio">Play</button>
    <button class="control-btn" onclick="restartMedia('membotAudio','audioPlayPauseBtn')" aria-label="Restart audio">Restart</button>
  </div>
</div>

## ⚙️ Custom JS Functions
<script>
function togglePlayback(id, btnId) {
  const m = document.getElementById(id);
  const b = document.getElementById(btnId);
  if (!m || !b) return;
  if (m.paused || m.ended) {
    m.play();
    b.textContent = 'Pause';
  } else {
    m.pause();
    b.textContent = 'Play';
  }
}
function restartMedia(id, btnId) {
  const m = document.getElementById(id);
  const b = document.getElementById(btnId);
  if (!m) return;
  m.currentTime = 0;
  m.play();
  if (b) b.textContent = 'Pause';
}
function toggleFullscreen(id) {
  const v = document.getElementById(id);
  if (!v) return;
  if (v.requestFullscreen) v.requestFullscreen();
  else if (v.mozRequestFullScreen) v.mozRequestFullScreen();
  else if (v.webkitRequestFullscreen) v.webkitRequestFullscreen();
  else if (v.msRequestFullscreen) v.msRequestFullscreen();
}

document.addEventListener('DOMContentLoaded', function() {
  const video = document.getElementById('membotVideo');
  const audio = document.getElementById('membotAudio');
  if (video) {
    video.addEventListener('pause', () => { document.getElementById('videoPlayPauseBtn').textContent = 'Play'; });
    video.addEventListener('play', () => { document.getElementById('videoPlayPauseBtn').textContent = 'Pause'; });
    video.addEventListener('ended', () => { document.getElementById('videoPlayPauseBtn').textContent = 'Restart'; });
  }
  if (audio) {
    audio.addEventListener('pause', () => { document.getElementById('audioPlayPauseBtn').textContent = 'Play'; });
    audio.addEventListener('play', () => { document.getElementById('audioPlayPauseBtn').textContent = 'Pause'; });
    audio.addEventListener('ended', () => { document.getElementById('audioPlayPauseBtn').textContent = 'Restart'; });
  }
});
</script>

## 📝 Usage Notes
1. Replace placeholder src with actual public links. Local paths won't work.
2. Host files on GitHub Pages, S3, or GCS with CORS set.
3. Native controls removed for consistency.
4. `preload="auto"` loads enough for smooth playback.
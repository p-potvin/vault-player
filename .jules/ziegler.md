## 🛡️-05-09 - XSS Vulnerability in video_player.js
**Vulnerability:** Found `btnPlay.innerHTML` being updated dynamically with unicode characters which could lead to an XSS vulnerability. Also `seekPreview.style.backgroundImage` uses string interpolation without encoding.
**Learning:** These paths handle user paths or file content natively without adequate escaping. Even with `%27` encoding in `sanitizePath()`, DOM insertions must be careful not to introduce execution bugs.
**Prevention:** Use `.textContent` for text insertion to automatically escape, and validate CSS parameters thoroughly.

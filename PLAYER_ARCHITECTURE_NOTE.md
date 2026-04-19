# Vault Player Architecture Note

This project is slated to adapt the custom hardware-accelerated video modal and engine from `vault-explorer`.

## Core Mechanics Designed in Explorer

1. **Glass-UI Chrome-less Player:**
   We successfully hid and intercepted standard HTML5 Chromeless controls. The `<video>` wrapper utilizes native DOM intersections completely skinned using CSS `radial-gradients` and transparent bounds.
2. **Seek-Bar Trickplay Injection:**
   Using Node IPC, we extracted the `.trickplay` frame maps entirely locally. Whenever the custom playback scrubber triggers `mousemove`, we map the physical DOM cursor relative offset (`percent = X / width`) and slice into the raw trickplay array mathematically.
   **Crucial Rendering Note:** The CSS inline `backgroundImage: url(...)` will fail natively in Node if the original filename has an apostrophe `'`. The `vault-explorer` successfully implemented an isolated RegExp `.replace(/'/g, "%27")` into its `sanitizePath()` logic to strictly ensure standard file strings inject smoothly into the scrubber!

## Implementation Pipeline

- Rip the `<div id="video-modal">` mapping and CSS from `vault-explorer/index.html`.
- Fork the exact `processFfmpegQueue` for asynchronous hardware nvenc previews.
- Ensure the `<input type="range">` seekbar utilizes the custom `%27` encoding sequence.

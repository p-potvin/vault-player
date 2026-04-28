/**
 * Vault Video Player
 * Extracted from vault-explorer to provide a reusable, hardware-accelerated video player
 * for the VaultWares ecosystem.
 *
 * Supports plain file playback as well as PQC-encrypted (.vault) media files.
 * Encrypted playback is driven by a caller-supplied async `decryptFn` so the
 * decryption back-end (Python/Electron IPC, WASM, etc.) stays fully decoupled.
 */

export class VaultVideoPlayer {
    constructor(modalId, options = {}) {
        this.modalId = modalId;
        this.options = options;
        this.trickFrames = [];
        this.currentPlayingIndex = -1;
        this.ffmpegQueue = [];
        this.isFfmpegRunning = false;

        // Active Blob URL for encrypted playback — revoked when the player closes.
        this._blobUrl = null;

        // Will be populated by bindElements
        this.elements = {};
    }

    // Fix for file:// paths (spaces, special chars, and especially apostrophes)
    // As per PLAYER_ARCHITECTURE_NOTE.md, standard file strings must strictly ensure %27 encoding.
    sanitizePath(p) {
        if (!p) return '';
        const standardized = p.replace(/\\/g, '/');
        const encoded = standardized.split('/').map(segment => encodeURIComponent(segment).replace(/'/g, "%27")).join('/');
        const decodedDrive = encoded.replace(/^([a-zA-Z])%3A\//, '$1:/');
        return 'file:///' + decodedDrive;
    }

    formatDuration(sec) {
        if (!sec) return '0:00';
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    bindElements() {
        const modal = document.getElementById(this.modalId);
        if (!modal) throw new Error(`Modal with id ${this.modalId} not found.`);

        this.elements = {
            modal: modal,
            vp: modal.querySelector('#video-player'),
            seekArea: modal.querySelector('#seek-area'),
            seekFill: modal.querySelector('#seek-fill'),
            seekPreview: modal.querySelector('#seek-hover-preview'),
            btnPlay: modal.querySelector('#btn-playpause'),
            btnPrev: modal.querySelector('#btn-prev'),
            btnNext: modal.querySelector('#btn-next'),
            btnFullscreen: modal.querySelector('#btn-fullscreen'),
            volSlider: modal.querySelector('#volume-slider'),
            timeDisplay: modal.querySelector('#time-display'),
            btnClose: modal.querySelector('#close-modal'),
            decryptOverlay: modal.querySelector('#decrypt-overlay'),
            decryptSpinner: modal.querySelector('#decrypt-spinner'),
            decryptIcon: modal.querySelector('#decrypt-icon'),
            decryptTitle: modal.querySelector('#decrypt-title'),
            decryptSub: modal.querySelector('#decrypt-sub'),
            decryptDismiss: modal.querySelector('#decrypt-dismiss'),
            pqcBadge: modal.querySelector('#pqc-badge'),
        };

        this.setupEventListeners();
    }

    setupEventListeners() {
        const { vp, seekArea, seekFill, seekPreview, btnPlay, volSlider, btnFullscreen, timeDisplay, btnClose, modal, decryptDismiss } = this.elements;

        if (btnClose) {
            btnClose.addEventListener('click', () => this.close());
        }

        if (decryptDismiss) {
            decryptDismiss.addEventListener('click', () => this._hideDecryptOverlay());
        }

        // Initialize volume
        if (volSlider) {
            vp.volume = volSlider.value;
            volSlider.addEventListener('input', (e) => {
                vp.volume = parseFloat(e.target.value);
            });
        }

        if (vp) {
            vp.addEventListener('timeupdate', () => {
                if (!vp.duration) return;
                if (seekFill) {
                    const pct = (vp.currentTime / vp.duration * 100);
                    seekFill.style.width = pct + '%';
                    if (this.elements.seekArea) {
                        this.elements.seekArea.setAttribute('aria-valuenow', Math.round(pct));
                    }
                }
                if (timeDisplay) {
                    timeDisplay.innerText = this.formatDuration(vp.currentTime) + ' / ' + this.formatDuration(vp.duration);
                }
            });

            vp.addEventListener('click', () => this.togglePlayPause());
        }

        if (btnPlay) {
            btnPlay.addEventListener('click', () => this.togglePlayPause());
        }

        if (btnFullscreen) {
            btnFullscreen.addEventListener('click', () => {
                if (!document.fullscreenElement) {
                    vp.parentElement.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
            });
        }

        if (seekArea) {
            seekArea.addEventListener('click', (e) => {
                const rect = seekArea.getBoundingClientRect();
                vp.currentTime = ((e.clientX - rect.left) / rect.width) * vp.duration;
            });

            seekArea.addEventListener('mousemove', async (e) => {
                const rect = seekArea.getBoundingClientRect();
                let percent = (e.clientX - rect.left) / rect.width;
                if (percent < 0) percent = 0;
                if (percent > 1) percent = 1;

                const tpFolder = vp.dataset.trickplay;
                if (tpFolder && seekPreview) {
                    seekPreview.style.display = 'block';
                    seekPreview.style.left = (percent * 100) + '%';

                    if (this.trickFrames.length === 0 && this.options.getTrickplaySprites) {
                        this.trickFrames = await this.options.getTrickplaySprites(tpFolder);
                    }

                    if (this.trickFrames.length > 0) {
                        const idx = Math.floor(percent * this.trickFrames.length);
                        if (this.trickFrames[idx]) {
                            // strictly enforce %27 escaping logic
                            seekPreview.style.backgroundImage = `url('${this.sanitizePath(this.trickFrames[idx])}')`;
                        }
                    }
                }
            });

            seekArea.addEventListener('mouseleave', () => {
                if (seekPreview) seekPreview.style.display = 'none';
            });
        }

        // Global shortcuts (only active when modal is visible)
        document.addEventListener('keydown', (e) => {
            if (modal.style.display === 'flex') {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

                switch(e.key.toLowerCase()) {
                    case 'escape':
                        this.close();
                        break;
                    case ' ':
                        e.preventDefault();
                        this.togglePlayPause();
                        break;
                    case 'arrowleft':
                        e.preventDefault();
                        vp.currentTime = Math.max(0, vp.currentTime - 5);
                        break;
                    case 'arrowright':
                        e.preventDefault();
                        vp.currentTime = Math.min(vp.duration, vp.currentTime + 5);
                        break;
                    case 'arrowup':
                        e.preventDefault();
                        vp.volume = Math.min(1, vp.volume + 0.05);
                        if (volSlider) volSlider.value = vp.volume;
                        break;
                    case 'arrowdown':
                        e.preventDefault();
                        vp.volume = Math.max(0, vp.volume - 0.05);
                        if (volSlider) volSlider.value = vp.volume;
                        break;
                    case 'f':
                        e.preventDefault();
                        if (!document.fullscreenElement) vp.parentElement.requestFullscreen();
                        else document.exitFullscreen();
                        break;
                }
            }
        });
    }

    togglePlayPause() {
        const { vp, btnPlay } = this.elements;
        if (vp.paused) {
            vp.play();
            if (btnPlay) {
                btnPlay.innerHTML = '&#10074;&#10074;';
                btnPlay.setAttribute('aria-label', 'Pause');
            }
        } else {
            vp.pause();
            if (btnPlay) {
                btnPlay.innerHTML = '&#9654;';
                btnPlay.setAttribute('aria-label', 'Play');
            }
        }
    }

    play(videoPath, trickplayFolder = null) {
        const { vp, modal, btnPlay, pqcBadge } = this.elements;
        this._revokeBlobUrl();
        this.trickFrames = [];
        vp.dataset.trickplay = trickplayFolder || '';
        vp.src = this.sanitizePath(videoPath);
        if (btnPlay) {
            btnPlay.innerHTML = '&#10074;&#10074;';
            btnPlay.setAttribute('aria-label', 'Pause');
        }
        if (pqcBadge) pqcBadge.classList.remove('visible');
        modal.style.display = 'flex';
    }

    /**
     * Play a video from an in-memory ArrayBuffer or Uint8Array of already-
     * decrypted bytes.  A Blob URL is created internally and revoked when the
     * player is closed.
     *
     * @param {ArrayBuffer|Uint8Array} buffer  Decrypted media bytes.
     * @param {object} [options]
     * @param {string} [options.mimeType='video/mp4']  MIME type of the media.
     * @param {boolean} [options.encrypted=false]      Show PQC badge when true.
     * @param {string|null} [options.trickplayFolder]  Trickplay sprite folder.
     */
    playFromBytes(buffer, options = {}) {
        const { vp, modal, btnPlay, pqcBadge } = this.elements;
        const mimeType = options.mimeType || 'video/mp4';

        this._revokeBlobUrl();
        this.trickFrames = [];

        const blob = new Blob([buffer], { type: mimeType });
        this._blobUrl = URL.createObjectURL(blob);

        vp.dataset.trickplay = options.trickplayFolder || '';
        vp.src = this._blobUrl;

        if (btnPlay) {
            btnPlay.innerHTML = '&#10074;&#10074;';
            btnPlay.setAttribute('aria-label', 'Pause');
        }

        if (pqcBadge) {
            if (options.encrypted) {
                pqcBadge.classList.add('visible');
            } else {
                pqcBadge.classList.remove('visible');
            }
        }

        modal.style.display = 'flex';
    }

    /**
     * Decrypt a PQC-encrypted media payload and begin playback.
     *
     * The caller provides `decryptFn`, an async function that receives the
     * encrypted ArrayBuffer and returns the decrypted ArrayBuffer.  This
     * keeps the JS player fully decoupled from the underlying crypto
     * back-end (Python/Electron IPC, WASM, etc.).
     *
     * Example (Electron main-process bridge):
     * ```js
     * player.playEncrypted(encryptedBuffer, async (buf) => {
     *     return await ipcRenderer.invoke('pqc-decrypt', buf, keyId);
     * }, { mimeType: 'video/mp4' });
     * ```
     *
     * @param {ArrayBuffer|Uint8Array} encryptedBuffer  Raw encrypted bytes.
     * @param {function(ArrayBuffer): Promise<ArrayBuffer>} decryptFn
     * @param {object} [options]
     * @param {string} [options.mimeType='video/mp4']
     * @param {string|null} [options.trickplayFolder]
     */
    async playEncrypted(encryptedBuffer, decryptFn, options = {}) {
        const { modal } = this.elements;
        modal.style.display = 'flex';
        this._showDecryptOverlay('loading');

        try {
            const decrypted = await decryptFn(encryptedBuffer);
            this._hideDecryptOverlay();
            this.playFromBytes(decrypted, { ...options, encrypted: true });
        } catch (err) {
            this._showDecryptOverlay('error', err.message || 'Decryption failed');
        }
    }

    close() {
        const { vp, modal } = this.elements;
        vp.pause();
        vp.src = "";
        this._revokeBlobUrl();
        this._hideDecryptOverlay();
        modal.style.display = 'none';
    }

    // ------------------------------------------------------------------
    // Decryption overlay helpers
    // ------------------------------------------------------------------

    /**
     * @param {'loading'|'error'} state
     * @param {string} [errorMessage]
     */
    _showDecryptOverlay(state, errorMessage = '') {
        const { decryptOverlay, decryptSpinner, decryptIcon, decryptTitle, decryptSub, decryptDismiss } = this.elements;
        if (!decryptOverlay) return;

        decryptOverlay.classList.add('visible');

        if (state === 'loading') {
            decryptSpinner.style.display = 'block';
            decryptIcon.style.display = 'none';
            decryptTitle.textContent = 'Decrypting Media';
            decryptSub.textContent = 'Applying ML-KEM-768 + ChaCha20-Poly1305…';
            decryptSub.classList.remove('error');
            decryptDismiss.classList.remove('visible');
        } else {
            decryptSpinner.style.display = 'none';
            decryptIcon.style.display = 'flex';
            decryptTitle.textContent = 'Decryption Failed';
            decryptSub.textContent = errorMessage || 'Could not decrypt the media file.';
            decryptSub.classList.add('error');
            decryptDismiss.classList.add('visible');
        }
    }

    _hideDecryptOverlay() {
        const { decryptOverlay } = this.elements;
        if (decryptOverlay) decryptOverlay.classList.remove('visible');
    }

    // ------------------------------------------------------------------
    // Blob URL lifecycle
    // ------------------------------------------------------------------

    _revokeBlobUrl() {
        if (this._blobUrl) {
            URL.revokeObjectURL(this._blobUrl);
            this._blobUrl = null;
        }
    }

    // Node-side preview generation port from main.js
    // Intended to be used within a Node/Electron context
    static processFfmpegQueue(queue, exec, fs) {
        if (queue.isFfmpegRunning || queue.tasks.length === 0) return;
        queue.isFfmpegRunning = true;
        const task = queue.tasks.shift();

        const runPreviewFfmpeg = (task) => {
            if (fs.existsSync(task.outPath) || fs.existsSync(task.altWebmPath)) {
                queue.isFfmpegRunning = false;
                task.resolve({ success: true, path: task.outPath });
                this.processFfmpegQueue(queue, exec, fs);
                return;
            }

            exec(task.cmdCuda, { windowsHide: true }, (err) => {
                if (err) {
                    exec(task.cmdCpu, { windowsHide: true }, (err2) => {
                        queue.isFfmpegRunning = false;
                        if (err2) task.resolve({ success: false, error: err2.message });
                        else task.resolve({ success: true, path: task.outPath });
                        this.processFfmpegQueue(queue, exec, fs);
                    });
                } else {
                    queue.isFfmpegRunning = false;
                    task.resolve({ success: true, path: task.outPath });
                    this.processFfmpegQueue(queue, exec, fs);
                }
            });
        };

        if (task.needsThumb) {
            const thumbCmd = `ffmpeg -y -ss 00:00:15 -i "${task.itemPath}" -vframes 1 -q:v 2 "${task.thumbPath}"`;
            exec(thumbCmd, { windowsHide: true }, () => {
                 runPreviewFfmpeg(task);
            });
        } else {
             runPreviewFfmpeg(task);
        }
    }
}
    constructor(modalId, options = {}) {
        this.modalId = modalId;
        this.options = options;
        this.trickFrames = [];
        this.currentPlayingIndex = -1;
        this.ffmpegQueue = [];
        this.isFfmpegRunning = false;

        // Will be populated by bindElements
        this.elements = {};
    }

    // Fix for file:// paths (spaces, special chars, and especially apostrophes)
    // As per PLAYER_ARCHITECTURE_NOTE.md, standard file strings must strictly ensure %27 encoding.
    sanitizePath(p) {
        if (!p) return '';
        const standardized = p.replace(/\\/g, '/');
        const encoded = standardized.split('/').map(segment => encodeURIComponent(segment).replace(/'/g, "%27")).join('/');
        const decodedDrive = encoded.replace(/^([a-zA-Z])%3A\//, '$1:/');
        return 'file:///' + decodedDrive;
    }

    formatDuration(sec) {
        if (!sec) return '0:00';
        const m = Math.floor(sec / 60);
        const s = Math.floor(sec % 60);
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    }

    bindElements() {
        const modal = document.getElementById(this.modalId);
        if (!modal) throw new Error(`Modal with id ${this.modalId} not found.`);

        this.elements = {
            modal: modal,
            vp: modal.querySelector('#video-player'),
            seekArea: modal.querySelector('#seek-area'),
            seekFill: modal.querySelector('#seek-fill'),
            seekPreview: modal.querySelector('#seek-hover-preview'),
            btnPlay: modal.querySelector('#btn-playpause'),
            btnPrev: modal.querySelector('#btn-prev'),
            btnNext: modal.querySelector('#btn-next'),
            btnFullscreen: modal.querySelector('#btn-fullscreen'),
            volSlider: modal.querySelector('#volume-slider'),
            timeDisplay: modal.querySelector('#time-display'),
            btnClose: modal.querySelector('#close-modal')
        };

        this.setupEventListeners();
    }

    setupEventListeners() {
        const { vp, seekArea, seekFill, seekPreview, btnPlay, volSlider, btnFullscreen, timeDisplay, btnClose, modal } = this.elements;

        if (btnClose) {
            btnClose.addEventListener('click', () => this.close());
        }

        // Initialize volume
        if (volSlider) {
            vp.volume = volSlider.value;
            volSlider.addEventListener('input', (e) => {
                vp.volume = parseFloat(e.target.value);
            });
        }

        if (vp) {
            vp.addEventListener('timeupdate', () => {
                if (!vp.duration) return;
                if (seekFill) {
                    seekFill.style.width = (vp.currentTime / vp.duration * 100) + '%';
                }
                if (timeDisplay) {
                    timeDisplay.innerText = this.formatDuration(vp.currentTime) + ' / ' + this.formatDuration(vp.duration);
                }
            });

            vp.addEventListener('click', () => this.togglePlayPause());
        }

        if (btnPlay) {
            btnPlay.addEventListener('click', () => this.togglePlayPause());
        }

        if (btnFullscreen) {
            btnFullscreen.addEventListener('click', () => {
                if (!document.fullscreenElement) {
                    vp.parentElement.requestFullscreen();
                } else {
                    document.exitFullscreen();
                }
            });
        }

        if (seekArea) {
            seekArea.addEventListener('click', (e) => {
                const rect = seekArea.getBoundingClientRect();
                vp.currentTime = ((e.clientX - rect.left) / rect.width) * vp.duration;
            });

            seekArea.addEventListener('mousemove', async (e) => {
                const rect = seekArea.getBoundingClientRect();
                let percent = (e.clientX - rect.left) / rect.width;
                if (percent < 0) percent = 0;
                if (percent > 1) percent = 1;

                const tpFolder = vp.dataset.trickplay;
                if (tpFolder && seekPreview) {
                    seekPreview.style.display = 'block';
                    seekPreview.style.left = (percent * 100) + '%';

                    if (this.trickFrames.length === 0 && this.options.getTrickplaySprites) {
                        this.trickFrames = await this.options.getTrickplaySprites(tpFolder);
                    }

                    if (this.trickFrames.length > 0) {
                        const idx = Math.floor(percent * this.trickFrames.length);
                        if (this.trickFrames[idx]) {
                            // strictly enforce %27 escaping logic
                            seekPreview.style.backgroundImage = `url('${this.sanitizePath(this.trickFrames[idx])}')`;
                        }
                    }
                }
            });

            seekArea.addEventListener('mouseleave', () => {
                if (seekPreview) seekPreview.style.display = 'none';
            });
        }

        // Global shortcuts (only active when modal is visible)
        document.addEventListener('keydown', (e) => {
            if (modal.style.display === 'flex') {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

                switch(e.key.toLowerCase()) {
                    case 'escape':
                        this.close();
                        break;
                    case ' ':
                        e.preventDefault();
                        this.togglePlayPause();
                        break;
                    case 'arrowleft':
                        e.preventDefault();
                        vp.currentTime = Math.max(0, vp.currentTime - 5);
                        break;
                    case 'arrowright':
                        e.preventDefault();
                        vp.currentTime = Math.min(vp.duration, vp.currentTime + 5);
                        break;
                    case 'arrowup':
                        e.preventDefault();
                        vp.volume = Math.min(1, vp.volume + 0.05);
                        if (volSlider) volSlider.value = vp.volume;
                        break;
                    case 'arrowdown':
                        e.preventDefault();
                        vp.volume = Math.max(0, vp.volume - 0.05);
                        if (volSlider) volSlider.value = vp.volume;
                        break;
                    case 'f':
                        e.preventDefault();
                        if (!document.fullscreenElement) vp.parentElement.requestFullscreen();
                        else document.exitFullscreen();
                        break;
                }
            }
        });
    }

    togglePlayPause() {
        const { vp, btnPlay } = this.elements;
        if (vp.paused) {
            vp.play();
            if (btnPlay) btnPlay.innerHTML = '&#10074;&#10074;';
        } else {
            vp.pause();
            if (btnPlay) btnPlay.innerHTML = '&#9654;';
        }
    }

    play(videoPath, trickplayFolder = null) {
        const { vp, modal, btnPlay } = this.elements;
        this.trickFrames = [];
        vp.dataset.trickplay = trickplayFolder || '';
        vp.src = this.sanitizePath(videoPath);
        if (btnPlay) btnPlay.innerHTML = '&#10074;&#10074;';
        modal.style.display = 'flex';
    }

    close() {
        const { vp, modal } = this.elements;
        vp.pause();
        vp.src = "";
        modal.style.display = 'none';
    }

    // Node-side preview generation port from main.js
    // Intended to be used within a Node/Electron context
    static processFfmpegQueue(queue, exec, fs) {
        if (queue.isFfmpegRunning || queue.tasks.length === 0) return;
        queue.isFfmpegRunning = true;
        const task = queue.tasks.shift();

        const runPreviewFfmpeg = (task) => {
            if (fs.existsSync(task.outPath) || fs.existsSync(task.altWebmPath)) {
                queue.isFfmpegRunning = false;
                task.resolve({ success: true, path: task.outPath });
                this.processFfmpegQueue(queue, exec, fs);
                return;
            }

            exec(task.cmdCuda, { windowsHide: true }, (err) => {
                if (err) {
                    exec(task.cmdCpu, { windowsHide: true }, (err2) => {
                        queue.isFfmpegRunning = false;
                        if (err2) task.resolve({ success: false, error: err2.message });
                        else task.resolve({ success: true, path: task.outPath });
                        this.processFfmpegQueue(queue, exec, fs);
                    });
                } else {
                    queue.isFfmpegRunning = false;
                    task.resolve({ success: true, path: task.outPath });
                    this.processFfmpegQueue(queue, exec, fs);
                }
            });
        };

        if (task.needsThumb) {
            const thumbCmd = `ffmpeg -y -ss 00:00:15 -i "${task.itemPath}" -vframes 1 -q:v 2 "${task.thumbPath}"`;
            exec(thumbCmd, { windowsHide: true }, () => {
                 runPreviewFfmpeg(task);
            });
        } else {
             runPreviewFfmpeg(task);
        }
    }
}

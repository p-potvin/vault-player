# VaultPlayer — TODO

## Branding (Phase 1)

- [x] Read vault-themes Brand Guide and AGENTS.md
- [x] Add vault-themes to VAULT_DEPENDENCIES.txt
- [x] Write branded README.md with mission, color system, typography, and architecture
- [x] Populate ROADMAP.md with phased roadmap
- [x] Add local theme_manager.py from vault-themes
- [x] Apply VaultWares theme tokens to agent console output

## Core Player Extraction (Phase 1.5)

- [x] Extract ideo-modal Chrome-less UI from ault-explorer
- [x] Port VaultVideoPlayer JavaScript class and processFfmpegQueue
- [x] Preserve local path encoding (%27) for trickplay previews

## Container Format (Phase 2)

- [x] Draft container format specification (custom manifest, standard fallback)
- [x] Prototype container writer
- [x] Prototype container reader
- [x] Add standard format export for external clients (MP4, MKV, WebM)

## PQC Protocol (Phase 3)

- [x] Research lattice-based and code-based PQC candidates
- [x] Draft VaultWares PQC protocol specification
- [x] Implement key exchange (ML-KEM-768 via oqs)
- [x] Implement stream cipher for media payloads (ChaCha20-Poly1305)
- [x] Implement digital signatures (ML-DSA-65 via oqs)
- [x] Implement signed-envelope seal/open API
- [x] SecurityAgent integrated into multi-agent coordination system
- [x] Integrate PQC decryption pipeline into the video player component

## In-Process Plugins (Phase 4) - SKIPPED

- [-] Refactor agent task execution to run in-process for real-time playback
- [-] Keep Redis dispatch for non-real-time workflows
- [-] Integrate with vault-flows for heavy workflows

## Platform (Phase 5)

- [x] Web layer (priority 1) in javascript and support for most features except those deemed impossible/too heavy for browser use.
- [ ] Windows desktop player (priority 2)
- [ ] iOS mobile player (priority 3)
- [ ] Android mobile player (priority 4)
- [ ] macOS port from iOS (priority 5)
- [ ] Linux desktop player (priority 6)

## Extensive Redesign and Branding (Phase 6)

- [ ] Add the small logo somewhere and link it with the dark/light theme switch
- [ ] Follow vault-themes guidelines
- [ ] Smooth out the UX/UI with animations and minimalist icons
- [ ] Add keyboard control and other accessibility features

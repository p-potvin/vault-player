# VaultPlayer Roadmap

## Phase 1 — Branding & Identity

- [x] Integrate VaultWares Brand Guide from vault-themes
- [x] Add vault-themes as a project dependency
- [x] Document color system, typography, and theme tokens in README
- [x] Add local theme manager for theme integration
- [ ] Apply VaultWares branding to all agent output and logs

## Phase 2 — Custom Container Format

- [ ] Design custom VaultWares media container format with internal manifest
- [ ] Implement container reader/writer in the player process
- [ ] Maintain standard format export (MP4, MKV, WebM) for external clients
- [ ] Document container specification

## Phase 3 — Post-Quantum Cryptography (PQC) Protocol

- [ ] Research and design a custom PQC protocol for media encryption
- [ ] Implement PQC key exchange and stream cipher for the container format
- [ ] Integrate PQC into the player decryption pipeline
- [ ] Document protocol specification and threat model

## Phase 4 — In-Process Plugin Architecture

- [ ] Move agent task execution to in-process plugins (no external Redis for real-time playback)
- [ ] Implement Redis-backed workflow dispatch for non-real-time video processing
- [ ] Delegate non-real-time workflows to vault-flows
- [ ] Benchmark latency for in-process vs. Redis-dispatched tasks

## Phase 5 — Platform Rollout

- [ ] **Windows** — Primary desktop player (WPF/WinUI with VaultWares.Brand.xaml)
- [ ] **iOS** — Mobile player
- [ ] **Android** — Mobile player
- [ ] **macOS** — Port from iOS implementation if feasible
- [ ] **Linux** — Desktop player (last priority)
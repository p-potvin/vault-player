# VaultPlayer — TODO

## Branding (Phase 1)

- [x] Read vault-themes Brand Guide and AGENTS.md
- [x] Add vault-themes to VAULT_DEPENDENCIES.txt
- [x] Write branded README.md with mission, color system, typography, and architecture
- [x] Populate ROADMAP.md with phased roadmap
- [x] Add local theme_manager.py from vault-themes
- [ ] Apply VaultWares theme tokens to agent console output

## Container Format (Phase 2)

- [ ] Draft container format specification (custom manifest, standard fallback)
- [ ] Prototype container writer
- [ ] Prototype container reader
- [ ] Add standard format export for external clients (MP4, MKV, WebM)

## PQC Protocol (Phase 3)

- [x] Research lattice-based and code-based PQC candidates
- [x] Draft VaultWares PQC protocol specification
- [x] Implement key exchange (ML-KEM-768 via oqs)
- [x] Implement stream cipher for media payloads (ChaCha20-Poly1305)
- [x] Implement digital signatures (ML-DSA-65 via oqs)
- [x] Implement signed-envelope seal/open API
- [x] SecurityAgent integrated into multi-agent coordination system
- [ ] Integrate PQC decryption pipeline into the video player component

## In-Process Plugins (Phase 4)

- [ ] Refactor agent task execution to run in-process for real-time playback
- [ ] Keep Redis dispatch for non-real-time workflows
- [ ] Integrate with vault-flows for heavy workflows

## Platform (Phase 5)

- [ ] Windows desktop player (priority 1)
- [ ] iOS mobile player (priority 2)
- [ ] Android mobile player (priority 3)
- [ ] macOS port from iOS (priority 4)
- [ ] Linux desktop player (priority 5)
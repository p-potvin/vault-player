# VaultPlayer

**Privacy first. Security in service.**

VaultPlayer is a privacy-first media player built by [VaultWares](https://github.com/p-potvin). It is designed for secure, local-first video playback with multi-agent AI coordination for text, image, video, and workflow processing.

## Mission

Create privacy-first technology that is secure by default, understandable by design, and accessible to everyone — in English and French.

### Core Values

1. **Privacy** — Data minimization. Local-first. No tracking.
2. **Security** — In service of people, never theatrics.
3. **Functionality** — For everyone. Clear, fast, bilingual.

## Architecture

VaultPlayer uses a Redis-based multi-agent coordination system. All agents inherit from `ExtrovertAgent` and are overseen by `LonelyManager`.

| Agent | Type | Skills |
|---|---|---|
| **TextAgent** | `text` | Text generation, captioning, prompt engineering, VQA |
| **ImageAgent** | `image` | Image generation, editing, masking, inpainting, outpainting |
| **VideoAgent** | `video` | Video trimming, frame sampling, effects, analysis, captioning |
| **WorkflowAgent** | `workflow` | Workflow parsing, ComfyUI/Diffusion export, validation |

See [agent_manifest.md](agent_manifest.md) for full agent documentation.

## Branding

VaultPlayer follows the VaultWares Brand Guide defined in [vault-themes](https://github.com/p-potvin/vault-themes).

### Color System (Solarized-inspired)

| Token | Dark | Light |
|---|---|---|
| Base / Background | `#002B36` | `#FDF6E3` |
| Slate | `#4A5459` | — |
| Cyan | `#21B8CC` | `#21B8CC` |
| Green | `#4ECC21` | — |
| Gold Accent | `#CC9B21` | — |
| Burgundy | — | `#A63D40` |
| Text | `#F8FAFC` | `#002B36` |
| Muted | — | `#586E75` |

### Typography

```
font-family: "Segoe UI Semilight", "Segoe UI", Inter, system-ui, -apple-system, "Helvetica Neue", Arial, sans-serif;
```

- Weight: 300–500
- Tracking: -0.01em headings
- Languages: EN • FR

### Theme Integration

VaultPlayer includes a local theme manager (`Brand/theme_manager.py`) synced from vault-themes. All UI surfaces must use named theme tokens — never hardcode ad-hoc colors.

- Theme mode must be explicit: `light` or `dark`.
- Every theme must define at least `background` and `accent` role colors.
- WCAG AA compliance: body text ≥ 4.5:1 contrast, large text ≥ 3.0:1.
- Theme names are Title Case; IDs are kebab-case.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Initialize submodules
git submodule update --init

# 3. Start Redis
redis-server vaultwares-agentciation/redis.conf

# 4. Run the full system
python run_coordinated_system.py

# Or run agents individually:
python run_lonely_manager.py &
python run_worker_agent.py --type text --id text-agent-1 &
python run_worker_agent.py --type video --id video-agent-1 &
```

## Dependencies

- **vaultwares-agentciation** — Multi-agent coordination framework (git submodule)
- **vault-themes** — Branding, themes, and visual guidelines

See [VAULT_DEPENDENCIES.txt](VAULT_DEPENDENCIES.txt) for the full submodule manifest.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the project roadmap.

## License

See [LICENSE](LICENSE) for license information.
<img src="https://raw.githubusercontent.com/p-potvin/vaultwares-docs/main/logo/vaultwares-logo.svg">

# vault-player

**Fully Encrypted AI-Powered Video Player**  
**Part of the VaultWares Ecosystem** • <a href="https://docs.vaultwares.com">docs.vaultwares.com</a> • <a href="https://vaultwares.com">vaultwares.com</a>

**Privacy-first media player with real-time AI audio/video filters, effects, and multi-agent coordination. All processing stays local and encrypted.**

## Overview
VaultPlayer delivers secure, local-first video playback with dynamic AI enhancements (filters, subtitles, translation, object detection, style transfer, etc.) powered by realtime-stt, vaultwares-pipelines, and the VaultWares agent team.

## Features
- End-to-end encryption for media and filters
- Real-time AI effects using local models
- Multi-agent coordination (Text, Image, Video, Workflow agents)
- Seamless integration with vault-flows GUI and pipelines
- Bilingual (EN/FR) interface
- Redis-based agent orchestration (upgraded to Google ADK where applicable)
- Theme support via vault-themes submodule

## Quick Start

```bash
git clone https://github.com/p-potvin/vault-player.git
cd vault-player
git submodule update --init --recursive
pip install -r requirements.txt

# Start Redis (required for agents)
redis-server

# Run full coordinated system
python run_coordinated_system.py
```
Architecture &amp; Agent Integration
Fully synchronized with the VaultWares Agent Knowledge Dissemination System:
→ https://raw.githubusercontent.com/p-potvin/vaultwares-docs/main/agents/knowledge-dissemination.mdx
Uses the Google ADK-powered team from vaultwares-agentciation via the invoke_vaultwares_team skill for complex real-time processing.
See PLAYER_ARCHITECTURE_NOTE.md, agent_manifest.md, and agent folders for full details.
Privacy &amp; Security

All data and processing local-first
Full encryption layer
No telemetry or external calls by default
Detailed threat model in central VaultWares docs

Contributing
See CONTRIBUTING.md and the central Brand Guidelines.
License
GPL-3.0 (see LICENSE)
Your data. Your rules. VaultWares.
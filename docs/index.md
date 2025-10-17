---
layout: default
title: NeoMeme Markets Documentation
---

# NeoMeme Markets Documentation

![Logo](../assets/sprites/logo_main.png)

Welcome to the NeoMeme Markets documentation site. This site contains the comprehensive User Manual, setup guidance, and reference materials.
## Beginner Quick Start (First Trade Today)
- Download the Windows installer: https://github.com/Snapwave333/membot/releases/latest/download/NeoMemeMarkets-Setup.exe
- Launch the app and set up your wallet (generate/restore passphrase, connect, fund a small amount)
- Safety net is ON by default: compliance checks run automatically
- Switch Market Mode to Live
- Open Discovery and choose a trending token with real volume
- Set the smallest position size and place a tiny buy
- Use Kill Switch or Emergency Stop anytime if uncertain
- After your first trade, switch back to Simulation (Paper Mode) to practice

For a friendly step-by-step, see the Idiot’s Guide: https://github.com/Snapwave333/membot/blob/main/IDIOTS_GUIDE.md

- Read the full [User Manual](./user-manual.html)
- Idiot's Guide (Day One Profit Strategy): https://github.com/Snapwave333/membot/blob/main/IDIOTS_GUIDE.md
- View the project on GitHub: https://github.com/Snapwave333/membot
- Quick start:
  ```bash
  git clone https://github.com/Snapwave333/membot.git
  cd membot
  python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  cp .env.example .env
  python main.py --paper-mode
  ```

## Sections
- [User Manual](./user-manual.html)
- [Troubleshooting Index](./troubleshooting.html)
- [Diagrams](./diagrams.html)
- [CHANGELOG](https://github.com/Snapwave333/membot/blob/main/CHANGELOG.md)
- [README](https://github.com/Snapwave333/membot/blob/main/README.md)
- [Idiot's Guide](https://github.com/Snapwave333/membot/blob/main/IDIOTS_GUIDE.md)

## Architecture Diagram
![System Architecture](./assets/architecture.svg)


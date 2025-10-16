# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-10-16
- Added Electron Forge desktop wrapper with Squirrel Windows installer
- Integrated Solana wallet UI (connect existing, generate new, deposit, withdraw)
- Removed PayPal integration in favor of Solana-only wallet flow
- Implemented Memecoin Scam Detection tab (market/social/tokenomics heuristics)
- Added Axiom.trade Discovery tab (trending, overview, search via MCP server)
- Integrated Digital Wallet Manager (init, execute trades, reinvest/withdraw, history)
- Added Market Mode toggle (Simulation vs Live) and live data fetcher
- Applied “NeoMeme Markets” theme, sprite system, and animations
- Introduced accordion-style collapsible sections and scroll areas to reduce crowding

## [0.9.0] - 2025-10-10
- Stabilized paper mode demo; resolved PySide6 environment issues
- Added sprite generator utility and sprite pack loader
- Introduced basic live market fetcher with fallbacks

## [0.8.0] - 2025-10-01
- Initial GUI scaffolding, rules/ML engines, Solana/EVM wallet managers
- Paper mode trading flow and tests

[1.0.0]: https://github.com/Snapwave333/membot/releases/tag/v1.0.0

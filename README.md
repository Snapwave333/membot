# Autonomous Hardened Meme-Coin Trading Bot

<p align="center">
  <img src="https://capsule-render.vercel.app/api?text=NeoMeme%20Markets&animation=fadeIn&type=waving&color=0:00F5D4,100:00B3F0&height=140&fontColor=001018&fontAlignY=35" alt="NeoMeme Markets Banner" />
</p>

<p align="center">
  <a href="https://github.com/Snapwave333/membot/actions"><img src="https://img.shields.io/badge/CI-Tests-blue?style=for-the-badge" alt="CI" /></a>
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20Mac-0A84FF?style=for-the-badge" alt="Platforms" />
  <img src="https://img.shields.io/badge/GUI-PySide6-6E40C9?style=for-the-badge" alt="GUI" />
  <img src="https://img.shields.io/badge/Desktop-Electron%20Forge-14F195?style=for-the-badge&labelColor=0b1220" alt="Electron Forge" />
</p>

<p align="center">
  <a href="#quick-start-paper-mode">Quick Start</a> •
  <a href="#desktop-app-windows-via-electron-forge">Desktop App</a> •
  <a href="#recent-changes">Recent Changes</a> •
  <a href="#security-features">Security</a>
</p>

A secure, autonomous trading bot for meme-coins with fail-closed security defaults, comprehensive safety controls, Kraken compliance layer, Solana integration, and Telegram signal processing. Features a layered brain system combining rules-based logic with machine learning.

## Features

### 🔒 Security & Safety
- **Fail-Closed Security**: Refuses to trade when in doubt
- **Encrypted Hot Wallets**: Secure key management with Argon2 KDF and AES-GCM for EVM and Solana
- **Paper Mode**: Fully functional isolated testing environment
- **Safety Controls**: Kill-switch, profit sweep, position limits

### 🏛️ Kraken Compliance Layer
- **Token Safety Assessment**: Bytecode analysis, owner privilege detection
- **Liquidity Analysis**: LP token lock verification, router compatibility
- **Holder Distribution**: Top holder concentration analysis
- **Social Verification**: Multi-source corroboration
- **External Tool Integration**: DexScreener, Birdeye validation
- **Hard Veto System**: Automatic blocking of unsafe tokens

### ⚡ Solana Integration
- **SPL Token Support**: Native Solana token trading
- **DEX Integration**: Serum, Orca, Raydium, Jupiter aggregator
- **Compute Budget Optimization**: Transaction priority and fee management
- **Multi-Chain Support**: Simultaneous EVM and Solana operations

### 📱 Telegram Signal Processing
- **Real-Time Signal Ingestion**: Telegram Bot API integration
- **Astroturf Detection**: Bot account identification, fake engagement detection
- **Multi-Source Corroboration**: Signal validation across platforms
- **Rate Limiting**: Throttling and spam protection

### 🧠 Intelligent Trading
- **Layered Brain**: Rules engine + ML components for decision making
- **Kraken Weighting**: ML confidence adjustment based on compliance
- **Real-Time Analysis**: Market data, sentiment, risk assessment
- **Adaptive Strategies**: Dynamic position sizing and risk management

### 🖥️ User Interface & Infrastructure
- **Native GUI**: Secure PySide6 interface with multi-chain support
- **Comprehensive Logging**: Full audit trail with database persistence
- **Unit Tests**: Complete test coverage with pytest
- **PAPER_MODE Demo**: Comprehensive demonstration script

## Quick Start (Paper Mode)

1. Clone and setup:
```bash
git clone <repo>
cd meme-bot
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your configuration (no real keys needed for paper mode)
```

3. Run PAPER_MODE demonstration:
```bash
# Windows
runpaperdemo.bat

# Linux/Mac
./runpaperdemo.sh

# Or run directly
python run_paper_demo.py
```

4. Run in paper mode:
```bash
python main.py --paper-mode
```

## Desktop App (Windows via Electron Forge)

Build and run a Windows desktop wrapper that launches the Python GUI.

- Install Node.js deps:
```bash
cd electron
npm install
```
- Dev run (spawns Python GUI using venv):
```bash
npm start
```
- Build Windows installer (Squirrel):
```bash
npm run make
# Output: electron/out/make/squirrel.windows/x64/NeoMemeMarkets-Setup.exe
```
Notes:
- The launcher executes `../venv/Scripts/python.exe src/gui/main_window.py` with `PYTHONPATH` set to the repo root.
- Ensure the Python venv and dependencies are installed before running the installer; alternatively, bundle with PyInstaller and ship the EXE via Forge `extraResources`.

## Security Features

- All secrets loaded from `.env` file
- Encrypted private key storage with secure passphrase
- Fail-closed defaults (refuses to trade when uncertain)
- Paper mode isolation from real trading
- Comprehensive audit logging
- Kill-switch and emergency controls

## Recent Changes
- Solana wallet-only flow (remove PayPal)
- Scam Detection tab with heuristics
- Axiom.trade Discovery integration
- Digital Wallet tab: init, reinvest, withdraw, trade history
- Market Mode toggle (Simulation/Live)
- NeoMeme Markets theme, sprites, animations
- Accordion-style collapsible sections and scroll areas
- Electron Forge Windows installer

## Project Structure

```
meme-bot/
├── src/
│   ├── config.py              # Configuration parameters
│   ├── security/
│   │   └── wallet_manager.py  # Encrypted wallet management
│   ├── data/
│   │   └── rpc_connector.py   # RPC connection handling
│   ├── trading/
│   │   ├── exchange.py        # Exchange interface
│   │   ├── strategy.py        # Trading strategies
│   │   └── risk_manager.py    # Risk management
│   ├── brain/
│   │   ├── rules_engine.py    # Rules-based logic
│   │   └── ml_engine.py       # Machine learning components
│   ├── gui/
│   │   └── main_window.py     # PySide6 GUI
│   └── utils/
│       ├── logger.py          # Logging utilities
│       └── database.py        # Database operations
├── tests/                     # Unit tests
├── docs/                      # Documentation
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── pyproject.toml           # Project configuration
├── Dockerfile               # Container configuration
└── main.py                  # Application entry point
```

## Environment Variables

See `.env.example` for required configuration variables:

### RPC Endpoints
- `ETHRPCPRIMARY`, `ETHRPCFALLBACK`: Ethereum RPC endpoints
- `SOLANARPCPRIMARY`, `SOLANARPCFALLBACK`: Solana RPC endpoints
- `WSMEMPOOLPRIMARY`: WebSocket mempool connection

### Security & Trading
- `COLDSTORAGEADDRESS`: Cold storage wallet address
- `NOTIFIERTOKEN`: Notification service token
- `TELEGRAMBOTTOKEN`: Telegram bot token for signal ingestion

### External Services
- `MODELSTOREURL`: ML model storage URL
- `INDEXERURL`: Blockchain indexer URL
- `BACKUPSTORAGEURL`: Backup storage URL
- `GUIAPISOCKET`: GUI API socket path

### Feature Flags
- `SOLANAMODE`: Enable Solana trading (true/false)
- `TELEGRAMMODE`: Enable Telegram signal processing (true/false)
- `PAPERMODE`: Run in paper mode (true/false)

## Development

Run tests:
```bash
pytest tests/
```

Build Docker image:
```bash
docker build -t meme-bot .
```

## Security Considerations

- Never commit `.env` files or private keys
- Use paper mode for testing
- Review all security decisions in code comments
- Follow deployment checklist in `DEPLOYMENT.md`
- Enable kill-switch before live trading

## License

MIT License - see LICENSE file for details.

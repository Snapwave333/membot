# An Idiot's Guide to NeoMeme Markets: Day One Profit Strategy

A friendly, fast track to getting your first safe, automated live trade done today. Keep it simple. Start small. Never risk more than you can afford to lose.

## Quick-Start Table of Contents

- Welcome: Your Fast Track to Trading
- Step 1: Get the App (5 Minutes)
- Step 2: Fund Your Wallet
- Step 3: Check Your Safety Net (Kraken Compliance)
- Step 4: Your First Trade (Start Small!)
- Step 5: Safety First

---

## Welcome: Your Fast Track to Trading
Your goal today: install the app, fund a wallet with a small amount, switch to Live Market Mode, and execute one tiny trade safely. The bot is built with fail‑closed defaults and a hard safety net, so it refuses risky tokens and lets you bail out instantly.

## Step 1: Get the App (5 Minutes)

- Download the Windows installer (Electron Forge desktop wrapper):
  - Latest release: https://github.com/Snapwave333/membot/releases/latest
  - Direct installer link: https://github.com/Snapwave333/membot/releases/latest/download/NeoMemeMarkets-Setup.exe
- Run the installer, then open the app.
- If the app asks for a Python environment, follow the simple prompt or see “Getting Started” in README for the quick venv setup. Most users just click the installer and go.

## Step 2: Fund Your Wallet

In the GUI, open the Solana Wallet tab.

- Action: Click "Generate New Wallet" to create an encrypted key file, or "Connect Existing" to use a wallet you already have.
- Crucial Security: Set a strong passphrase for the encrypted key file. Write it down and store it safely. Never share it.
- Action: Deposit a small amount of SOL or USDC to the wallet address shown in the app. Start tiny.

## Step 3: Check Your Safety Net (The Kraken Compliance Layer)

The Kraken Compliance Layer runs automatically in the background. Think of it as a hard veto system:

- It blocks known scam tokens and suspicious contracts.
- It reduces risk by gating position sizes on unverified assets.
- You don’t need to manually audit bytecode—this layer does the heavy lifting for you.

This means you can focus on simple, safe actions while the bot filters out the worst tokens.

## Step 4: Your First Trade (Start Small!)

- Toggle Market Mode to Live:
  - In the main window, switch from Simulation (Paper Mode) to Live Market Mode.
- Go to the Axiom.trade Discovery tab:
  - Pick a token that’s trending with real volume. Avoid illiquid, brand‑new listings.
- Set Position Size to the minimum:
  - Keep it tiny. The goal is a safe first trade, not a big win. Never risk more than you can afford to lose.
- Action: Execute the trade.
  - Watch the Real‑Time Monitoring panel for P&L, compliance status, and position updates. Let the safety layers do their job.

## Step 5: Safety First

Know your emergency exit before you trade:

- Emergency Controls are in the main window.
  - "Activate Kill Switch": Immediately halt new trading and apply safety rules.
  - "Emergency Stop": Close positions and stop the bot.
- After your first successful live trade, switch back to Simulation (Paper Mode) to test new ideas safely.

---

You did it. One safe, small live trade today. Come back tomorrow with the same discipline: start tiny, let the compliance layer protect you, and use the emergency controls if anything feels off.

Resources if you want to read more (optional):
- README.md (install + desktop app): https://github.com/Snapwave333/membot/blob/main/README.md
- Solana Integration (wallet + funding basics): https://github.com/Snapwave333/membot/blob/main/SOLANAINTEGRATION.md
- Kraken Compliance (safety net overview): https://github.com/Snapwave333/membot/blob/main/KRAKENCOMPLIANCE.md
- Project Summary (features + safety): https://github.com/Snapwave333/membot/blob/main/PROJECT_SUMMARY.md

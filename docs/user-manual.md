---
layout: default
title: User Manual
---

# NeoMeme Markets — Comprehensive User Manual and Tutorial

![NeoMeme Markets Banner](../assets/branding/neomeme-banner.png)

<details>
<summary><strong>Quick Navigation — Collapsible Table of Contents</strong></summary>

- [Chapter 1: Project Overview](#chapter-1-project-overview)
  - [1.1 Purpose and Vision](#11-purpose-and-vision)
  - [1.2 Key Features](#12-key-features)
    - [1.2.1 Security & Safety](#121-security--safety)
    - [1.2.2 Intelligent Trading](#122-intelligent-trading)
    - [1.2.3 User Interface](#123-user-interface)
    - [1.2.4 Data & Persistence](#124-data--persistence)
  - [1.3 Recent Changes](#13-recent-changes)

- [Chapter 2: Initial Setup and Installation](#chapter-2-initial-setup-and-installation)
  - [2.1 Prerequisites](#21-prerequisites)
  - [2.2 Create a Virtual Environment](#22-create-a-virtual-environment)
  - [2.3 Install Dependencies](#23-install-dependencies)
  - [2.4 Configure Environment Variables](#24-configure-environment-variables)
  - [2.5 Run the Paper Mode Demo](#25-run-the-paper-mode-demo)
  - [2.6 Windows Desktop Wrapper (Electron Forge)](#26-windows-desktop-wrapper-electron-forge)
  - [2.7 Troubleshooting](#27-troubleshooting)
    - [2.7.1 Python Version Guidance](#271-python-version-guidance)
    - [2.7.2 Electron Launcher ENOENT](#272-electron-launcher-enoent)
    - [2.7.3 Dependency Pins](#273-dependency-pins)
    - [2.7.4 OneDrive Build Issues](#274-onedrive-build-issues)

- [Chapter 3: Deployment and Configuration](#chapter-3-deployment-and-configuration)
  - [3.1 Pre‑Deployment Checklist](#31-pre-deployment-checklist)
  - [3.2 Security Configuration](#32-security-configuration)
  - [3.3 Network Configuration](#33-network-configuration)
  - [3.4 Database Setup](#34-database-setup)
  - [3.5 Monitoring & Alerting](#35-monitoring--alerting)
  - [3.6 Deployment Steps](#36-deployment-steps)
  - [3.7 Docker Deployment](#37-docker-deployment)
  - [3.8 Emergency Procedures](#38-emergency-procedures)
  - [3.9 Risk Management](#39-risk-management)
  - [3.10 Security Best Practices](#310-security-best-practices)
  - [3.11 Compliance and Legal](#311-compliance-and-legal)

- [Chapter 4: Core Functionality Walkthrough](#chapter-4-core-functionality-walkthrough)
  - [4.1 Wallet Management (Solana)](#41-wallet-management-solana)
    - [4.1.1 Encrypted Keypair Generation and Storage](#411-encrypted-keypair-generation-and-storage)
    - [4.1.2 Decryption and Validation](#412-decryption-and-validation)
    - [4.1.3 Deposit and Withdraw](#413-deposit-and-withdraw)
  - [4.2 Market Modes](#42-market-modes)
    - [4.2.1 Simulation (Paper Mode)](#421-simulation-paper-mode)
    - [4.2.2 Live Mode](#422-live-mode)
  - [4.3 Kraken Compliance Layer](#43-kraken-compliance-layer)
    - [4.3.1 Principles](#431-principles)
    - [4.3.2 EVM Contract Checks](#432-evm-contract-checks)
    - [4.3.3 Solana Contract Checks](#433-solana-contract-checks)
    - [4.3.4 Social Verification](#434-social-verification)
    - [4.3.5 Compliance Scoring and Hard Veto](#435-compliance-scoring-and-hard-veto)

- [Chapter 5: Advanced Topics and Performance](#chapter-5-advanced-topics-and-performance)
  - [5.1 Security Features](#51-security-features)
    - [5.1.1 Fail‑Closed Defaults](#511-fail-closed-defaults)
    - [5.1.2 Audit Trails](#512-audit-trails)
    - [5.1.3 Kill‑Switch](#513-kill-switch)
  - [5.2 Solana Optimizations](#52-solana-optimizations)
    - [5.2.1 Compute Budget](#521-compute-budget)
    - [5.2.2 Priority Fees](#522-priority-fees)
    - [5.2.3 Blockhash and Transaction Handling](#523-blockhash-and-transaction-handling)
  - [5.3 Monitoring and Performance Metrics](#53-monitoring-and-performance-metrics)

- [Chapter 6: Architecture Overview](#chapter-6-architecture-overview)
  - [6.1 Project Structure](#61-project-structure)
  - [6.2 Tech Stack](#62-tech-stack)
  - [6.3 Environment Variables](#63-environment-variables)

- [Chapter 7: Testing](#chapter-7-testing)
  - [7.1 Unit Tests](#71-unit-tests)
  - [7.2 Integration Tests](#72-integration-tests)
  - [7.3 Paper Mode Testing](#73-paper-mode-testing)

- [Chapter 8: Contributing and Roadmap](#chapter-8-contributing-and-roadmap)
  - [8.1 Contribution Guidelines](#81-contribution-guidelines)
  - [8.2 Roadmap](#82-roadmap)

- [Appendix A: Detailed Index](#appendix-a-detailed-index)

</details>

<!-- The remainder mirrors the content of USER_MANUAL.md to render within GitHub Pages site. For brevity here, see the root USER_MANUAL.md for the full text. -->

{% comment %}
If desired, we can auto-sync this file with USER_MANUAL.md via CI in future.
{% endcomment %}

> See the full manual at the repository root: https://github.com/Snapwave333/membot/blob/main/USER_MANUAL.md


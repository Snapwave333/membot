# Deployment Guide - Meme-Coin Trading Bot

This document provides a comprehensive deployment checklist and security guidelines for the meme-coin trading bot.

## Pre-Deployment Checklist

### 1. Environment Setup
- [ ] Python 3.11+ installed
- [ ] Virtual environment created and activated
- [ ] All dependencies installed from `requirements.txt`
- [ ] `.env` file configured with all required variables
- [ ] No secrets committed to version control

### 2. Security Configuration
- [ ] Strong passphrase set for wallet encryption (12+ characters)
- [ ] Encrypted key file created with secure permissions (0o600)
- [ ] Kill-switch file path configured and accessible
- [ ] Cold storage address verified and tested
- [ ] Notification tokens configured and tested

### 3. Network Configuration
- [ ] Primary RPC endpoint tested and responsive
- [ ] Secondary RPC endpoint configured for failover
- [ ] WebSocket connections tested
- [ ] Rate limits configured appropriately
- [ ] Firewall rules configured (if applicable)

### 4. Database Setup
- [ ] Database server running and accessible
- [ ] Database schema created
- [ ] Connection string tested
- [ ] Backup strategy implemented
- [ ] Log retention policies configured

### 5. Monitoring and Alerting
- [ ] Logging configured and tested
- [ ] Security event logging enabled
- [ ] Performance monitoring configured
- [ ] Alert notifications tested
- [ ] Health check endpoints configured

## Security Checklist

### Critical Security Measures
- [ ] **Fail-closed defaults**: Bot refuses to trade when uncertain
- [ ] **Paper mode testing**: Thoroughly tested in paper mode
- [ ] **Kill-switch enabled**: Emergency stop mechanism active
- [ ] **Position limits**: Maximum position sizes configured
- [ ] **Daily loss limits**: Maximum daily loss percentage set
- [ ] **Profit sweep**: Automatic profit withdrawal configured

### Access Control
- [ ] **File permissions**: Encrypted key file has 0o600 permissions
- [ ] **User permissions**: Bot runs with minimal required privileges
- [ ] **Network access**: Only necessary ports exposed
- [ ] **API keys**: Stored securely in environment variables
- [ ] **Passphrase**: Never logged or stored in plaintext

### Audit and Compliance
- [ ] **Audit logging**: All actions logged with timestamps
- [ ] **Security events**: Security-related events logged separately
- [ ] **Trade history**: Complete trade history maintained
- [ ] **Error tracking**: All errors logged and monitored
- [ ] **Compliance**: Regulatory requirements met (if applicable)

## Deployment Steps

### 1. Initial Setup
```bash
# Clone repository
git clone <repository-url>
cd meme-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp env.example .env
```

### 2. Configuration
```bash
# Edit environment variables
nano .env

# Validate configuration
python main.py --validate
```

### 3. Wallet Setup
```bash
# Setup encrypted wallet (first run only)
python main.py --setup

# Test wallet functionality
python main.py --paper-mode
```

### 4. Testing
```bash
# Run unit tests
pytest tests/

# Run integration tests
pytest tests/ -m integration

# Test in paper mode
python main.py --paper-mode
```

### 5. Production Deployment
```bash
# Enable live trading (DANGEROUS!)
python main.py --live
```

## Docker Deployment

### 1. Build Image
```bash
docker build -t meme-bot .
```

### 2. Run Container
```bash
# Paper mode
docker run -d --name meme-bot-paper \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/.encrypted_key:/app/.encrypted_key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  meme-bot

# Live mode (DANGEROUS!)
docker run -d --name meme-bot-live \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/.encrypted_key:/app/.encrypted_key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  meme-bot --live
```

## Monitoring and Maintenance

### 1. Health Checks
- [ ] Bot responds to health check endpoints
- [ ] RPC connections are healthy
- [ ] Database connections are stable
- [ ] Memory usage is within limits
- [ ] CPU usage is reasonable

### 2. Log Monitoring
- [ ] Security events monitored
- [ ] Trading events logged
- [ ] Error rates tracked
- [ ] Performance metrics collected
- [ ] Audit trail maintained

### 3. Regular Maintenance
- [ ] Log files rotated regularly
- [ ] Database backups performed
- [ ] Security updates applied
- [ ] Performance optimized
- [ ] Configuration reviewed

## Emergency Procedures

### 1. Kill Switch Activation
```bash
# Create kill switch file
touch /tmp/meme_bot_kill_switch

# Bot will stop trading within 10 seconds
```

### 2. Emergency Stop
```bash
# Stop the bot process
pkill -f "python main.py"

# Or if running in Docker
docker stop meme-bot-live
```

### 3. Recovery Procedures
```bash
# Check logs for errors
tail -f logs/memebot.log

# Check security events
tail -f logs/security.log

# Check trading events
tail -f logs/trading.log
```

## Risk Management

### 1. Position Limits
- **Maximum position size**: $5,000 USD
- **Maximum concurrent positions**: 5
- **Per-trade percentage**: 2% of portfolio
- **Daily loss limit**: 5% of portfolio

### 2. Profit Management
- **Profit target**: 15% per position
- **Profit sweep threshold**: $1,000 USD
- **Automatic withdrawal**: Enabled
- **Cold storage**: Configured

### 3. Safety Controls
- **Kill-switch**: Active
- **Emergency stop loss**: 20%
- **Maximum drawdown**: 15%
- **Position timeout**: 24 hours

## Troubleshooting

### Common Issues

#### 1. RPC Connection Failures
```bash
# Check RPC endpoint status
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  https://mainnet.infura.io/v3/YOUR_PROJECT_ID

# Check failover endpoints
python main.py --validate
```

#### 2. Wallet Decryption Failures
```bash
# Verify encrypted key file exists
ls -la .encrypted_key

# Check file permissions
stat .encrypted_key

# Recreate encrypted key if necessary
python main.py --setup
```

#### 3. Database Connection Issues
```bash
# Test database connection
python -c "from src.utils.database import test_connection; test_connection()"

# Check database logs
tail -f logs/database.log
```

### Performance Issues

#### 1. High Memory Usage
- Check for memory leaks in logs
- Restart bot if necessary
- Monitor memory usage over time

#### 2. Slow Response Times
- Check RPC endpoint latency
- Verify network connectivity
- Monitor rate limiting

#### 3. High CPU Usage
- Check for infinite loops
- Monitor trading frequency
- Optimize algorithms if necessary

## Security Best Practices

### 1. Key Management
- Never share private keys
- Use strong passphrases
- Rotate keys regularly
- Store keys securely

### 2. Network Security
- Use HTTPS for all connections
- Implement rate limiting
- Monitor for suspicious activity
- Use VPN if necessary

### 3. System Security
- Keep system updated
- Use minimal privileges
- Monitor file permissions
- Implement intrusion detection

## Compliance and Legal

### 1. Regulatory Compliance
- Check local regulations
- Implement required controls
- Maintain audit trails
- Report as required

### 2. Tax Implications
- Track all trades
- Calculate gains/losses
- Maintain records
- Consult tax professional

### 3. Risk Disclosure
- Understand risks involved
- Start with small amounts
- Never risk more than you can afford to lose
- Monitor performance regularly

## Support and Resources

### 1. Documentation
- README.md: Basic usage
- DEPLOYMENT.md: This file
- API documentation: In code
- Configuration guide: In config.py

### 2. Community
- GitHub Issues: Bug reports
- Discord: Community support
- Telegram: Updates and alerts
- Email: team@memebot.dev

### 3. Professional Support
- Consulting services available
- Custom development possible
- Training and workshops
- Emergency support

## Version History

- **v1.0.0**: Initial release
  - Basic trading functionality
  - Security features
  - Paper mode support
  - Comprehensive logging

## License

MIT License - see LICENSE file for details.

## Disclaimer

This software is provided "as is" without warranty of any kind. Trading cryptocurrencies involves significant risk and may result in substantial losses. Users are responsible for their own trading decisions and should never risk more than they can afford to lose.

The developers and contributors are not responsible for any financial losses incurred through the use of this software. Users should thoroughly test the software in paper mode before using it with real funds.

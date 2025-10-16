"""
Digital Wallet Manager for AI Trading Bot

This module manages a digital wallet for the AI trading bot, including:
- Wallet creation and management
- Profit tracking and reinvestment
- Transaction history
- Portfolio management
- Automatic profit reinvestment
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal, ROUND_DOWN
from src.utils.logger import get_logger
from src.security.wallet_manager import WalletManager
from src.trading.financial_integration import get_financial_manager, PaymentProvider, TransactionStatus, FinancialAccount
from src.security.solana_wallet_manager import SolanaWalletManager

logger = get_logger(__name__)


@dataclass
class WalletBalance:
    """Wallet balance for a specific token."""
    symbol: str
    balance: Decimal
    usd_value: Decimal
    last_updated: float
    chain: str = "Ethereum"  # Ethereum, Solana, etc.


@dataclass
class Transaction:
    """Transaction record."""
    tx_hash: str
    timestamp: float
    token_symbol: str
    amount: Decimal
    price: Decimal
    usd_value: Decimal
    transaction_type: str  # buy, sell, reinvest, withdraw
    gas_fee: Decimal = Decimal('0')
    chain: str = "Ethereum"
    status: str = "completed"


@dataclass
class ProfitRecord:
    """Profit tracking record."""
    timestamp: float
    initial_investment: Decimal
    current_value: Decimal
    profit_loss: Decimal
    profit_percentage: Decimal
    reinvested_amount: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int


class DigitalWalletManager:
    """
    Manages the AI trading bot's digital wallet with profit tracking and reinvestment.
    """
    
    def __init__(self):
        self.wallet_manager = WalletManager()
        self.solana_wallet_manager = SolanaWalletManager()
        
        # Financial integration
        self.financial_manager = get_financial_manager()
        self.primary_account_id = "acc_stripe_001"  # Default primary account
        
        # Wallet state
        self.initial_investment = Decimal('0')
        self.current_portfolio_value = Decimal('0')
        self.total_profit = Decimal('0')
        self.reinvested_profit = Decimal('0')
        
        # Transaction history
        self.transactions: List[Transaction] = []
        self.balances: Dict[str, WalletBalance] = {}
        
        # Profit tracking
        self.profit_records: List[ProfitRecord] = []
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        
        # Configuration
        self.reinvestment_threshold = Decimal('0.1')  # Reinvest when profit > 10%
        self.min_reinvestment_amount = Decimal('50')  # Minimum $50 to reinvest
        self.max_reinvestment_percentage = Decimal('0.8')  # Max 80% of profit
        
        # Load existing data
        self.load_wallet_data()
    
    def load_wallet_data(self):
        """Load wallet data from persistent storage."""
        try:
            # Load from JSON file (in production, use database)
            with open('data/wallet_data.json', 'r') as f:
                data = json.load(f)
                
            self.initial_investment = Decimal(str(data.get('initial_investment', 0)))
            self.current_portfolio_value = Decimal(str(data.get('current_portfolio_value', 0)))
            self.total_profit = Decimal(str(data.get('total_profit', 0)))
            self.reinvested_profit = Decimal(str(data.get('reinvested_profit', 0)))
            self.total_trades = data.get('total_trades', 0)
            self.winning_trades = data.get('winning_trades', 0)
            self.losing_trades = data.get('losing_trades', 0)
            
            # Load transactions
            for tx_data in data.get('transactions', []):
                tx = Transaction(
                    tx_hash=tx_data['tx_hash'],
                    timestamp=tx_data['timestamp'],
                    token_symbol=tx_data['token_symbol'],
                    amount=Decimal(str(tx_data['amount'])),
                    price=Decimal(str(tx_data['price'])),
                    usd_value=Decimal(str(tx_data['usd_value'])),
                    transaction_type=tx_data['transaction_type'],
                    gas_fee=Decimal(str(tx_data.get('gas_fee', 0))),
                    chain=tx_data.get('chain', 'Ethereum'),
                    status=tx_data.get('status', 'completed')
                )
                self.transactions.append(tx)
            
            # Load balances
            for symbol, balance_data in data.get('balances', {}).items():
                self.balances[symbol] = WalletBalance(
                    symbol=symbol,
                    balance=Decimal(str(balance_data['balance'])),
                    usd_value=Decimal(str(balance_data['usd_value'])),
                    last_updated=balance_data['last_updated'],
                    chain=balance_data.get('chain', 'Ethereum')
                )
            
            logger.info("Wallet data loaded successfully")
            
        except FileNotFoundError:
            logger.info("No existing wallet data found, starting fresh")
        except Exception as e:
            logger.error(f"Failed to load wallet data: {e}")
    
    def save_wallet_data(self):
        """Save wallet data to persistent storage."""
        try:
            data = {
                'initial_investment': float(self.initial_investment),
                'current_portfolio_value': float(self.current_portfolio_value),
                'total_profit': float(self.total_profit),
                'reinvested_profit': float(self.reinvested_profit),
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'transactions': [asdict(tx) for tx in self.transactions],
                'balances': {
                    symbol: {
                        'balance': float(balance.balance),
                        'usd_value': float(balance.usd_value),
                        'last_updated': balance.last_updated,
                        'chain': balance.chain
                    }
                    for symbol, balance in self.balances.items()
                }
            }
            
            with open('data/wallet_data.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Wallet data saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save wallet data: {e}")
    
    def initialize_wallet(self, initial_amount: Decimal, chain: str = "Ethereum") -> bool:
        """
        Initialize the wallet with initial investment.
        
        Args:
            initial_amount: Initial investment amount in USD
            chain: Blockchain to use (Ethereum, Solana)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.initial_investment > 0:
                logger.warning("Wallet already initialized")
                return False
            
            self.initial_investment = initial_amount
            self.current_portfolio_value = initial_amount
            
            # Create initial balance record
            self.balances['USD'] = WalletBalance(
                symbol='USD',
                balance=initial_amount,
                usd_value=initial_amount,
                last_updated=time.time(),
                chain=chain
            )
            
            # Record initial transaction
            tx = Transaction(
                tx_hash=f"init_{int(time.time())}",
                timestamp=time.time(),
                token_symbol='USD',
                amount=initial_amount,
                price=Decimal('1.0'),
                usd_value=initial_amount,
                transaction_type='deposit',
                chain=chain
            )
            self.transactions.append(tx)
            
            self.save_wallet_data()
            logger.info(f"Wallet initialized with ${initial_amount} on {chain}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize wallet: {e}")
            return False
    
    def get_financial_accounts(self) -> List[Dict[str, Any]]:
        """Get all connected financial accounts."""
        accounts = self.financial_manager.get_accounts()
        return [asdict(account) for account in accounts]
    
    def get_primary_account(self) -> Optional[Dict[str, Any]]:
        """Get the primary financial account."""
        account = self.financial_manager.get_account(self.primary_account_id)
        return asdict(account) if account else None
    
    def set_primary_account(self, account_id: str) -> bool:
        """Set the primary financial account."""
        account = self.financial_manager.get_account(account_id)
        if account:
            self.primary_account_id = account_id
            logger.info(f"Primary account set to {account_id}")
            return True
        return False
    
    def deposit_from_financial_account(self, account_id: str, amount: Decimal) -> bool:
        """
        Deposit funds from a financial account to the trading wallet.
        
        Args:
            account_id: Financial account ID
            amount: Amount to deposit
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create deposit transaction
            transaction = self.financial_manager.create_deposit(account_id, amount, "Deposit to trading wallet")
            
            if transaction and transaction.status == TransactionStatus.COMPLETED:
                # Update wallet balance
                self.current_portfolio_value += amount
                
                # Add to transaction history
                self._add_transaction(
                    transaction_type="deposit",
                    amount=amount,
                    description=f"Deposit from {account_id}",
                    status="completed"
                )
                
                logger.info(f"Deposited ${amount} from {account_id} to trading wallet")
                return True
            else:
                logger.error(f"Failed to deposit from {account_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error depositing from financial account: {e}")
            return False
    
    def withdraw_to_financial_account(self, account_id: str, amount: Decimal) -> bool:
        """
        Withdraw funds from the trading wallet to a financial account.
        
        Args:
            account_id: Financial account ID
            amount: Amount to withdraw
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.current_portfolio_value < amount:
                logger.error(f"Insufficient balance: ${self.current_portfolio_value} < ${amount}")
                return False
            
            # Create withdrawal transaction
            transaction = self.financial_manager.create_withdrawal(
                account_id, amount, "Trading wallet", "Withdrawal from trading wallet"
            )
            
            if transaction and transaction.status == TransactionStatus.COMPLETED:
                # Update wallet balance
                self.current_portfolio_value -= amount
                
                # Add to transaction history
                self._add_transaction(
                    transaction_type="withdrawal",
                    amount=amount,
                    description=f"Withdrawal to {account_id}",
                    status="completed"
                )
                
                logger.info(f"Withdrew ${amount} from trading wallet to {account_id}")
                return True
            else:
                logger.error(f"Failed to withdraw to {account_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error withdrawing to financial account: {e}")
            return False
    
    def transfer_between_financial_accounts(self, from_account_id: str, to_account_id: str, amount: Decimal) -> bool:
        """
        Transfer funds between financial accounts.
        
        Args:
            from_account_id: Source account ID
            to_account_id: Destination account ID
            amount: Transfer amount
        
        Returns:
            True if successful, False otherwise
        """
        try:
            transaction = self.financial_manager.transfer_between_accounts(
                from_account_id, to_account_id, amount, "Account transfer"
            )
            
            if transaction and transaction.status == TransactionStatus.COMPLETED:
                # Add to transaction history
                self._add_transaction(
                    transaction_type="transfer",
                    amount=amount,
                    description=f"Transfer from {from_account_id} to {to_account_id}",
                    status="completed"
                )
                
                logger.info(f"Transferred ${amount} from {from_account_id} to {to_account_id}")
                return True
            else:
                logger.error(f"Failed to transfer between accounts")
                return False
                
        except Exception as e:
            logger.error(f"Error transferring between financial accounts: {e}")
            return False
    
    def get_financial_transactions(self, account_id: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        """Get financial transaction history."""
        transactions = self.financial_manager.get_transactions(account_id, limit)
        return [asdict(transaction) for transaction in transactions]
    
    def get_total_financial_balance(self, currency: str = "USD") -> Decimal:
        """Get total balance across all financial accounts."""
        return self.financial_manager.get_total_balance(currency)
    
    def get_account_summary(self, account_id: str) -> Dict[str, Any]:
        """Get detailed account summary."""
        return self.financial_manager.get_account_summary(account_id)
    
    def verify_financial_account(self, account_id: str) -> bool:
        """Verify a financial account."""
        return self.financial_manager.verify_account(account_id)
    
    def get_payment_providers(self) -> List[Dict[str, Any]]:
        """Get available payment providers and their information."""
        providers = []
        for provider in PaymentProvider:
            info = self.financial_manager.get_provider_info(provider)
            if info:
                providers.append({
                    "provider": provider.value,
                    **info
                })
        return providers
    
    def get_accounts_by_provider(self, provider: str) -> List[Dict[str, Any]]:
        """Get accounts by provider name."""
        accounts = self.financial_manager.get_accounts()
        return [asdict(account) for account in accounts if account.provider.value == provider]
    
    def create_paypal_account(self, email: str, password: str) -> bool:
        """Create a new PayPal account connection."""
        try:
            # Simulate PayPal account creation
            account_id = f"acc_paypal_{int(time.time())}"
            
            # Create account in financial manager
            account = FinancialAccount(
                account_id=account_id,
                provider=PaymentProvider.PAYPAL,
                account_type="business",
                currency="USD",
                balance=Decimal('1000.00'),  # Mock initial balance
                account_name=f"PayPal Account ({email})",
                is_verified=True,
                created_at=time.time()
            )
            
            # Add to financial manager
            self.financial_manager.accounts[account_id] = account
            
            logger.info(f"PayPal account created for {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create PayPal account: {e}")
            return False
    
    def disconnect_paypal_account(self) -> bool:
        """Disconnect PayPal account."""
        try:
            # Find PayPal accounts
            paypal_accounts = [acc for acc in self.financial_manager.accounts.values() 
                              if acc.provider == PaymentProvider.PAYPAL]
            
            if not paypal_accounts:
                logger.warning("No PayPal accounts to disconnect")
                return False
            
            # Remove PayPal accounts
            for account in paypal_accounts:
                del self.financial_manager.accounts[account.account_id]
            
            logger.info("PayPal account disconnected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect PayPal account: {e}")
            return False
    
    def generate_solana_wallet(self) -> bool:
        """Generate a new Solana wallet."""
        try:
            # Generate new keypair
            success = self.solana_wallet_manager.generate_keypair()
            
            if success:
                logger.info("New Solana wallet generated successfully")
                return True
            else:
                logger.error("Failed to generate new Solana wallet")
                return False
                
        except Exception as e:
            logger.error(f"Failed to generate Solana wallet: {e}")
            return False
    
    def connect_solana_wallet(self, private_key: str) -> bool:
        """Connect to existing Solana wallet using private key."""
        try:
            # Load keypair from private key
            success = self.solana_wallet_manager.load_keypair_from_private_key(private_key)
            
            if success:
                logger.info("Solana wallet connected successfully")
                return True
            else:
                logger.error("Failed to connect Solana wallet")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect Solana wallet: {e}")
            return False
    
    def disconnect_solana_wallet(self) -> bool:
        """Disconnect Solana wallet."""
        try:
            # Clear keypair
            self.solana_wallet_manager.keypair = None
            logger.info("Solana wallet disconnected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to disconnect Solana wallet: {e}")
            return False
    
    def deposit_from_solana_wallet(self, amount: Decimal) -> bool:
        """Deposit funds from Solana wallet to trading wallet."""
        try:
            if not self.solana_wallet_manager.keypair:
                logger.error("No Solana wallet connected")
                return False
            
            # Simulate deposit from Solana wallet
            # In a real implementation, this would check Solana wallet balance
            # and transfer funds to the trading wallet
            
            # Update trading wallet balance
            self.current_portfolio_value += amount
            
            # Add to transaction history
            self._add_transaction(
                transaction_type="deposit",
                amount=amount,
                description="Deposit from Solana wallet",
                status="completed"
            )
            
            logger.info(f"Deposited ${amount} from Solana wallet to trading wallet")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deposit from Solana wallet: {e}")
            return False
    
    def withdraw_to_solana_wallet(self, amount: Decimal) -> bool:
        """Withdraw funds from trading wallet to Solana wallet."""
        try:
            if not self.solana_wallet_manager.keypair:
                logger.error("No Solana wallet connected")
                return False
            
            if self.current_portfolio_value < amount:
                logger.error(f"Insufficient balance: ${self.current_portfolio_value} < ${amount}")
                return False
            
            # Simulate withdrawal to Solana wallet
            # In a real implementation, this would transfer funds to the Solana wallet
            
            # Update trading wallet balance
            self.current_portfolio_value -= amount
            
            # Add to transaction history
            self._add_transaction(
                transaction_type="withdrawal",
                amount=amount,
                description="Withdrawal to Solana wallet",
                status="completed"
            )
            
            logger.info(f"Withdrew ${amount} from trading wallet to Solana wallet")
            return True
            
        except Exception as e:
            logger.error(f"Failed to withdraw to Solana wallet: {e}")
            return False
    
    def execute_trade(self, symbol: str, amount: Decimal, price: Decimal, 
                     trade_type: str, chain: str = "Ethereum") -> bool:
        """
        Execute a trade and update wallet balances.
        
        Args:
            symbol: Token symbol
            amount: Amount to trade
            price: Price per token
            trade_type: 'buy' or 'sell'
            chain: Blockchain chain
        
        Returns:
            True if successful, False otherwise
        """
        try:
            usd_value = amount * price
            
            if trade_type == 'buy':
                # Check if we have enough USD
                if symbol not in self.balances:
                    self.balances[symbol] = WalletBalance(
                        symbol=symbol,
                        balance=Decimal('0'),
                        usd_value=Decimal('0'),
                        last_updated=time.time(),
                        chain=chain
                    )
                
                if self.balances['USD'].balance < usd_value:
                    logger.error(f"Insufficient USD balance for buy order")
                    return False
                
                # Update balances
                self.balances['USD'].balance -= usd_value
                self.balances['USD'].usd_value = self.balances['USD'].balance
                self.balances[symbol].balance += amount
                self.balances[symbol].usd_value = self.balances[symbol].balance * price
                
            elif trade_type == 'sell':
                # Check if we have enough tokens
                if symbol not in self.balances or self.balances[symbol].balance < amount:
                    logger.error(f"Insufficient {symbol} balance for sell order")
                    return False
                
                # Update balances
                self.balances[symbol].balance -= amount
                self.balances[symbol].usd_value = self.balances[symbol].balance * price
                self.balances['USD'].balance += usd_value
                self.balances['USD'].usd_value = self.balances['USD'].balance
            
            # Record transaction
            tx = Transaction(
                tx_hash=f"trade_{int(time.time())}_{symbol}",
                timestamp=time.time(),
                token_symbol=symbol,
                amount=amount,
                price=price,
                usd_value=usd_value,
                transaction_type=trade_type,
                chain=chain
            )
            self.transactions.append(tx)
            
            # Update trade statistics
            self.total_trades += 1
            
            # Update portfolio value
            self.update_portfolio_value()
            
            # Check for profit reinvestment
            self.check_reinvestment_opportunity()
            
            self.save_wallet_data()
            logger.info(f"Trade executed: {trade_type} {amount} {symbol} at ${price}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return False
    
    def update_portfolio_value(self):
        """Update the current portfolio value."""
        try:
            total_value = Decimal('0')
            
            for balance in self.balances.values():
                total_value += balance.usd_value
            
            self.current_portfolio_value = total_value
            self.total_profit = total_value - self.initial_investment
            
            # Update profit records
            profit_record = ProfitRecord(
                timestamp=time.time(),
                initial_investment=self.initial_investment,
                current_value=total_value,
                profit_loss=self.total_profit,
                profit_percentage=(self.total_profit / self.initial_investment * 100) if self.initial_investment > 0 else Decimal('0'),
                reinvested_amount=self.reinvested_profit,
                total_trades=self.total_trades,
                winning_trades=self.winning_trades,
                losing_trades=self.losing_trades
            )
            self.profit_records.append(profit_record)
            
            # Keep only last 1000 records
            if len(self.profit_records) > 1000:
                self.profit_records = self.profit_records[-1000:]
            
        except Exception as e:
            logger.error(f"Failed to update portfolio value: {e}")
    
    def check_reinvestment_opportunity(self):
        """Check if we should reinvest profits."""
        try:
            if self.total_profit <= 0:
                return
            
            profit_percentage = self.total_profit / self.initial_investment
            
            if profit_percentage >= self.reinvestment_threshold:
                # Calculate reinvestment amount
                available_profit = self.total_profit - self.reinvested_profit
                reinvestment_amount = min(
                    available_profit * self.max_reinvestment_percentage,
                    available_profit
                )
                
                if reinvestment_amount >= self.min_reinvestment_amount:
                    # Execute reinvestment
                    self.execute_reinvestment(reinvestment_amount)
            
        except Exception as e:
            logger.error(f"Failed to check reinvestment opportunity: {e}")
    
    def execute_reinvestment(self, amount: Decimal):
        """Execute profit reinvestment."""
        try:
            # Add reinvested amount to USD balance
            self.balances['USD'].balance += amount
            self.balances['USD'].usd_value = self.balances['USD'].balance
            
            # Update reinvested profit tracking
            self.reinvested_profit += amount
            
            # Record reinvestment transaction
            tx = Transaction(
                tx_hash=f"reinvest_{int(time.time())}",
                timestamp=time.time(),
                token_symbol='USD',
                amount=amount,
                price=Decimal('1.0'),
                usd_value=amount,
                transaction_type='reinvest',
                chain='Ethereum'
            )
            self.transactions.append(tx)
            
            self.save_wallet_data()
            logger.info(f"Reinvested ${amount} from profits")
            
        except Exception as e:
            logger.error(f"Failed to execute reinvestment: {e}")
    
    def get_wallet_summary(self) -> Dict[str, Any]:
        """Get wallet summary information."""
        try:
            self.update_portfolio_value()
            
            return {
                'initial_investment': float(self.initial_investment),
                'current_value': float(self.current_portfolio_value),
                'total_profit': float(self.total_profit),
                'profit_percentage': float(self.total_profit / self.initial_investment * 100) if self.initial_investment > 0 else 0,
                'reinvested_profit': float(self.reinvested_profit),
                'total_trades': self.total_trades,
                'winning_trades': self.winning_trades,
                'losing_trades': self.losing_trades,
                'win_rate': (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0,
                'balances': {
                    symbol: {
                        'balance': float(balance.balance),
                        'usd_value': float(balance.usd_value),
                        'chain': balance.chain
                    }
                    for symbol, balance in self.balances.items()
                },
                'last_updated': time.time()
            }
            
        except Exception as e:
            logger.error(f"Failed to get wallet summary: {e}")
            return {}
    
    def get_transaction_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transaction history."""
        try:
            recent_transactions = self.transactions[-limit:] if self.transactions else []
            return [asdict(tx) for tx in recent_transactions]
            
        except Exception as e:
            logger.error(f"Failed to get transaction history: {e}")
            return []
    
    def get_profit_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get profit history."""
        try:
            recent_profits = self.profit_records[-limit:] if self.profit_records else []
            return [asdict(record) for record in recent_profits]
            
        except Exception as e:
            logger.error(f"Failed to get profit history: {e}")
            return []
    
    def withdraw_profit(self, amount: Decimal) -> bool:
        """
        Withdraw profit from the wallet.
        
        Args:
            amount: Amount to withdraw in USD
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if amount > self.total_profit:
                logger.error("Withdrawal amount exceeds available profit")
                return False
            
            if self.balances['USD'].balance < amount:
                logger.error("Insufficient USD balance for withdrawal")
                return False
            
            # Update balances
            self.balances['USD'].balance -= amount
            self.balances['USD'].usd_value = self.balances['USD'].balance
            
            # Record withdrawal transaction
            tx = Transaction(
                tx_hash=f"withdraw_{int(time.time())}",
                timestamp=time.time(),
                token_symbol='USD',
                amount=amount,
                price=Decimal('1.0'),
                usd_value=amount,
                transaction_type='withdraw',
                chain='Ethereum'
            )
            self.transactions.append(tx)
            
            self.update_portfolio_value()
            self.save_wallet_data()
            
            logger.info(f"Withdrew ${amount} from profits")
            return True
            
        except Exception as e:
            logger.error(f"Failed to withdraw profit: {e}")
            return False
    
    def get_reinvestment_status(self) -> Dict[str, Any]:
        """Get reinvestment status and recommendations."""
        try:
            if self.total_profit <= 0:
                return {
                    'can_reinvest': False,
                    'reason': 'No profit available',
                    'next_threshold': float(self.reinvestment_threshold * 100)
                }
            
            profit_percentage = self.total_profit / self.initial_investment
            available_profit = self.total_profit - self.reinvested_profit
            
            can_reinvest = (
                profit_percentage >= self.reinvestment_threshold and
                available_profit >= self.min_reinvestment_amount
            )
            
            if can_reinvest:
                reinvestment_amount = min(
                    available_profit * self.max_reinvestment_percentage,
                    available_profit
                )
                
                return {
                    'can_reinvest': True,
                    'available_profit': float(available_profit),
                    'recommended_amount': float(reinvestment_amount),
                    'profit_percentage': float(profit_percentage * 100),
                    'next_threshold': float(self.reinvestment_threshold * 100)
                }
            else:
                return {
                    'can_reinvest': False,
                    'reason': 'Threshold not met or insufficient profit',
                    'profit_percentage': float(profit_percentage * 100),
                    'next_threshold': float(self.reinvestment_threshold * 100),
                    'min_amount': float(self.min_reinvestment_amount)
                }
                
        except Exception as e:
            logger.error(f"Failed to get reinvestment status: {e}")
            return {}


# Global wallet manager instance
_wallet_manager: Optional[DigitalWalletManager] = None

def get_digital_wallet_manager() -> DigitalWalletManager:
    """Get the global digital wallet manager instance."""
    global _wallet_manager
    if _wallet_manager is None:
        _wallet_manager = DigitalWalletManager()
    return _wallet_manager


if __name__ == "__main__":
    # Test the wallet manager
    wallet = get_digital_wallet_manager()
    
    # Initialize with $1000
    wallet.initialize_wallet(Decimal('1000'))
    
    # Simulate some trades
    wallet.execute_trade('DOGE', Decimal('1000'), Decimal('0.08'), 'buy')
    wallet.execute_trade('DOGE', Decimal('500'), Decimal('0.12'), 'sell')
    
    # Get summary
    summary = wallet.get_wallet_summary()
    print("Wallet Summary:", json.dumps(summary, indent=2))
    
    # Get reinvestment status
    status = wallet.get_reinvestment_status()
    print("Reinvestment Status:", json.dumps(status, indent=2))

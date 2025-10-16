"""
Telegram signal ingestion and astroturf detection system.

This module provides comprehensive Telegram signal processing including:
- Telegram Bot API integration
- Message parsing and token extraction
- Astroturf detection heuristics
- Multi-source corroboration
- Rate limiting and throttling
- Social signal aggregation
"""

import asyncio
import time
import re
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

try:
    from telegram import Bot, Update
    from telegram.ext import Application, MessageHandler, filters, ContextTypes
    from telegram.error import TelegramError
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    # Mock classes for when Telegram is not available
    class Bot:
        def __init__(self, token):
            pass
    
    class Update:
        pass
    
    class ContextTypes:
        class DEFAULT_TYPE:
            pass
    
    class TelegramError(Exception):
        pass

from src.config import TRADING_CONFIG
from src.utils.logger import log_trading_event

logger = structlog.get_logger(__name__)


class SignalSource(Enum):
    """Signal source enumeration."""
    TELEGRAM = "telegram"
    TWITTER = "twitter"
    DISCORD = "discord"
    REDDIT = "reddit"
    OTHER = "other"


class SignalStrength(Enum):
    """Signal strength enumeration."""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


class AstroturfType(Enum):
    """Astroturf detection type enumeration."""
    SINGLE_ACCOUNT_AMPLIFICATION = "single_account_amplification"
    REPEATED_IDENTICAL_POSTS = "repeated_identical_posts"
    UNNATURAL_CADENCE = "unnatural_cadence"
    BOT_ACCOUNTS = "bot_accounts"
    FAKE_ENGAGEMENT = "fake_engagement"


@dataclass
class TelegramSignal:
    """Telegram signal data structure."""
    message_id: str
    chat_id: str
    user_id: str
    username: str
    text: str
    timestamp: float
    tokens_mentioned: List[str]
    signal_strength: SignalStrength
    astroturf_score: float
    astroturf_types: List[AstroturfType]
    metadata: Dict[str, Any]


@dataclass
class SocialSignal:
    """Social signal data structure."""
    signal_id: str
    source: SignalSource
    token_address: str
    signal_strength: SignalStrength
    timestamp: float
    message_count: int
    unique_users: int
    astroturf_score: float
    corroboration_score: float
    metadata: Dict[str, Any]


class TelegramListener:
    """
    Telegram signal ingestion and astroturf detection system.
    
    Features:
    - Telegram Bot API integration
    - Message parsing and token extraction
    - Astroturf detection heuristics
    - Multi-source corroboration
    - Rate limiting and throttling
    - Social signal aggregation
    """
    
    def __init__(self, bot_token: str, allowed_chats: List[str] = None):
        """
        Initialize Telegram listener.
        
        Args:
            bot_token: Telegram bot token
            allowed_chats: List of allowed chat IDs
        """
        self.bot_token = bot_token
        self.allowed_chats = allowed_chats or []
        
        # Signal tracking
        self.received_signals: List[TelegramSignal] = []
        self.aggregated_signals: Dict[str, SocialSignal] = {}
        self.signal_callbacks: List[Callable[[SocialSignal], None]] = []
        
        # Astroturf detection
        self.user_activity: Dict[str, List[float]] = {}  # user_id -> timestamps
        self.message_patterns: Dict[str, List[str]] = {}  # user_id -> messages
        self.token_mentions: Dict[str, List[str]] = {}  # token -> user_ids
        
        # Rate limiting
        self.message_times: List[float] = []
        self.max_messages_per_minute = 100
        
        # Telegram bot
        self.bot: Optional[Bot] = None
        self.application: Optional[Application] = None
        
        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task: Optional[asyncio.Task] = None
        
        # Token extraction patterns
        self.token_patterns = [
            r'0x[a-fA-F0-9]{40}',  # Ethereum addresses
            r'[A-Za-z0-9]{32,44}',  # Solana addresses (base58)
            r'\$[A-Z]{2,10}',  # Token symbols
            r'#([A-Z]{2,10})',  # Hashtag symbols
        ]
        
        logger.info("Telegram listener initialized", allowed_chats=len(self.allowed_chats))
    
    async def start_monitoring(self):
        """Start Telegram monitoring."""
        if self.is_monitoring:
            logger.warning("Telegram monitoring already started")
            return
        
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram libraries not available")
            return
        
        try:
            # Initialize bot
            self.bot = Bot(self.bot_token)
            self.application = Application.builder().token(self.bot_token).build()
            
            # Add message handler
            self.application.add_handler(
                MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message)
            )
            
            # Start monitoring
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # Start bot
            await self.application.initialize()
            await self.application.start()
            
            logger.info("Telegram monitoring started")
            log_trading_event("telegram_monitoring_started", {}, "INFO")
            
        except Exception as e:
            logger.error("Failed to start Telegram monitoring", error=str(e))
            self.is_monitoring = False
    
    async def stop_monitoring(self):
        """Stop Telegram monitoring."""
        if not self.is_monitoring:
            logger.warning("Telegram monitoring not started")
            return
        
        self.is_monitoring = False
        
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
        
        if self.application:
            await self.application.stop()
            await self.application.shutdown()
        
        logger.info("Telegram monitoring stopped")
        log_trading_event("telegram_monitoring_stopped", {}, "INFO")
    
    async def _monitoring_loop(self):
        """Main monitoring loop."""
        try:
            while self.is_monitoring:
                # Process received signals
                await self._process_received_signals()
                
                # Aggregate signals
                await self._aggregate_signals()
                
                # Cleanup old data
                await self._cleanup_old_data()
                
                # Wait before next iteration
                await asyncio.sleep(TRADING_CONFIG.WATCH_CADENCE_SECONDS)
                
        except asyncio.CancelledError:
            logger.info("Telegram monitoring loop cancelled")
        except Exception as e:
            logger.error("Telegram monitoring loop error", error=str(e))
            self.is_monitoring = False
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle incoming Telegram messages."""
        try:
            if not update.message or not update.message.text:
                return
            
            # Check if chat is allowed
            chat_id = str(update.message.chat_id)
            if self.allowed_chats and chat_id not in self.allowed_chats:
                return
            
            # Check rate limits
            if not self._check_rate_limit():
                logger.warning("Rate limit exceeded for Telegram messages")
                return
            
            # Extract message information
            message_id = str(update.message.message_id)
            user_id = str(update.message.from_user.id)
            username = update.message.from_user.username or "unknown"
            text = update.message.text
            timestamp = time.time()
            
            # Extract tokens from message
            tokens_mentioned = self._extract_tokens_from_text(text)
            
            if not tokens_mentioned:
                return  # No tokens mentioned, skip
            
            # Analyze for astroturf
            astroturf_score, astroturf_types = await self._analyze_astroturf(
                user_id, text, timestamp
            )
            
            # Calculate signal strength
            signal_strength = self._calculate_signal_strength(
                text, tokens_mentioned, astroturf_score
            )
            
            # Create signal
            signal = TelegramSignal(
                message_id=message_id,
                chat_id=chat_id,
                user_id=user_id,
                username=username,
                text=text,
                timestamp=timestamp,
                tokens_mentioned=tokens_mentioned,
                signal_strength=signal_strength,
                astroturf_score=astroturf_score,
                astroturf_types=astroturf_types,
                metadata={
                    "chat_title": update.message.chat.title,
                    "message_type": "text"
                }
            )
            
            # Store signal
            self.received_signals.append(signal)
            
            # Update tracking data
            self._update_tracking_data(user_id, text, timestamp, tokens_mentioned)
            
            # Log signal
            log_trading_event(
                "telegram_signal_received",
                {
                    "message_id": message_id,
                    "user_id": user_id,
                    "username": username,
                    "tokens_mentioned": tokens_mentioned,
                    "signal_strength": signal_strength.value,
                    "astroturf_score": astroturf_score,
                    "astroturf_types": [t.value for t in astroturf_types]
                },
                "INFO"
            )
            
        except Exception as e:
            logger.error("Failed to handle Telegram message", error=str(e))
    
    def _extract_tokens_from_text(self, text: str) -> List[str]:
        """Extract token addresses and symbols from text."""
        tokens = []
        
        for pattern in self.token_patterns:
            matches = re.findall(pattern, text)
            tokens.extend(matches)
        
        # Clean and validate tokens
        cleaned_tokens = []
        for token in tokens:
            # Remove prefixes and clean
            cleaned_token = token.replace('$', '').replace('#', '').strip()
            
            # Validate token format
            if self._is_valid_token(cleaned_token):
                cleaned_tokens.append(cleaned_token)
        
        return list(set(cleaned_tokens))  # Remove duplicates
    
    def _is_valid_token(self, token: str) -> bool:
        """Validate token format."""
        # Ethereum address
        if re.match(r'^0x[a-fA-F0-9]{40}$', token):
            return True
        
        # Solana address (base58)
        if re.match(r'^[A-Za-z0-9]{32,44}$', token):
            return True
        
        # Token symbol
        if re.match(r'^[A-Z]{2,10}$', token):
            return True
        
        return False
    
    async def _analyze_astroturf(self, user_id: str, text: str, timestamp: float) -> Tuple[float, List[AstroturfType]]:
        """Analyze message for astroturf patterns."""
        astroturf_score = 0.0
        astroturf_types = []
        
        try:
            # 1. Single account amplification
            if user_id in self.user_activity:
                recent_activity = [
                    t for t in self.user_activity[user_id] 
                    if timestamp - t < 3600  # Last hour
                ]
                
                if len(recent_activity) > 10:  # More than 10 messages per hour
                    astroturf_score += 0.3
                    astroturf_types.append(AstroturfType.SINGLE_ACCOUNT_AMPLIFICATION)
            
            # 2. Repeated identical posts
            if user_id in self.message_patterns:
                if text in self.message_patterns[user_id]:
                    astroturf_score += 0.4
                    astroturf_types.append(AstroturfType.REPEATED_IDENTICAL_POSTS)
            
            # 3. Unnatural cadence
            if user_id in self.user_activity:
                recent_times = self.user_activity[user_id][-10:]  # Last 10 messages
                if len(recent_times) >= 3:
                    intervals = [recent_times[i] - recent_times[i-1] for i in range(1, len(recent_times))]
                    avg_interval = sum(intervals) / len(intervals)
                    
                    # Check for very regular intervals (bot-like)
                    if avg_interval > 0 and max(intervals) - min(intervals) < 5:  # Within 5 seconds
                        astroturf_score += 0.2
                        astroturf_types.append(AstroturfType.UNNATURAL_CADENCE)
            
            # 4. Bot account detection
            if self._is_bot_account(text, user_id):
                astroturf_score += 0.5
                astroturf_types.append(AstroturfType.BOT_ACCOUNTS)
            
            # 5. Fake engagement patterns
            if self._has_fake_engagement_patterns(text):
                astroturf_score += 0.3
                astroturf_types.append(AstroturfType.FAKE_ENGAGEMENT)
            
            return min(1.0, astroturf_score), astroturf_types
            
        except Exception as e:
            logger.error("Astroturf analysis failed", error=str(e))
            return 0.0, []
    
    def _is_bot_account(self, text: str, user_id: str) -> bool:
        """Detect bot account patterns."""
        # Simple heuristics for bot detection
        bot_indicators = [
            len(text) < 10,  # Very short messages
            text.isupper(),  # All caps
            text.count('!') > 3,  # Excessive exclamation marks
            text.count('🚀') > 2,  # Excessive rocket emojis
            'moon' in text.lower() and 'lamb' in text.lower(),  # Moon/lambo spam
        ]
        
        return sum(bot_indicators) >= 2
    
    def _has_fake_engagement_patterns(self, text: str) -> bool:
        """Detect fake engagement patterns."""
        fake_patterns = [
            'to the moon',
            'diamond hands',
            'hodl',
            'wen lambo',
            'this is the way',
            'ape in',
            'yolo',
        ]
        
        text_lower = text.lower()
        return sum(1 for pattern in fake_patterns if pattern in text_lower) >= 2
    
    def _calculate_signal_strength(self, text: str, tokens: List[str], astroturf_score: float) -> SignalStrength:
        """Calculate signal strength based on various factors."""
        try:
            base_score = 0.0
            
            # Token count factor
            base_score += min(0.3, len(tokens) * 0.1)
            
            # Text length factor
            base_score += min(0.2, len(text) / 1000)
            
            # Keyword factors
            strong_keywords = ['buy', 'pump', 'moon', 'gem', 'diamond', 'hodl']
            weak_keywords = ['sell', 'dump', 'scam', 'rug', 'honeypot']
            
            text_lower = text.lower()
            strong_count = sum(1 for kw in strong_keywords if kw in text_lower)
            weak_count = sum(1 for kw in weak_keywords if kw in text_lower)
            
            base_score += min(0.3, strong_count * 0.1)
            base_score -= min(0.2, weak_count * 0.1)
            
            # Apply astroturf penalty
            base_score *= (1.0 - astroturf_score)
            
            # Convert to signal strength
            if base_score >= 0.7:
                return SignalStrength.VERY_STRONG
            elif base_score >= 0.5:
                return SignalStrength.STRONG
            elif base_score >= 0.3:
                return SignalStrength.MODERATE
            else:
                return SignalStrength.WEAK
                
        except Exception as e:
            logger.error("Signal strength calculation failed", error=str(e))
            return SignalStrength.WEAK
    
    def _update_tracking_data(self, user_id: str, text: str, timestamp: float, tokens: List[str]):
        """Update tracking data for astroturf detection."""
        try:
            # Update user activity
            if user_id not in self.user_activity:
                self.user_activity[user_id] = []
            self.user_activity[user_id].append(timestamp)
            
            # Keep only recent activity (last 24 hours)
            self.user_activity[user_id] = [
                t for t in self.user_activity[user_id] 
                if timestamp - t < 86400
            ]
            
            # Update message patterns
            if user_id not in self.message_patterns:
                self.message_patterns[user_id] = []
            self.message_patterns[user_id].append(text)
            
            # Keep only recent messages (last 100)
            self.message_patterns[user_id] = self.message_patterns[user_id][-100:]
            
            # Update token mentions
            for token in tokens:
                if token not in self.token_mentions:
                    self.token_mentions[token] = []
                if user_id not in self.token_mentions[token]:
                    self.token_mentions[token].append(user_id)
            
        except Exception as e:
            logger.error("Failed to update tracking data", error=str(e))
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        current_time = time.time()
        
        # Remove old message times
        self.message_times = [t for t in self.message_times if current_time - t < 60]
        
        # Check if within limits
        if len(self.message_times) >= self.max_messages_per_minute:
            return False
        
        # Add current message time
        self.message_times.append(current_time)
        return True
    
    async def _process_received_signals(self):
        """Process received Telegram signals."""
        try:
            # Process signals that haven't been processed yet
            unprocessed_signals = [
                signal for signal in self.received_signals
                if signal.timestamp > time.time() - 3600  # Last hour
            ]
            
            for signal in unprocessed_signals:
                # Skip signals with high astroturf score
                if signal.astroturf_score > 0.7:
                    continue
                
                # Skip weak signals
                if signal.signal_strength == SignalStrength.WEAK:
                    continue
                
                # Process signal for each token
                for token in signal.tokens_mentioned:
                    await self._process_token_signal(signal, token)
                    
        except Exception as e:
            logger.error("Failed to process received signals", error=str(e))
    
    async def _process_token_signal(self, signal: TelegramSignal, token: str):
        """Process a signal for a specific token."""
        try:
            # Check if we already have a signal for this token
            if token in self.aggregated_signals:
                existing_signal = self.aggregated_signals[token]
                
                # Update existing signal
                existing_signal.message_count += 1
                existing_signal.unique_users = len(set(
                    existing_signal.metadata.get("user_ids", []) + [signal.user_id]
                ))
                existing_signal.metadata["user_ids"] = list(set(
                    existing_signal.metadata.get("user_ids", []) + [signal.user_id]
                ))
                
                # Recalculate corroboration score
                existing_signal.corroboration_score = self._calculate_corroboration_score(
                    existing_signal.message_count,
                    existing_signal.unique_users,
                    existing_signal.astroturf_score
                )
                
            else:
                # Create new aggregated signal
                aggregated_signal = SocialSignal(
                    signal_id=f"telegram_{token}_{int(time.time())}",
                    source=SignalSource.TELEGRAM,
                    token_address=token,
                    signal_strength=signal.signal_strength,
                    timestamp=signal.timestamp,
                    message_count=1,
                    unique_users=1,
                    astroturf_score=signal.astroturf_score,
                    corroboration_score=0.5,  # Initial score
                    metadata={
                        "user_ids": [signal.user_id],
                        "chat_ids": [signal.chat_id],
                        "first_message": signal.text
                    }
                )
                
                self.aggregated_signals[token] = aggregated_signal
            
        except Exception as e:
            logger.error("Failed to process token signal", error=str(e))
    
    def _calculate_corroboration_score(self, message_count: int, unique_users: int, astroturf_score: float) -> float:
        """Calculate corroboration score based on multiple factors."""
        try:
            # Base score from message count
            message_score = min(0.4, message_count * 0.1)
            
            # User diversity score
            user_score = min(0.4, unique_users * 0.1)
            
            # Astroturf penalty
            astroturf_penalty = astroturf_score * 0.3
            
            # Calculate final score
            score = message_score + user_score - astroturf_penalty
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error("Corroboration score calculation failed", error=str(e))
            return 0.0
    
    async def _aggregate_signals(self):
        """Aggregate signals and notify callbacks."""
        try:
            # Find signals that meet corroboration threshold
            threshold = 0.6  # Minimum corroboration score
            
            for token, signal in self.aggregated_signals.items():
                if signal.corroboration_score >= threshold:
                    # Notify callbacks
                    for callback in self.signal_callbacks:
                        try:
                            callback(signal)
                        except Exception as e:
                            logger.error("Signal callback error", error=str(e))
                    
                    # Log aggregated signal
                    log_trading_event(
                        "telegram_signal_aggregated",
                        {
                            "token": token,
                            "message_count": signal.message_count,
                            "unique_users": signal.unique_users,
                            "corroboration_score": signal.corroboration_score,
                            "signal_strength": signal.signal_strength.value
                        },
                        "INFO"
                    )
                    
        except Exception as e:
            logger.error("Failed to aggregate signals", error=str(e))
    
    async def _cleanup_old_data(self):
        """Cleanup old data to prevent memory leaks."""
        try:
            current_time = time.time()
            
            # Cleanup old signals
            self.received_signals = [
                signal for signal in self.received_signals
                if current_time - signal.timestamp < 86400  # Keep last 24 hours
            ]
            
            # Cleanup old aggregated signals
            self.aggregated_signals = {
                token: signal for token, signal in self.aggregated_signals.items()
                if current_time - signal.timestamp < 86400  # Keep last 24 hours
            }
            
            # Cleanup old user activity
            for user_id in list(self.user_activity.keys()):
                self.user_activity[user_id] = [
                    t for t in self.user_activity[user_id]
                    if current_time - t < 86400  # Keep last 24 hours
                ]
                
                if not self.user_activity[user_id]:
                    del self.user_activity[user_id]
            
        except Exception as e:
            logger.error("Failed to cleanup old data", error=str(e))
    
    def add_signal_callback(self, callback: Callable[[SocialSignal], None]):
        """Add a signal callback."""
        self.signal_callbacks.append(callback)
    
    def remove_signal_callback(self, callback: Callable[[SocialSignal], None]):
        """Remove a signal callback."""
        if callback in self.signal_callbacks:
            self.signal_callbacks.remove(callback)
    
    def get_received_signals(self, limit: int = 100) -> List[TelegramSignal]:
        """Get recent received signals."""
        return self.received_signals[-limit:] if self.received_signals else []
    
    def get_aggregated_signals(self) -> Dict[str, SocialSignal]:
        """Get all aggregated signals."""
        return self.aggregated_signals.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get Telegram listener status."""
        return {
            "is_monitoring": self.is_monitoring,
            "received_signals": len(self.received_signals),
            "aggregated_signals": len(self.aggregated_signals),
            "tracked_users": len(self.user_activity),
            "tracked_tokens": len(self.token_mentions),
            "signal_callbacks": len(self.signal_callbacks),
            "allowed_chats": len(self.allowed_chats)
        }


# Global Telegram listener instance
_telegram_listener: Optional[TelegramListener] = None


def get_telegram_listener(bot_token: str = None, allowed_chats: List[str] = None) -> TelegramListener:
    """
    Get the global Telegram listener instance.
    
    Args:
        bot_token: Telegram bot token
        allowed_chats: List of allowed chat IDs
        
    Returns:
        Telegram listener instance
    """
    global _telegram_listener
    
    if _telegram_listener is None:
        if not bot_token:
            import os
            bot_token = os.getenv("TELEGRAMBOTTOKEN")
        
        if not bot_token:
            raise ValueError("Telegram bot token not provided")
        
        _telegram_listener = TelegramListener(bot_token, allowed_chats)
    
    return _telegram_listener

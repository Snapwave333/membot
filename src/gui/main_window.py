"""
Main GUI window for the meme-coin trading bot.

This module provides a secure native GUI interface using PySide6
with real-time monitoring, control panels, and security features.
"""

import sys
import time
from typing import Dict, Any
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTabWidget, QTableWidget,
    QTableWidgetItem, QGroupBox, QGridLayout, QFrame,
    QSpinBox, QDoubleSpinBox, QCheckBox, QMessageBox, QSlider,
    QProgressBar, QComboBox, QSplitter, QScrollArea
)
from PySide6.QtCore import QThread, Signal, Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont, QPalette, QColor, QLinearGradient, QPainter
from decimal import Decimal


from src.config import TRADING_CONFIG, SAFETY_CONFIG
from src.trading.risk_manager import get_risk_manager
from src.trading.digital_wallet_manager import get_digital_wallet_manager
from src.security.memecoin_scam_detector import get_scam_detector
from src.utils.logger import get_logger
from src.gui.sprite_manager import get_sprite_manager
from src.data.live_market_fetcher import fetch_market_data_sync
from src.mcp.axiom_mcp_server import call_axiom_tool_sync

logger = get_logger(__name__)


class CollapsibleGroupBox(QGroupBox):
    """Custom collapsible group box widget."""
    
    def __init__(self, title="", parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.toggled.connect(self._on_toggled)
        
        # Store the original layout
        self._original_layout = None
        self._content_widget = None
        
        # Style the toggle button
        self.setStyleSheet("""
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                font-weight: bold;
                color: #00F5D4;
            }
            QGroupBox {
                border: 2px solid rgba(0, 245, 212, 0.3);
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background: rgba(27, 31, 59, 0.1);
            }
            QGroupBox::indicator {
                width: 16px;
                height: 16px;
            }
            QGroupBox::indicator:checked {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNkw2IDhMMTIgMiIgc3Ryb2tlPSIjMDBGNUQ0IiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgo8L3N2Zz4K);
            }
            QGroupBox::indicator:unchecked {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAxNiAxNiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTQgNEgxMlYxMkg0VjRaIiBzdHJva2U9IiM4ODg4ODgiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+Cjwvc3ZnPgo=);
            }
        """)
    
    def setContentLayout(self, layout):
        """Set the content layout for the collapsible group."""
        self._original_layout = layout
        super().setLayout(layout)
    
    def _on_toggled(self, checked):
        """Handle toggle state change."""
        if self._original_layout:
            for i in range(self._original_layout.count()):
                item = self._original_layout.itemAt(i)
                if item and item.widget():
                    item.widget().setVisible(checked)
    
    def addWidget(self, widget):
        """Add a widget to the collapsible group."""
        if not self._original_layout:
            self._original_layout = QVBoxLayout()
            self.setContentLayout(self._original_layout)
        
        self._original_layout.addWidget(widget)
        widget.setVisible(self.isChecked())


class BotStatusThread(QThread):
    """Thread for updating bot status."""
    
    status_updated = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.running = True
    
    def run(self):
        """Run the status update loop."""
        while self.running:
            try:
                # Get current status
                risk_manager = get_risk_manager()
                risk_metrics = risk_manager.get_risk_metrics()
                
                status = {
                    "portfolio_value": risk_metrics.portfolio_value,
                    "total_pnl": risk_metrics.total_pnl,
                    "daily_pnl": risk_metrics.daily_pnl,
                    "max_drawdown": risk_metrics.max_drawdown,
                    "position_count": risk_metrics.position_count,
                    "risk_level": risk_metrics.risk_level.value,
                    "kill_switch_active": risk_metrics.kill_switch_active,
                    "timestamp": time.time()
                }
                
                self.status_updated.emit(status)
                
            except Exception as e:
                logger.error("Failed to update bot status", error=str(e))
            
            self.msleep(1000)  # Update every second
    
    def stop(self):
        """Stop the status update thread."""
        self.running = False


class MainWindow(QMainWindow):
    """
    Main GUI window for the trading bot.
    
    Features:
    - Real-time status monitoring
    - Position management
    - Risk controls
    - Emergency controls
    - Security features
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NeoMeme Markets: Where Trends Meet Trades")
        self.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.risk_manager = get_risk_manager()
        self.wallet_manager = get_digital_wallet_manager()
        self.scam_detector = get_scam_detector()
        self.status_thread = BotStatusThread()
        self.status_thread.status_updated.connect(self.update_status)
        self.sprite_manager = get_sprite_manager()
        
        # Market mode state
        self.market_mode = "Simulation"  # "Simulation" or "Live Market"
        self.live_market_data = {}  # Cache for live market data
        
        # Setup UI
        self.setup_ui()
        self.setup_styles()
        
        # Start status updates
        self.status_thread.start()
        
        # Setup animation timer for bot persona
        self.persona_timer = QTimer()
        self.persona_timer.timeout.connect(self.update_bot_persona)
        self.persona_timer.start(2000)  # Update every 2 seconds
        
        # Setup ticker update timer
        self.ticker_timer = QTimer()
        self.ticker_timer.timeout.connect(self.update_ticker_prices)
        self.ticker_timer.start(1000)  # Update every second
        
        # Setup live market data timer (slower for real API calls)
        self.live_market_timer = QTimer()
        self.live_market_timer.timeout.connect(self.fetch_live_market_data)
        self.live_market_timer.start(5000)  # Update every 5 seconds for live data
        
        # Setup wallet update timer
        self.wallet_timer = QTimer()
        self.wallet_timer.timeout.connect(self.update_wallet_display)
        self.wallet_timer.start(10000)  # Update every 10 seconds
        
        logger.info("Main window initialized")
    
    def setup_header(self, parent_layout):
        """Setup the header section with title and bot persona."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.NoFrame)
        header_layout = QHBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("NeoMeme Markets")
        title_label.setObjectName("title_label")
        header_layout.addWidget(title_label)
        
        # Bot persona indicator with sprite support
        persona_frame = QFrame()
        persona_frame.setFixedSize(60, 60)
        persona_frame.setStyleSheet("""
            QFrame {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    stop:0 #00F5D4, stop:0.7 #00C4A3, stop:1 #1B1F3B);
                border: 2px solid #00F5D4;
                border-radius: 30px;
            }
        """)
        
        # Bot status indicator with sprite
        self.bot_status_indicator = self.sprite_manager.create_sprite_label("avatar_bot_neutral")
        self.bot_status_indicator.setAlignment(Qt.AlignCenter)
        self.bot_status_indicator.setFixedSize(40, 40)
        
        persona_layout = QVBoxLayout(persona_frame)
        persona_layout.addWidget(self.bot_status_indicator)
        
        header_layout.addWidget(persona_frame)
        header_layout.addStretch()
        
        # Market mode toggle
        market_mode_label = QLabel("Market Mode:")
        self.market_mode_combo = QComboBox()
        self.market_mode_combo.addItems(["Simulation", "Live Market"])
        self.market_mode_combo.setCurrentText("Simulation")
        self.market_mode_combo.currentTextChanged.connect(self.change_market_mode)
        
        header_layout.addWidget(market_mode_label)
        header_layout.addWidget(self.market_mode_combo)
        
        # Theme selector
        theme_label = QLabel("Theme:")
        theme_combo = QComboBox()
        theme_combo.addItems(["Classic", "CyberGlow", "MemeLite"])
        theme_combo.setCurrentText("Classic")
        theme_combo.currentTextChanged.connect(self.change_theme)
        
        header_layout.addWidget(theme_label)
        header_layout.addWidget(theme_combo)
        
        parent_layout.addWidget(header_frame)
    
    def change_theme(self, theme_name):
        """Change the application theme."""
        if theme_name == "CyberGlow":
            self.apply_cyberglow_theme()
        elif theme_name == "MemeLite":
            self.apply_memelite_theme()
        else:
            self.setup_styles()  # Default Classic theme
    
    def apply_cyberglow_theme(self):
        """Apply CyberGlow theme with enhanced glow effects."""
        cyberglow_styles = """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0A0A0A, stop:1 #1A1A2E);
            }
            QGroupBox {
                background: rgba(10, 10, 10, 0.9);
                border: 2px solid #00FFFF;
                box-shadow: 0 0 20px rgba(0, 255, 255, 0.3);
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00FFFF, stop:1 #0080FF);
                box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
            }
            QPushButton:hover {
                box-shadow: 0 0 25px rgba(0, 255, 255, 0.8);
            }
        """
        self.setStyleSheet(cyberglow_styles)
    
    def apply_memelite_theme(self):
        """Apply MemeLite theme with lighter, playful colors."""
        memelite_styles = """
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #FFE5E5, stop:1 #E5F3FF);
            }
            QGroupBox {
                background: rgba(255, 255, 255, 0.9);
                border: 2px solid #FF6B6B;
                color: #333333;
            }
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF6B6B, stop:1 #FFD93D);
                color: #FFFFFF;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF7B7B, stop:1 #FFE066);
            }
        """
        self.setStyleSheet(memelite_styles)
    
    def change_market_mode(self, mode):
        """Change between simulation and live market mode."""
        self.market_mode = mode
        
        if mode == "Live Market":
            # Switch to live market mode
            self.show_market_mode_notification("Switching to Live Market Mode", 
                "Connecting to real market data sources...")
            
            # Initialize live market data
            self.initialize_live_market_data()
            
            # Update UI to show live mode
            self.update_live_market_indicators()
            
        else:
            # Switch to simulation mode
            self.show_market_mode_notification("Switching to Simulation Mode", 
                "Using simulated market data for testing...")
            
            # Update UI to show simulation mode
            self.update_simulation_indicators()
        
        logger.info(f"Market mode changed to: {mode}")
    
    def initialize_live_market_data(self):
        """Initialize live market data structure."""
        self.live_market_data = {
            "DOGE": {"price": 0.0, "change": 0.0, "volume": 0, "last_update": None},
            "SHIB": {"price": 0.0, "change": 0.0, "volume": 0, "last_update": None},
            "PEPE": {"price": 0.0, "change": 0.0, "volume": 0, "last_update": None},
            "BONK": {"price": 0.0, "change": 0.0, "volume": 0, "last_update": None},
            "WIF": {"price": 0.0, "change": 0.0, "volume": 0, "last_update": None}
        }
    
    def fetch_live_market_data(self):
        """Fetch live market data from real APIs."""
        if self.market_mode != "Live Market":
            return
        
        try:
            # Fetch real market data
            symbols = list(self.live_market_data.keys())
            market_data = fetch_market_data_sync(symbols)
            
            if market_data:
                # Update with real data
                for symbol, data in market_data.items():
                    if symbol in self.live_market_data:
                        self.live_market_data[symbol]["price"] = data.price
                        self.live_market_data[symbol]["change"] = data.change_24h
                        self.live_market_data[symbol]["volume"] = data.volume_24h
                        self.live_market_data[symbol]["last_update"] = data.last_update
                
                # Update sentiment based on real market movement
                avg_change = sum(data["change"] for data in self.live_market_data.values()) / len(self.live_market_data)
                self.update_live_sentiment(avg_change)
                
                logger.info(f"Fetched live market data for {len(market_data)} symbols")
            else:
                # Fallback to simulated data if API fails
                self._fallback_to_simulated_data()
                
        except Exception as e:
            logger.error(f"Failed to fetch live market data: {e}")
            # Fallback to simulation if live data fails
            self._fallback_to_simulated_data()
    
    def _fallback_to_simulated_data(self):
        """Fallback to simulated data when live data fails."""
        import random
        import time
        
        for symbol in self.live_market_data.keys():
            current_data = self.live_market_data[symbol]
            
            if current_data["price"] == 0.0:
                # Initialize with realistic starting prices
                base_prices = {
                    "DOGE": 0.08,
                    "SHIB": 0.000025,
                    "PEPE": 0.0000012,
                    "BONK": 0.000034,
                    "WIF": 0.00018
                }
                current_data["price"] = base_prices.get(symbol, 0.01)
            else:
                # Simulate realistic price movements (±2% max per update)
                change_percent = random.uniform(-0.02, 0.02)
                current_data["price"] *= (1 + change_percent)
            
            # Calculate 24h change
            current_data["change"] = random.uniform(-0.15, 0.15)  # ±15% max
            
            # Simulate volume
            current_data["volume"] = random.randint(1000000, 50000000)
            current_data["last_update"] = time.time()
        
        # Update sentiment based on simulated market movement
        if self.live_market_data:
            avg_change = sum(data["change"] for data in self.live_market_data.values()) / len(self.live_market_data)
            self.update_live_sentiment(avg_change)
        
        # Show warning about fallback
        self.statusBar().showMessage("Live Market: Using simulated data (API unavailable)", 5000)
    
    def update_live_market_indicators(self):
        """Update UI indicators for live market mode."""
        # Update ticker labels to show live mode
        for symbol in self.ticker_labels.keys():
            label = self.ticker_labels[symbol]
            label.setToolTip(f"Live market data for {symbol}")
        
        # Update sentiment indicator
        if hasattr(self, 'sentiment_indicator'):
            self.sentiment_indicator.setToolTip("Live market sentiment analysis")
        
        # Update status bar
        self.statusBar().showMessage("Market Mode: Live Market Data")
    
    def update_simulation_indicators(self):
        """Update UI indicators for simulation mode."""
        # Update ticker labels to show simulation mode
        for symbol in self.ticker_labels.keys():
            label = self.ticker_labels[symbol]
            label.setToolTip(f"Simulated market data for {symbol}")
        
        # Update sentiment indicator
        if hasattr(self, 'sentiment_indicator'):
            self.sentiment_indicator.setToolTip("Simulated market sentiment")
        
        # Update status bar
        self.statusBar().showMessage("Market Mode: Simulation")
    
    def update_live_sentiment(self, avg_change):
        """Update sentiment based on live market data."""
        if avg_change > 0.05:  # >5% average gain
            self.sentiment_indicator.setText("📈")
            self.sentiment_indicator.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    background: rgba(0, 255, 0, 0.2);
                    border-radius: 20px;
                    padding: 10px;
                }
            """)
        elif avg_change < -0.05:  # >5% average loss
            self.sentiment_indicator.setText("📉")
            self.sentiment_indicator.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    background: rgba(255, 0, 0, 0.2);
                    border-radius: 20px;
                    padding: 10px;
                }
            """)
        else:  # Neutral
            self.sentiment_indicator.setText("😐")
            self.sentiment_indicator.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    background: rgba(255, 255, 0, 0.2);
                    border-radius: 20px;
                    padding: 10px;
                }
            """)
    
    def show_market_mode_notification(self, title, message):
        """Show a notification when market mode changes."""
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background: rgba(27, 31, 59, 0.95);
                color: #FFFFFF;
            }
            QMessageBox QPushButton {
                background: #00F5D4;
                color: #1B1F3B;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        msg.exec()
    
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Header section
        self.setup_header(main_layout)
        
        # Status bar
        self.setup_status_bar()
        
        # Control panel
        self.setup_control_panel(main_layout)
        
        # Main content area
        self.setup_main_content(main_layout)
        
        # Bottom panel
        self.setup_bottom_panel(main_layout)
    
    def setup_status_bar(self):
        """Setup the status bar."""
        self.statusBar().showMessage("Bot Status: Initializing...")
        
        # Add status indicators
        self.market_mode_label = QLabel("Mode: Simulation")
        self.risk_level_label = QLabel("Risk: Unknown")
        self.kill_switch_label = QLabel("Kill Switch: Unknown")
        self.position_count_label = QLabel("Positions: 0")
        
        self.statusBar().addPermanentWidget(self.market_mode_label)
        self.statusBar().addPermanentWidget(self.risk_level_label)
        self.statusBar().addPermanentWidget(self.kill_switch_label)
        self.statusBar().addPermanentWidget(self.position_count_label)
    
    def setup_control_panel(self, parent_layout):
        """Setup the control panel."""
        control_group = QGroupBox("Bot Controls")
        control_layout = QHBoxLayout(control_group)
        
        # Emergency controls
        self.kill_switch_button = QPushButton("Activate Kill Switch")
        self.kill_switch_button.clicked.connect(self.activate_kill_switch)
        self.kill_switch_button.setObjectName("kill_switch")
        
        self.emergency_stop_button = QPushButton("Emergency Stop")
        self.emergency_stop_button.clicked.connect(self.emergency_stop)
        self.emergency_stop_button.setObjectName("emergency_stop")
        
        # Normal controls
        self.pause_button = QPushButton("Pause Bot")
        self.pause_button.clicked.connect(self.pause_bot)
        
        self.resume_button = QPushButton("Resume Bot")
        self.resume_button.clicked.connect(self.resume_bot)
        self.resume_button.setEnabled(False)
        
        # Add to layout
        control_layout.addWidget(self.kill_switch_button)
        control_layout.addWidget(self.emergency_stop_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.resume_button)
        control_layout.addStretch()
        
        parent_layout.addWidget(control_group)
    
    def setup_main_content(self, parent_layout):
        """Setup the main content area."""
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Status tab
        self.setup_status_tab()
        
        # Positions tab
        self.setup_positions_tab()
        
        # Risk tab
        self.setup_risk_tab()
        
        # Logs tab
        self.setup_logs_tab()
        
        # Trade console tab
        self.setup_trade_console_tab()
        
        # Axiom.trade tab
        self.setup_axiom_tab()
        
        # Digital Wallet tab
        self.setup_wallet_tab()
        
        # Scam Detection tab
        self.setup_scam_detection_tab()
        
        parent_layout.addWidget(self.tab_widget)
    
    def setup_status_tab(self):
        """Setup the status tab with collapsible sections."""
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        
        # Add scroll area for better navigation
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Portfolio metrics
        portfolio_group = CollapsibleGroupBox("Portfolio Metrics")
        portfolio_layout = QGridLayout(portfolio_group)
        
        # Portfolio value
        portfolio_layout.addWidget(QLabel("Portfolio Value:"), 0, 0)
        self.portfolio_value_label = QLabel("$0.00")
        self.portfolio_value_label.setFont(QFont("Arial", 12, QFont.Bold))
        portfolio_layout.addWidget(self.portfolio_value_label, 0, 1)
        
        # Total P&L
        portfolio_layout.addWidget(QLabel("Total P&L:"), 1, 0)
        self.total_pnl_label = QLabel("$0.00")
        self.total_pnl_label.setFont(QFont("Arial", 12, QFont.Bold))
        portfolio_layout.addWidget(self.total_pnl_label, 1, 1)
        
        # Daily P&L
        portfolio_layout.addWidget(QLabel("Daily P&L:"), 2, 0)
        self.daily_pnl_label = QLabel("$0.00")
        self.daily_pnl_label.setFont(QFont("Arial", 12, QFont.Bold))
        portfolio_layout.addWidget(self.daily_pnl_label, 2, 1)
        
        # Max drawdown
        portfolio_layout.addWidget(QLabel("Max Drawdown:"), 3, 0)
        self.max_drawdown_label = QLabel("0.00%")
        self.max_drawdown_label.setFont(QFont("Arial", 12, QFont.Bold))
        portfolio_layout.addWidget(self.max_drawdown_label, 3, 1)
        
        # Risk level
        portfolio_layout.addWidget(QLabel("Risk Level:"), 4, 0)
        self.risk_level_status_label = QLabel("Unknown")
        self.risk_level_status_label.setFont(QFont("Arial", 12, QFont.Bold))
        portfolio_layout.addWidget(self.risk_level_status_label, 4, 1)
        
        portfolio_group.setContentLayout(portfolio_layout)
        scroll_layout.addWidget(portfolio_group)
        
        # Live ticker panel
        ticker_group = CollapsibleGroupBox("Live Meme Asset Prices")
        ticker_layout = QGridLayout(ticker_group)
        
        # Mock ticker data
        ticker_symbols = ["DOGE", "SHIB", "PEPE", "BONK", "WIF"]
        self.ticker_labels = {}
        
        for i, symbol in enumerate(ticker_symbols):
            symbol_label = QLabel(symbol)
            symbol_label.setStyleSheet("font-weight: bold; color: #00F5D4;")
            ticker_layout.addWidget(symbol_label, 0, i)
            
            price_label = QLabel(f"${0.00001 * (i + 1):.6f}")
            price_label.setStyleSheet("font-family: 'Courier New', monospace;")
            self.ticker_labels[symbol] = price_label
            ticker_layout.addWidget(price_label, 1, i)
            
            change_label = QLabel(f"+{i * 2.5:.1f}%")
            change_label.setStyleSheet("color: #00FF00;" if i % 2 == 0 else "color: #FF0000;")
            ticker_layout.addWidget(change_label, 2, i)
        
        ticker_group.setContentLayout(ticker_layout)
        scroll_layout.addWidget(ticker_group)
        
        # Sentiment analyzer
        sentiment_group = CollapsibleGroupBox("Market Sentiment Analyzer")
        sentiment_layout = QVBoxLayout(sentiment_group)
        
        # Sentiment gauge
        sentiment_frame = QFrame()
        sentiment_frame.setFixedHeight(100)
        sentiment_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF0000, stop:0.5 #FFD93D, stop:1 #00FF00);
                border-radius: 10px;
                border: 2px solid #00F5D4;
            }
        """)
        
        # Sentiment indicator
        self.sentiment_indicator = QLabel("😐")
        self.sentiment_indicator.setStyleSheet("""
            QLabel {
                font-size: 24px;
                background: rgba(27, 31, 59, 0.8);
                border-radius: 20px;
                padding: 10px;
            }
        """)
        self.sentiment_indicator.setAlignment(Qt.AlignCenter)
        
        sentiment_layout.addWidget(sentiment_frame)
        sentiment_layout.addWidget(self.sentiment_indicator)
        
        # Sentiment sources
        sources_layout = QHBoxLayout()
        sources_label = QLabel("Sources: Reddit • Twitter • Discord")
        sources_label.setStyleSheet("color: #888888; font-size: 12px;")
        sources_layout.addWidget(sources_label)
        sources_layout.addStretch()
        
        sentiment_layout.addLayout(sources_layout)
        sentiment_group.setContentLayout(sentiment_layout)
        scroll_layout.addWidget(sentiment_group)
        
        # Bot status
        bot_status_group = CollapsibleGroupBox("Bot Status")
        bot_status_layout = QVBoxLayout(bot_status_group)
        
        self.bot_status_text = QTextEdit()
        self.bot_status_text.setMaximumHeight(200)
        self.bot_status_text.setReadOnly(True)
        bot_status_layout.addWidget(self.bot_status_text)
        
        bot_status_group.setContentLayout(bot_status_layout)
        scroll_layout.addWidget(bot_status_group)
        
        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(27, 31, 59, 0.3);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 245, 212, 0.5);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 245, 212, 0.7);
            }
        """)
        
        status_layout.addWidget(scroll_area)
        self.tab_widget.addTab(status_widget, "Status")
    
    def setup_positions_tab(self):
        """Setup the positions tab."""
        positions_widget = QWidget()
        positions_layout = QVBoxLayout(positions_widget)
        
        # Positions table
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(8)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Side", "Amount", "Entry Price", "Current Price",
            "Unrealized P&L", "Status", "Created"
        ])
        positions_layout.addWidget(self.positions_table)
        
        # Position controls
        position_controls_layout = QHBoxLayout()
        
        self.close_position_button = QPushButton("Close Selected Position")
        self.close_position_button.clicked.connect(self.close_selected_position)
        
        self.refresh_positions_button = QPushButton("Refresh Positions")
        self.refresh_positions_button.clicked.connect(self.refresh_positions)
        
        position_controls_layout.addWidget(self.close_position_button)
        position_controls_layout.addWidget(self.refresh_positions_button)
        position_controls_layout.addStretch()
        
        positions_layout.addLayout(position_controls_layout)
        
        self.tab_widget.addTab(positions_widget, "Positions")
    
    def setup_risk_tab(self):
        """Setup the risk tab."""
        risk_widget = QWidget()
        risk_layout = QVBoxLayout(risk_widget)
        
        # Risk settings
        risk_settings_group = QGroupBox("Risk Settings")
        risk_settings_layout = QGridLayout(risk_settings_group)
        
        # Daily max loss
        risk_settings_layout.addWidget(QLabel("Daily Max Loss (%):"), 0, 0)
        self.daily_max_loss_spinbox = QDoubleSpinBox()
        self.daily_max_loss_spinbox.setRange(0.1, 50.0)
        self.daily_max_loss_spinbox.setValue(TRADING_CONFIG.DAILY_MAX_LOSS_PERCENT)
        self.daily_max_loss_spinbox.setSuffix("%")
        risk_settings_layout.addWidget(self.daily_max_loss_spinbox, 0, 1)
        
        # Per trade percentage
        risk_settings_layout.addWidget(QLabel("Per Trade (%):"), 1, 0)
        self.per_trade_spinbox = QDoubleSpinBox()
        self.per_trade_spinbox.setRange(0.1, 10.0)
        self.per_trade_spinbox.setValue(TRADING_CONFIG.PER_TRADE_PCT)
        self.per_trade_spinbox.setSuffix("%")
        risk_settings_layout.addWidget(self.per_trade_spinbox, 1, 1)
        
        # Max concurrent positions
        risk_settings_layout.addWidget(QLabel("Max Positions:"), 2, 0)
        self.max_positions_spinbox = QSpinBox()
        self.max_positions_spinbox.setRange(1, 20)
        self.max_positions_spinbox.setValue(TRADING_CONFIG.MAX_CONCURRENT_POSITIONS)
        risk_settings_layout.addWidget(self.max_positions_spinbox, 2, 1)
        
        # Profit target
        risk_settings_layout.addWidget(QLabel("Profit Target (%):"), 3, 0)
        self.profit_target_spinbox = QDoubleSpinBox()
        self.profit_target_spinbox.setRange(1.0, 100.0)
        self.profit_target_spinbox.setValue(TRADING_CONFIG.PROFIT_TARGET_PCT)
        self.profit_target_spinbox.setSuffix("%")
        risk_settings_layout.addWidget(self.profit_target_spinbox, 3, 1)
        
        # Hard stop
        risk_settings_layout.addWidget(QLabel("Hard Stop (%):"), 4, 0)
        self.hard_stop_spinbox = QDoubleSpinBox()
        self.hard_stop_spinbox.setRange(0.1, 50.0)
        self.hard_stop_spinbox.setValue(TRADING_CONFIG.HARD_STOP_PCT)
        self.hard_stop_spinbox.setSuffix("%")
        risk_settings_layout.addWidget(self.hard_stop_spinbox, 4, 1)
        
        risk_layout.addWidget(risk_settings_group)
        
        # Risk controls
        risk_controls_layout = QHBoxLayout()
        
        self.apply_risk_settings_button = QPushButton("Apply Risk Settings")
        self.apply_risk_settings_button.clicked.connect(self.apply_risk_settings)
        
        self.reset_risk_settings_button = QPushButton("Reset to Defaults")
        self.reset_risk_settings_button.clicked.connect(self.reset_risk_settings)
        
        risk_controls_layout.addWidget(self.apply_risk_settings_button)
        risk_controls_layout.addWidget(self.reset_risk_settings_button)
        risk_controls_layout.addStretch()
        
        risk_layout.addLayout(risk_controls_layout)
        
        self.tab_widget.addTab(risk_widget, "Risk")
    
    def setup_logs_tab(self):
        """Setup the logs tab."""
        logs_widget = QWidget()
        logs_layout = QVBoxLayout(logs_widget)
        
        # Log display
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Courier", 9))
        logs_layout.addWidget(self.logs_text)
        
        # Log controls
        log_controls_layout = QHBoxLayout()
        
        self.clear_logs_button = QPushButton("Clear Logs")
        self.clear_logs_button.clicked.connect(self.clear_logs)
        
        self.auto_scroll_checkbox = QCheckBox("Auto-scroll")
        self.auto_scroll_checkbox.setChecked(True)
        
        log_controls_layout.addWidget(self.clear_logs_button)
        log_controls_layout.addWidget(self.auto_scroll_checkbox)
        log_controls_layout.addStretch()
        
        logs_layout.addLayout(log_controls_layout)
        
        self.tab_widget.addTab(logs_widget, "Logs")
    
    def setup_trade_console_tab(self):
        """Setup the trade console tab."""
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        # Trade console header
        console_header = QLabel("Professional Trading Console")
        console_header.setStyleSheet("""
            QLabel {
                font-family: 'Montserrat', sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #00F5D4;
                padding: 10px;
                background: rgba(0, 245, 212, 0.1);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        console_layout.addWidget(console_header)
        
        # Trade controls
        trade_controls_group = QGroupBox("Trade Controls")
        trade_controls_layout = QGridLayout(trade_controls_group)
        
        # Symbol selection
        trade_controls_layout.addWidget(QLabel("Symbol:"), 0, 0)
        self.symbol_combo = QComboBox()
        self.symbol_combo.addItems(["DOGE", "SHIB", "PEPE", "BONK", "WIF"])
        trade_controls_layout.addWidget(self.symbol_combo, 0, 1)
        
        # Amount input
        trade_controls_layout.addWidget(QLabel("Amount:"), 1, 0)
        self.amount_spinbox = QDoubleSpinBox()
        self.amount_spinbox.setRange(0.001, 10000.0)
        self.amount_spinbox.setValue(100.0)
        self.amount_spinbox.setSuffix(" USD")
        trade_controls_layout.addWidget(self.amount_spinbox, 1, 1)
        
        # Trade buttons
        button_layout = QHBoxLayout()
        
        self.buy_button = QPushButton("BUY")
        self.buy_button.setIcon(self.sprite_manager.get_icon("icon_buy"))
        self.buy_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00FF00, stop:1 #00CC00);
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
                padding: 15px 30px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00FF20, stop:1 #00DD00);
                box-shadow: 0 0 20px rgba(0, 255, 0, 0.5);
            }
        """)
        self.buy_button.clicked.connect(self.execute_buy)
        
        self.sell_button = QPushButton("SELL")
        self.sell_button.setIcon(self.sprite_manager.get_icon("icon_sell"))
        self.sell_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF0000, stop:1 #CC0000);
                color: #FFFFFF;
                font-weight: bold;
                font-size: 16px;
                padding: 15px 30px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF2020, stop:1 #DD0000);
                box-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
            }
        """)
        self.sell_button.clicked.connect(self.execute_sell)
        
        self.hold_button = QPushButton("HOLD")
        self.hold_button.setIcon(self.sprite_manager.get_icon("icon_hold"))
        self.hold_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFD93D, stop:1 #FFA500);
                color: #1B1F3B;
                font-weight: bold;
                font-size: 16px;
                padding: 15px 30px;
                border-radius: 10px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFE066, stop:1 #FFB84D);
                box-shadow: 0 0 20px rgba(255, 217, 61, 0.5);
            }
        """)
        self.hold_button.clicked.connect(self.execute_hold)
        
        button_layout.addWidget(self.buy_button)
        button_layout.addWidget(self.sell_button)
        button_layout.addWidget(self.hold_button)
        
        trade_controls_layout.addLayout(button_layout, 2, 0, 1, 2)
        console_layout.addWidget(trade_controls_group)
        
        # Trade history
        history_group = QGroupBox("Recent Trades")
        history_layout = QVBoxLayout(history_group)
        
        self.trade_history_table = QTableWidget()
        self.trade_history_table.setColumnCount(6)
        self.trade_history_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Action", "Amount", "Price", "Status"
        ])
        self.trade_history_table.setMaximumHeight(200)
        history_layout.addWidget(self.trade_history_table)
        
        console_layout.addWidget(history_group)
        
        # Market analysis
        analysis_group = QGroupBox("Market Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        
        self.market_analysis_text = QTextEdit()
        self.market_analysis_text.setMaximumHeight(150)
        self.market_analysis_text.setReadOnly(True)
        self.market_analysis_text.setPlainText(
            "Market Analysis:\n"
            "• DOGE showing strong momentum with 15% gain\n"
            "• SHIB consolidating near support levels\n"
            "• PEPE breaking resistance, bullish signal\n"
            "• Overall sentiment: BULLISH 📈\n"
            "• Recommendation: Consider buying DOGE and PEPE"
        )
        analysis_layout.addWidget(self.market_analysis_text)
        
        console_layout.addWidget(analysis_group)
        
        self.tab_widget.addTab(console_widget, "Trade Console")
    
    def setup_axiom_tab(self):
        """Setup the Axiom.trade discovery tab."""
        axiom_widget = QWidget()
        axiom_layout = QVBoxLayout(axiom_widget)
        
        # Axiom.trade header
        axiom_header = QLabel("Axiom.trade Discovery")
        axiom_header.setStyleSheet("""
            QLabel {
                font-family: 'Montserrat', sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #00F5D4;
                padding: 10px;
                background: rgba(0, 245, 212, 0.1);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        axiom_layout.addWidget(axiom_header)
        
        # Trending tokens section
        trending_group = QGroupBox("Trending Meme Coins")
        trending_layout = QVBoxLayout(trending_group)
        
        # Refresh button
        refresh_layout = QHBoxLayout()
        self.refresh_axiom_button = QPushButton("Refresh Trending")
        self.refresh_axiom_button.clicked.connect(self.refresh_axiom_data)
        self.refresh_axiom_button.setIcon(self.sprite_manager.get_icon("icon_buy"))
        
        # Timeframe selector
        timeframe_label = QLabel("Timeframe:")
        self.timeframe_combo = QComboBox()
        self.timeframe_combo.addItems(["1m", "5m", "30m", "1h", "24h"])
        self.timeframe_combo.setCurrentText("1h")
        
        refresh_layout.addWidget(self.refresh_axiom_button)
        refresh_layout.addWidget(timeframe_label)
        refresh_layout.addWidget(self.timeframe_combo)
        refresh_layout.addStretch()
        
        trending_layout.addLayout(refresh_layout)
        
        # Trending tokens table
        self.axiom_tokens_table = QTableWidget()
        self.axiom_tokens_table.setColumnCount(8)
        self.axiom_tokens_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Price", "24h Change", "Market Cap", "Volume", "Trend Score", "DEX"
        ])
        self.axiom_tokens_table.setMaximumHeight(300)
        trending_layout.addWidget(self.axiom_tokens_table)
        
        axiom_layout.addWidget(trending_group)
        
        # Market overview section
        overview_group = QGroupBox("Market Overview")
        overview_layout = QGridLayout(overview_group)
        
        # Overview metrics
        self.total_tokens_label = QLabel("Total Tokens: 0")
        self.total_volume_label = QLabel("24h Volume: $0")
        self.total_liquidity_label = QLabel("Total Liquidity: $0")
        self.active_tokens_label = QLabel("Active Tokens: 0")
        
        overview_layout.addWidget(self.total_tokens_label, 0, 0)
        overview_layout.addWidget(self.total_volume_label, 0, 1)
        overview_layout.addWidget(self.total_liquidity_label, 1, 0)
        overview_layout.addWidget(self.active_tokens_label, 1, 1)
        
        axiom_layout.addWidget(overview_group)
        
        # Top performers section
        performers_group = QGroupBox("Top Performers")
        performers_layout = QHBoxLayout(performers_group)
        
        # Top gainers
        gainers_layout = QVBoxLayout()
        gainers_label = QLabel("Top Gainers")
        gainers_label.setStyleSheet("color: #00FF00; font-weight: bold;")
        self.top_gainers_list = QTextEdit()
        self.top_gainers_list.setMaximumHeight(100)
        self.top_gainers_list.setReadOnly(True)
        
        gainers_layout.addWidget(gainers_label)
        gainers_layout.addWidget(self.top_gainers_list)
        
        # Top losers
        losers_layout = QVBoxLayout()
        losers_label = QLabel("Top Losers")
        losers_label.setStyleSheet("color: #FF0000; font-weight: bold;")
        self.top_losers_list = QTextEdit()
        self.top_losers_list.setMaximumHeight(100)
        self.top_losers_list.setReadOnly(True)
        
        losers_layout.addWidget(losers_label)
        losers_layout.addWidget(self.top_losers_list)
        
        performers_layout.addLayout(gainers_layout)
        performers_layout.addLayout(losers_layout)
        
        axiom_layout.addWidget(performers_group)
        
        # Search section
        search_group = QGroupBox("Token Search")
        search_layout = QHBoxLayout(search_group)
        
        self.search_input = QTextEdit()
        self.search_input.setMaximumHeight(30)
        self.search_input.setPlaceholderText("Search for tokens...")
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_axiom_tokens)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        
        axiom_layout.addWidget(search_group)
        
        # Load initial data
        self.refresh_axiom_data()
        
        self.tab_widget.addTab(axiom_widget, "Axiom.trade")
    
    def refresh_axiom_data(self):
        """Refresh Axiom.trade data."""
        try:
            # Get trending tokens
            timeframe = self.timeframe_combo.currentText()
            result = call_axiom_tool_sync("get_trending_tokens", {
                "limit": 20,
                "timeframe": timeframe
            })
            
            if result.get("success") and "data" in result:
                self.update_axiom_tokens_table(result["data"]["tokens"])
            
            # Get market overview
            overview_result = call_axiom_tool_sync("get_market_overview", {})
            if overview_result.get("success") and "data" in overview_result:
                self.update_market_overview(overview_result["data"])
            
            logger.info("Axiom.trade data refreshed successfully")
            
        except Exception as e:
            logger.error(f"Failed to refresh Axiom.trade data: {e}")
            self.show_trade_notification(f"Axiom.trade Error: Failed to refresh data: {e}")
    
    def update_axiom_tokens_table(self, tokens):
        """Update the Axiom tokens table."""
        self.axiom_tokens_table.setRowCount(len(tokens))
        
        for row, token in enumerate(tokens):
            self.axiom_tokens_table.setItem(row, 0, QTableWidgetItem(token["symbol"]))
            self.axiom_tokens_table.setItem(row, 1, QTableWidgetItem(token["name"]))
            self.axiom_tokens_table.setItem(row, 2, QTableWidgetItem(f"${token['price']:.8f}"))
            
            # Color code the change
            change_item = QTableWidgetItem(f"{token['price_change_24h']:.2%}")
            if token['price_change_24h'] > 0:
                change_item.setForeground(QColor("#00FF00"))
                font = change_item.font()
                font.setBold(True)
                change_item.setFont(font)
            else:
                change_item.setForeground(QColor("#FF0000"))
                font = change_item.font()
                font.setBold(True)
                change_item.setFont(font)
            self.axiom_tokens_table.setItem(row, 3, change_item)
            
            self.axiom_tokens_table.setItem(row, 4, QTableWidgetItem(f"${token['market_cap']:,.0f}"))
            self.axiom_tokens_table.setItem(row, 5, QTableWidgetItem(f"${token['volume_24h']:,.0f}"))
            self.axiom_tokens_table.setItem(row, 6, QTableWidgetItem(f"{token['trend_score']:.1f}"))
            self.axiom_tokens_table.setItem(row, 7, QTableWidgetItem(token["dex"]))
    
    def update_market_overview(self, overview_data):
        """Update the market overview section."""
        self.total_tokens_label.setText(f"Total Tokens: {overview_data['total_tokens']:,}")
        self.total_volume_label.setText(f"24h Volume: ${overview_data['total_volume_24h']:,.0f}")
        self.total_liquidity_label.setText(f"Total Liquidity: ${overview_data['total_liquidity']:,.0f}")
        self.active_tokens_label.setText(f"Active Tokens: {overview_data['active_tokens']:,}")
        
        # Update top gainers
        gainers_text = ""
        for gainer in overview_data.get("top_gainers", []):
            gainers_text += f"{gainer['symbol']}: +{gainer['change']:.1f}%\n"
        self.top_gainers_list.setPlainText(gainers_text)
        
        # Update top losers
        losers_text = ""
        for loser in overview_data.get("top_losers", []):
            losers_text += f"{loser['symbol']}: {loser['change']:.1f}%\n"
        self.top_losers_list.setPlainText(losers_text)
    
    def search_axiom_tokens(self):
        """Search for tokens on Axiom.trade."""
        try:
            query = self.search_input.toPlainText().strip()
            if not query:
                return
            
            result = call_axiom_tool_sync("search_tokens", {
                "query": query,
                "limit": 10
            })
            
            if result.get("success") and "data" in result:
                search_results = result["data"]["results"]
                if search_results:
                    # Update the tokens table with search results
                    self.update_axiom_tokens_table(search_results)
                    self.show_trade_notification(f"Search Results: Found {len(search_results)} tokens for '{query}'")
                else:
                    self.show_trade_notification(f"No Results: No tokens found for '{query}'")
            
        except Exception as e:
            logger.error(f"Failed to search Axiom.trade: {e}")
            self.show_trade_notification(f"Search Error: Failed to search: {e}")
    
    def setup_wallet_tab(self):
        """Setup the digital wallet tab with collapsible sections."""
        wallet_widget = QWidget()
        wallet_layout = QVBoxLayout(wallet_widget)
        
        # Add scroll area for better navigation
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Wallet header
        wallet_header = QLabel("AI Digital Wallet")
        wallet_header.setStyleSheet("""
            QLabel {
                font-family: 'Montserrat', sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #00F5D4;
                padding: 10px;
                background: rgba(0, 245, 212, 0.1);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        scroll_layout.addWidget(wallet_header)
        
        # Wallet summary section
        summary_group = CollapsibleGroupBox("Portfolio Summary")
        summary_layout = QGridLayout(summary_group)
        
        # Summary labels
        self.initial_investment_label = QLabel("Initial Investment: $0.00")
        self.current_value_label = QLabel("Current Value: $0.00")
        self.total_profit_label = QLabel("Total Profit: $0.00")
        self.profit_percentage_label = QLabel("Profit %: 0.00%")
        self.reinvested_label = QLabel("Reinvested: $0.00")
        
        # Style profit labels
        self.total_profit_label.setStyleSheet("font-weight: bold; color: #00FF00;")
        self.profit_percentage_label.setStyleSheet("font-weight: bold; color: #00FF00;")
        
        summary_layout.addWidget(self.initial_investment_label, 0, 0)
        summary_layout.addWidget(self.current_value_label, 0, 1)
        summary_layout.addWidget(self.total_profit_label, 1, 0)
        summary_layout.addWidget(self.profit_percentage_label, 1, 1)
        summary_layout.addWidget(self.reinvested_label, 2, 0)
        
        summary_group.setContentLayout(summary_layout)
        scroll_layout.addWidget(summary_group)
        
        # Wallet controls section
        controls_group = CollapsibleGroupBox("Wallet Controls")
        controls_layout = QVBoxLayout(controls_group)
        
        # Initialize wallet button
        init_layout = QHBoxLayout()
        self.init_amount_input = QDoubleSpinBox()
        self.init_amount_input.setRange(100, 100000)
        self.init_amount_input.setValue(1000)
        self.init_amount_input.setSuffix(" USD")
        
        self.init_wallet_button = QPushButton("Initialize Wallet")
        self.init_wallet_button.clicked.connect(self.initialize_wallet)
        
        init_layout.addWidget(QLabel("Initial Amount:"))
        init_layout.addWidget(self.init_amount_input)
        init_layout.addWidget(self.init_wallet_button)
        init_layout.addStretch()
        
        controls_layout.addLayout(init_layout)
        
        # Reinvestment controls
        reinvest_layout = QHBoxLayout()
        self.reinvest_button = QPushButton("Reinvest Profits")
        self.reinvest_button.clicked.connect(self.manual_reinvest)
        self.reinvest_button.setEnabled(False)
        
        self.withdraw_button = QPushButton("Withdraw Profits")
        self.withdraw_button.clicked.connect(self.withdraw_profits)
        self.withdraw_button.setEnabled(False)
        
        reinvest_layout.addWidget(self.reinvest_button)
        reinvest_layout.addWidget(self.withdraw_button)
        reinvest_layout.addStretch()
        
        controls_layout.addLayout(reinvest_layout)
        
        controls_group.setContentLayout(controls_layout)
        scroll_layout.addWidget(controls_group)
        
        # Balances section
        balances_group = CollapsibleGroupBox("Token Balances")
        balances_layout = QVBoxLayout(balances_group)
        
        self.balances_table = QTableWidget()
        self.balances_table.setColumnCount(4)
        self.balances_table.setHorizontalHeaderLabels([
            "Token", "Balance", "USD Value", "Chain"
        ])
        self.balances_table.setMaximumHeight(200)
        balances_layout.addWidget(self.balances_table)
        
        balances_group.setContentLayout(balances_layout)
        scroll_layout.addWidget(balances_group)
        
        # Transaction history section
        history_group = CollapsibleGroupBox("Recent Transactions")
        history_layout = QVBoxLayout(history_group)
        
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(7)
        self.transactions_table.setHorizontalHeaderLabels([
            "Time", "Type", "Token", "Amount", "Price", "Value", "Status"
        ])
        self.transactions_table.setMaximumHeight(200)
        history_layout.addWidget(self.transactions_table)
        
        history_group.setContentLayout(history_layout)
        scroll_layout.addWidget(history_group)
        
        # Reinvestment status section
        status_group = CollapsibleGroupBox("Reinvestment Status")
        status_layout = QVBoxLayout(status_group)
        
        self.reinvestment_status_label = QLabel("No profit available for reinvestment")
        self.reinvestment_status_label.setWordWrap(True)
        status_layout.addWidget(self.reinvestment_status_label)
        
        status_group.setContentLayout(status_layout)
        scroll_layout.addWidget(status_group)
        
        # Financial integration section
        financial_group = CollapsibleGroupBox("Financial Institution Integration")
        financial_layout = QVBoxLayout(financial_group)
        
        # Account selection
        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("Primary Account:"))
        self.primary_account_combo = QComboBox()
        self.primary_account_combo.currentTextChanged.connect(self.change_primary_account)
        account_layout.addWidget(self.primary_account_combo)
        
        # Account balance display
        self.financial_balance_label = QLabel("Total Balance: $0.00")
        self.financial_balance_label.setStyleSheet("font-weight: bold; color: #00F5D4;")
        account_layout.addWidget(self.financial_balance_label)
        
        financial_layout.addLayout(account_layout)
        
        # Solana wallet integration section
        solana_group = CollapsibleGroupBox("Solana Wallet Integration")
        solana_layout = QVBoxLayout(solana_group)
        
        # Solana wallet status
        solana_status_layout = QHBoxLayout()
        self.solana_status_label = QLabel("Solana Wallet: Not Connected")
        self.solana_status_label.setStyleSheet("font-weight: bold; color: #FF6B6B;")
        solana_status_layout.addWidget(self.solana_status_label)
        
        # Solana connect button
        self.connect_solana_button = QPushButton("Connect Solana Wallet")
        self.connect_solana_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #9945FF, stop:1 #14F195);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7A35CC, stop:1 #0FD180);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5A2599, stop:1 #0BB066);
            }
        """)
        self.connect_solana_button.clicked.connect(self.connect_solana_wallet)
        solana_status_layout.addWidget(self.connect_solana_button)
        
        # Solana disconnect button
        self.disconnect_solana_button = QPushButton("Disconnect")
        self.disconnect_solana_button.setStyleSheet("""
            QPushButton {
                background: #FF6B6B;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #FF5252;
            }
            QPushButton:pressed {
                background: #E53E3E;
            }
        """)
        self.disconnect_solana_button.clicked.connect(self.disconnect_solana_wallet)
        self.disconnect_solana_button.setVisible(False)
        solana_status_layout.addWidget(self.disconnect_solana_button)
        
        solana_layout.addLayout(solana_status_layout)
        
        # Solana wallet info
        self.solana_info_label = QLabel("No Solana wallet connected")
        self.solana_info_label.setStyleSheet("color: #888888; font-size: 12px;")
        self.solana_info_label.setWordWrap(True)
        solana_layout.addWidget(self.solana_info_label)
        
        # Solana quick actions
        solana_actions_layout = QHBoxLayout()
        
        self.solana_deposit_button = QPushButton("Quick Deposit from Solana")
        self.solana_deposit_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00C851, stop:1 #00A041);
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00A041, stop:1 #007A31);
            }
        """)
        self.solana_deposit_button.clicked.connect(self.quick_solana_deposit)
        self.solana_deposit_button.setEnabled(False)
        solana_actions_layout.addWidget(self.solana_deposit_button)
        
        self.solana_withdraw_button = QPushButton("Quick Withdraw to Solana")
        self.solana_withdraw_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B, stop:1 #E53E3E);
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #E53E3E, stop:1 #C53030);
            }
        """)
        self.solana_withdraw_button.clicked.connect(self.quick_solana_withdraw)
        self.solana_withdraw_button.setEnabled(False)
        solana_actions_layout.addWidget(self.solana_withdraw_button)
        
        solana_layout.addLayout(solana_actions_layout)
        
        financial_group.addWidget(solana_group)
        
        # Financial operations
        operations_layout = QHBoxLayout()
        
        # Deposit section
        deposit_layout = QVBoxLayout()
        deposit_layout.addWidget(QLabel("Deposit to Trading Wallet"))
        
        deposit_input_layout = QHBoxLayout()
        self.deposit_amount_input = QDoubleSpinBox()
        self.deposit_amount_input.setRange(1.0, 100000.0)
        self.deposit_amount_input.setSuffix(" USD")
        deposit_input_layout.addWidget(self.deposit_amount_input)
        
        self.deposit_button = QPushButton("Deposit")
        self.deposit_button.clicked.connect(self.deposit_from_financial_account)
        deposit_input_layout.addWidget(self.deposit_button)
        
        deposit_layout.addLayout(deposit_input_layout)
        operations_layout.addLayout(deposit_layout)
        
        # Withdrawal section
        withdrawal_layout = QVBoxLayout()
        withdrawal_layout.addWidget(QLabel("Withdraw from Trading Wallet"))
        
        withdrawal_input_layout = QHBoxLayout()
        self.withdrawal_amount_input = QDoubleSpinBox()
        self.withdrawal_amount_input.setRange(1.0, 100000.0)
        self.withdrawal_amount_input.setSuffix(" USD")
        withdrawal_input_layout.addWidget(self.withdrawal_amount_input)
        
        self.withdrawal_button = QPushButton("Withdraw")
        self.withdrawal_button.clicked.connect(self.withdraw_to_financial_account)
        withdrawal_input_layout.addWidget(self.withdrawal_button)
        
        withdrawal_layout.addLayout(withdrawal_input_layout)
        operations_layout.addLayout(withdrawal_layout)
        
        financial_layout.addLayout(operations_layout)
        
        # Financial accounts table
        self.financial_accounts_table = QTableWidget()
        self.financial_accounts_table.setColumnCount(5)
        self.financial_accounts_table.setHorizontalHeaderLabels([
            "Account", "Provider", "Type", "Balance", "Status"
        ])
        self.financial_accounts_table.setMaximumHeight(150)
        financial_layout.addWidget(self.financial_accounts_table)
        
        # Financial transactions table
        self.financial_transactions_table = QTableWidget()
        self.financial_transactions_table.setColumnCount(6)
        self.financial_transactions_table.setHorizontalHeaderLabels([
            "Time", "Type", "Amount", "Account", "Status", "Description"
        ])
        self.financial_transactions_table.setMaximumHeight(150)
        financial_layout.addWidget(self.financial_transactions_table)
        
        financial_group.setContentLayout(financial_layout)
        scroll_layout.addWidget(financial_group)
        
        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(27, 31, 59, 0.3);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 245, 212, 0.5);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 245, 212, 0.7);
            }
        """)
        
        wallet_layout.addWidget(scroll_area)
        
        # Load initial data
        self.update_wallet_display()
        self.update_financial_accounts()
        self.update_solana_status()
        
        self.tab_widget.addTab(wallet_widget, "Digital Wallet")
    
    def initialize_wallet(self):
        """Initialize the digital wallet."""
        try:
            amount = self.init_amount_input.value()
            success = self.wallet_manager.initialize_wallet(Decimal(str(amount)))
            
            if success:
                self.show_trade_notification(f"Wallet initialized with ${amount}")
                self.update_wallet_display()
                self.init_wallet_button.setEnabled(False)
                self.init_amount_input.setEnabled(False)
            else:
                self.show_trade_notification("Failed to initialize wallet")
                
        except Exception as e:
            logger.error(f"Failed to initialize wallet: {e}")
            self.show_trade_notification(f"Error: {e}")
    
    def manual_reinvest(self):
        """Manually trigger profit reinvestment."""
        try:
            status = self.wallet_manager.get_reinvestment_status()
            if status.get('can_reinvest'):
                # Execute reinvestment
                self.wallet_manager.execute_reinvestment(Decimal(str(status['recommended_amount'])))
                self.show_trade_notification(f"Reinvested ${status['recommended_amount']:.2f}")
                self.update_wallet_display()
            else:
                self.show_trade_notification("Cannot reinvest at this time")
                
        except Exception as e:
            logger.error(f"Failed to reinvest: {e}")
            self.show_trade_notification(f"Error: {e}")
    
    def withdraw_profits(self):
        """Withdraw profits from the wallet."""
        try:
            summary = self.wallet_manager.get_wallet_summary()
            available_profit = summary.get('total_profit', 0)
            
            if available_profit > 0:
                # Simple withdrawal dialog
                from PySide6.QtWidgets import QInputDialog
                amount, ok = QInputDialog.getDouble(
                    self, "Withdraw Profits", 
                    f"Available profit: ${available_profit:.2f}\nEnter amount to withdraw:",
                    min=0.01, max=available_profit, decimals=2
                )
                
                if ok and amount > 0:
                    success = self.wallet_manager.withdraw_profit(Decimal(str(amount)))
                    if success:
                        self.show_trade_notification(f"Withdrew ${amount:.2f}")
                        self.update_wallet_display()
                    else:
                        self.show_trade_notification("Withdrawal failed")
            else:
                self.show_trade_notification("No profit available for withdrawal")
                
        except Exception as e:
            logger.error(f"Failed to withdraw: {e}")
            self.show_trade_notification(f"Error: {e}")
    
    def update_wallet_display(self):
        """Update the wallet display with current data."""
        try:
            summary = self.wallet_manager.get_wallet_summary()
            
            if not summary:
                return
            
            # Update summary labels
            self.initial_investment_label.setText(f"Initial Investment: ${summary['initial_investment']:.2f}")
            self.current_value_label.setText(f"Current Value: ${summary['current_value']:.2f}")
            
            # Color code profit
            profit = summary['total_profit']
            profit_percent = summary['profit_percentage']
            
            if profit > 0:
                self.total_profit_label.setText(f"Total Profit: +${profit:.2f}")
                self.total_profit_label.setStyleSheet("font-weight: bold; color: #00FF00;")
                self.profit_percentage_label.setText(f"Profit %: +{profit_percent:.2f}%")
                self.profit_percentage_label.setStyleSheet("font-weight: bold; color: #00FF00;")
            else:
                self.total_profit_label.setText(f"Total Profit: ${profit:.2f}")
                self.total_profit_label.setStyleSheet("font-weight: bold; color: #FF0000;")
                self.profit_percentage_label.setText(f"Profit %: {profit_percent:.2f}%")
                self.profit_percentage_label.setStyleSheet("font-weight: bold; color: #FF0000;")
            
            self.reinvested_label.setText(f"Reinvested: ${summary['reinvested_profit']:.2f}")
            
            # Update balances table
            balances = summary.get('balances', {})
            self.balances_table.setRowCount(len(balances))
            
            for row, (symbol, balance_data) in enumerate(balances.items()):
                self.balances_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.balances_table.setItem(row, 1, QTableWidgetItem(f"{balance_data['balance']:.6f}"))
                self.balances_table.setItem(row, 2, QTableWidgetItem(f"${balance_data['usd_value']:.2f}"))
                self.balances_table.setItem(row, 3, QTableWidgetItem(balance_data['chain']))
            
            # Update transactions table
            transactions = self.wallet_manager.get_transaction_history(20)
            self.transactions_table.setRowCount(len(transactions))
            
            for row, tx in enumerate(transactions):
                import datetime
                time_str = datetime.datetime.fromtimestamp(tx['timestamp']).strftime('%H:%M:%S')
                
                self.transactions_table.setItem(row, 0, QTableWidgetItem(time_str))
                self.transactions_table.setItem(row, 1, QTableWidgetItem(tx['transaction_type'].title()))
                self.transactions_table.setItem(row, 2, QTableWidgetItem(tx['token_symbol']))
                self.transactions_table.setItem(row, 3, QTableWidgetItem(f"{tx['amount']:.6f}"))
                self.transactions_table.setItem(row, 4, QTableWidgetItem(f"${tx['price']:.6f}"))
                self.transactions_table.setItem(row, 5, QTableWidgetItem(f"${tx['usd_value']:.2f}"))
                self.transactions_table.setItem(row, 6, QTableWidgetItem(tx['status'].title()))
            
            # Update reinvestment status
            reinvest_status = self.wallet_manager.get_reinvestment_status()
            
            if reinvest_status.get('can_reinvest'):
                status_text = f"✅ Ready to reinvest!\n"
                status_text += f"Available profit: ${reinvest_status['available_profit']:.2f}\n"
                status_text += f"Recommended amount: ${reinvest_status['recommended_amount']:.2f}\n"
                status_text += f"Profit percentage: {reinvest_status['profit_percentage']:.2f}%"
                self.reinvestment_status_label.setStyleSheet("color: #00FF00; font-weight: bold;")
                self.reinvest_button.setEnabled(True)
            else:
                reason = reinvest_status.get('reason', 'Unknown')
                status_text = f"❌ Cannot reinvest: {reason}\n"
                if 'profit_percentage' in reinvest_status:
                    status_text += f"Current profit: {reinvest_status['profit_percentage']:.2f}%\n"
                if 'next_threshold' in reinvest_status:
                    status_text += f"Next threshold: {reinvest_status['next_threshold']:.1f}%"
                self.reinvestment_status_label.setStyleSheet("color: #FFAA00; font-weight: bold;")
                self.reinvest_button.setEnabled(False)
            
            self.reinvestment_status_label.setText(status_text)
            
            # Enable/disable withdraw button
            self.withdraw_button.setEnabled(profit > 0)
            
        except Exception as e:
            logger.error(f"Failed to update wallet display: {e}")
    
    def update_financial_accounts(self):
        """Update financial accounts display."""
        try:
            # Get financial accounts
            accounts = self.wallet_manager.get_financial_accounts()
            
            # Update primary account combo
            self.primary_account_combo.clear()
            for account in accounts:
                display_text = f"{account['account_name']} ({account['provider']})"
                self.primary_account_combo.addItem(display_text, account['account_id'])
            
            # Set current primary account
            primary_account = self.wallet_manager.get_primary_account()
            if primary_account:
                for i in range(self.primary_account_combo.count()):
                    if self.primary_account_combo.itemData(i) == primary_account['account_id']:
                        self.primary_account_combo.setCurrentIndex(i)
                        break
            
            # Update total balance
            total_balance = self.wallet_manager.get_total_financial_balance()
            self.financial_balance_label.setText(f"Total Balance: ${total_balance:.2f}")
            
            # Update accounts table
            self.financial_accounts_table.setRowCount(len(accounts))
            for row, account in enumerate(accounts):
                self.financial_accounts_table.setItem(row, 0, QTableWidgetItem(account['account_name']))
                self.financial_accounts_table.setItem(row, 1, QTableWidgetItem(account['provider']))
                self.financial_accounts_table.setItem(row, 2, QTableWidgetItem(account['account_type']))
                self.financial_accounts_table.setItem(row, 3, QTableWidgetItem(f"${account['balance']:.2f}"))
                
                status = "Verified" if account['is_verified'] else "Unverified"
                status_item = QTableWidgetItem(status)
                if account['is_verified']:
                    status_item.setForeground(QColor("#00FF00"))
                else:
                    status_item.setForeground(QColor("#FFAA00"))
                self.financial_accounts_table.setItem(row, 4, status_item)
            
            # Update financial transactions table
            transactions = self.wallet_manager.get_financial_transactions(limit=10)
            self.financial_transactions_table.setRowCount(len(transactions))
            for row, transaction in enumerate(transactions):
                # Time
                time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(transaction['created_at']))
                self.financial_transactions_table.setItem(row, 0, QTableWidgetItem(time_str))
                
                # Type
                self.financial_transactions_table.setItem(row, 1, QTableWidgetItem(transaction['transaction_type'].title()))
                
                # Amount
                amount_str = f"${transaction['amount']:.2f} {transaction['currency']}"
                self.financial_transactions_table.setItem(row, 2, QTableWidgetItem(amount_str))
                
                # Account
                self.financial_transactions_table.setItem(row, 3, QTableWidgetItem(transaction['account_id']))
                
                # Status
                status_item = QTableWidgetItem(transaction['status'].title())
                if transaction['status'] == 'completed':
                    status_item.setForeground(QColor("#00FF00"))
                elif transaction['status'] == 'failed':
                    status_item.setForeground(QColor("#FF0000"))
                elif transaction['status'] == 'processing':
                    status_item.setForeground(QColor("#FFAA00"))
                self.financial_transactions_table.setItem(row, 4, status_item)
                
                # Description
                self.financial_transactions_table.setItem(row, 5, QTableWidgetItem(transaction['description']))
            
        except Exception as e:
            logger.error(f"Failed to update financial accounts: {e}")
    
    def change_primary_account(self, account_name):
        """Change the primary financial account."""
        try:
            current_index = self.primary_account_combo.currentIndex()
            if current_index >= 0:
                account_id = self.primary_account_combo.itemData(current_index)
                if account_id:
                    success = self.wallet_manager.set_primary_account(account_id)
                    if success:
                        self.show_trade_notification(f"Primary account changed to {account_name}")
                        self.update_financial_accounts()
                    else:
                        self.show_trade_notification("Failed to change primary account")
        except Exception as e:
            logger.error(f"Failed to change primary account: {e}")
    
    def deposit_from_financial_account(self):
        """Deposit funds from financial account to trading wallet."""
        try:
            amount = self.deposit_amount_input.value()
            if amount <= 0:
                self.show_trade_notification("Please enter a valid deposit amount")
                return
            
            # Get current primary account
            current_index = self.primary_account_combo.currentIndex()
            if current_index < 0:
                self.show_trade_notification("Please select a primary account")
                return
            
            account_id = self.primary_account_combo.itemData(current_index)
            if not account_id:
                self.show_trade_notification("Invalid account selected")
                return
            
            # Perform deposit
            success = self.wallet_manager.deposit_from_financial_account(account_id, Decimal(str(amount)))
            
            if success:
                self.show_trade_notification(f"Successfully deposited ${amount:.2f} to trading wallet")
                self.update_wallet_display()
                self.update_financial_accounts()
                self.deposit_amount_input.setValue(0.0)
            else:
                self.show_trade_notification("Deposit failed - please check account balance")
                
        except Exception as e:
            logger.error(f"Failed to deposit from financial account: {e}")
            self.show_trade_notification(f"Deposit failed: {e}")
    
    def withdraw_to_financial_account(self):
        """Withdraw funds from trading wallet to financial account."""
        try:
            amount = self.withdrawal_amount_input.value()
            if amount <= 0:
                self.show_trade_notification("Please enter a valid withdrawal amount")
                return
            
            # Get current primary account
            current_index = self.primary_account_combo.currentIndex()
            if current_index < 0:
                self.show_trade_notification("Please select a primary account")
                return
            
            account_id = self.primary_account_combo.itemData(current_index)
            if not account_id:
                self.show_trade_notification("Invalid account selected")
                return
            
            # Perform withdrawal
            success = self.wallet_manager.withdraw_to_financial_account(account_id, Decimal(str(amount)))
            
            if success:
                self.show_trade_notification(f"Successfully withdrew ${amount:.2f} from trading wallet")
                self.update_wallet_display()
                self.update_financial_accounts()
                self.withdrawal_amount_input.setValue(0.0)
            else:
                self.show_trade_notification("Withdrawal failed - please check trading wallet balance")
                
        except Exception as e:
            logger.error(f"Failed to withdraw to financial account: {e}")
            self.show_trade_notification(f"Withdrawal failed: {e}")
    
    def update_solana_status(self):
        """Update Solana wallet connection status."""
        try:
            # Check if Solana wallet is connected
            solana_wallet = self.wallet_manager.solana_wallet_manager
            
            if solana_wallet and hasattr(solana_wallet, 'keypair') and solana_wallet.keypair:
                # Solana wallet is connected
                public_key = str(solana_wallet.keypair.public_key)
                self.solana_status_label.setText("Solana Wallet: Connected")
                self.solana_status_label.setStyleSheet("font-weight: bold; color: #00C851;")
                
                self.connect_solana_button.setVisible(False)
                self.disconnect_solana_button.setVisible(True)
                
                self.solana_info_label.setText(
                    f"Wallet Address: {public_key[:8]}...{public_key[-8:]}\n"
                    f"Network: Solana Mainnet\n"
                    f"Status: Connected"
                )
                self.solana_info_label.setStyleSheet("color: #00C851; font-size: 12px;")
                
                self.solana_deposit_button.setEnabled(True)
                self.solana_withdraw_button.setEnabled(True)
                
            else:
                # Solana wallet not connected
                self.solana_status_label.setText("Solana Wallet: Not Connected")
                self.solana_status_label.setStyleSheet("font-weight: bold; color: #FF6B6B;")
                
                self.connect_solana_button.setVisible(True)
                self.disconnect_solana_button.setVisible(False)
                
                self.solana_info_label.setText("No Solana wallet connected")
                self.solana_info_label.setStyleSheet("color: #888888; font-size: 12px;")
                
                self.solana_deposit_button.setEnabled(False)
                self.solana_withdraw_button.setEnabled(False)
                
        except Exception as e:
            logger.error(f"Failed to update Solana status: {e}")
    
    def connect_solana_wallet(self):
        """Connect to Solana wallet."""
        try:
            # Show Solana wallet connection dialog
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QTextEdit
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Connect Solana Wallet")
            dialog.setModal(True)
            dialog.resize(500, 400)
            
            layout = QVBoxLayout(dialog)
            
            # Title
            title_label = QLabel("Connect Your Solana Wallet")
            title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #9945FF; margin-bottom: 10px;")
            layout.addWidget(title_label)
            
            # Private key input
            private_key_label = QLabel("Private Key (Base58):")
            layout.addWidget(private_key_label)
            private_key_input = QTextEdit()
            private_key_input.setMaximumHeight(80)
            private_key_input.setPlaceholderText("Enter your Solana private key in Base58 format")
            layout.addWidget(private_key_input)
            
            # Or generate new wallet
            generate_label = QLabel("Or generate a new wallet:")
            layout.addWidget(generate_label)
            generate_button = QPushButton("Generate New Wallet")
            generate_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #9945FF, stop:1 #14F195);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #7A35CC, stop:1 #0FD180);
                }
            """)
            layout.addWidget(generate_button)
            
            # Info text
            info_label = QLabel(
                "This will securely connect your Solana wallet to enable instant deposits and withdrawals. "
                "Your private key is encrypted and stored securely. Never share your private key with anyone."
            )
            info_label.setWordWrap(True)
            info_label.setStyleSheet("color: #666666; font-size: 11px; margin: 10px 0;")
            layout.addWidget(info_label)
            
            # Buttons
            button_layout = QHBoxLayout()
            
            connect_button = QPushButton("Connect Wallet")
            connect_button.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #9945FF, stop:1 #14F195);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #7A35CC, stop:1 #0FD180);
                }
            """)
            
            cancel_button = QPushButton("Cancel")
            cancel_button.setStyleSheet("""
                QPushButton {
                    background: #6C757D;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background: #5A6268;
                }
            """)
            
            button_layout.addWidget(connect_button)
            button_layout.addWidget(cancel_button)
            layout.addLayout(button_layout)
            
            def on_generate():
                # Generate new Solana wallet
                success = self.wallet_manager.generate_solana_wallet()
                
                if success:
                    QMessageBox.information(dialog, "Wallet Generated", 
                        "New Solana wallet generated successfully! Your private key has been securely stored.")
                    dialog.accept()
                    self.show_trade_notification("Solana wallet connected successfully!")
                    self.update_solana_status()
                else:
                    QMessageBox.warning(dialog, "Generation Failed", "Failed to generate new wallet.")
            
            def on_connect():
                private_key = private_key_input.toPlainText().strip()
                
                if not private_key:
                    QMessageBox.warning(dialog, "Invalid Input", "Please enter a private key or generate a new wallet.")
                    return
                
                # Connect existing wallet
                success = self.wallet_manager.connect_solana_wallet(private_key)
                
                if success:
                    dialog.accept()
                    self.show_trade_notification("Solana wallet connected successfully!")
                    self.update_solana_status()
                else:
                    QMessageBox.warning(dialog, "Connection Failed", "Failed to connect wallet. Please check your private key.")
            
            def on_cancel():
                dialog.reject()
            
            generate_button.clicked.connect(on_generate)
            connect_button.clicked.connect(on_connect)
            cancel_button.clicked.connect(on_cancel)
            
            dialog.exec()
            
        except Exception as e:
            logger.error(f"Failed to connect Solana wallet: {e}")
            self.show_trade_notification(f"Solana wallet connection failed: {e}")
    
    def disconnect_solana_wallet(self):
        """Disconnect Solana wallet."""
        try:
            from PySide6.QtWidgets import QMessageBox
            
            reply = QMessageBox.question(
                self, 
                "Disconnect Solana Wallet", 
                "Are you sure you want to disconnect your Solana wallet?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                success = self.wallet_manager.disconnect_solana_wallet()
                
                if success:
                    self.show_trade_notification("Solana wallet disconnected successfully!")
                    self.update_solana_status()
                else:
                    self.show_trade_notification("Failed to disconnect Solana wallet")
                    
        except Exception as e:
            logger.error(f"Failed to disconnect Solana wallet: {e}")
            self.show_trade_notification(f"Solana wallet disconnection failed: {e}")
    
    def quick_solana_deposit(self):
        """Quick deposit from Solana wallet."""
        try:
            from PySide6.QtWidgets import QInputDialog
            
            amount, ok = QInputDialog.getDouble(
                self, 
                "Solana Deposit", 
                "Enter amount to deposit from Solana wallet:",
                value=100.0,
                min=1.0,
                max=10000.0,
                decimals=2
            )
            
            if ok and amount > 0:
                # Perform deposit from Solana wallet
                success = self.wallet_manager.deposit_from_solana_wallet(Decimal(str(amount)))
                
                if success:
                    self.show_trade_notification(f"Successfully deposited ${amount:.2f} from Solana wallet!")
                    self.update_wallet_display()
                    self.update_solana_status()
                else:
                    self.show_trade_notification("Solana deposit failed - check wallet balance")
                    
        except Exception as e:
            logger.error(f"Failed to perform Solana deposit: {e}")
            self.show_trade_notification(f"Solana deposit failed: {e}")
    
    def quick_solana_withdraw(self):
        """Quick withdraw to Solana wallet."""
        try:
            from PySide6.QtWidgets import QInputDialog
            
            amount, ok = QInputDialog.getDouble(
                self, 
                "Solana Withdrawal", 
                "Enter amount to withdraw to Solana wallet:",
                value=100.0,
                min=1.0,
                max=10000.0,
                decimals=2
            )
            
            if ok and amount > 0:
                # Perform withdrawal to Solana wallet
                success = self.wallet_manager.withdraw_to_solana_wallet(Decimal(str(amount)))
                
                if success:
                    self.show_trade_notification(f"Successfully withdrew ${amount:.2f} to Solana wallet!")
                    self.update_wallet_display()
                    self.update_solana_status()
                else:
                    self.show_trade_notification("Solana withdrawal failed - check trading wallet balance")
                    
        except Exception as e:
            logger.error(f"Failed to perform Solana withdrawal: {e}")
            self.show_trade_notification(f"Solana withdrawal failed: {e}")
    
    def setup_scam_detection_tab(self):
        """Setup the scam detection tab with collapsible sections."""
        scam_widget = QWidget()
        scam_layout = QVBoxLayout(scam_widget)
        
        # Add scroll area for better navigation
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Scam detection header
        scam_header = QLabel("Memecoin Scam Detection")
        scam_header.setStyleSheet("""
            QLabel {
                font-family: 'Montserrat', sans-serif;
                font-size: 18px;
                font-weight: bold;
                color: #FF6B6B;
                padding: 10px;
                background: rgba(255, 107, 107, 0.1);
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        scroll_layout.addWidget(scam_header)
        
        # Token analysis section
        analysis_group = CollapsibleGroupBox("Token Analysis")
        analysis_layout = QVBoxLayout(analysis_group)
        
        # Token input
        input_layout = QHBoxLayout()
        self.scam_token_input = QTextEdit()
        self.scam_token_input.setMaximumHeight(30)
        self.scam_token_input.setPlaceholderText("Enter token symbol (e.g., BONK, WIF, PEPE)")
        
        self.analyze_token_button = QPushButton("Analyze Token")
        self.analyze_token_button.clicked.connect(self.analyze_token_for_scams)
        
        input_layout.addWidget(QLabel("Token Symbol:"))
        input_layout.addWidget(self.scam_token_input)
        input_layout.addWidget(self.analyze_token_button)
        
        analysis_layout.addLayout(input_layout)
        
        # Analysis results
        self.scam_analysis_text = QTextEdit()
        self.scam_analysis_text.setMaximumHeight(200)
        self.scam_analysis_text.setReadOnly(True)
        analysis_layout.addWidget(self.scam_analysis_text)
        
        analysis_group.setContentLayout(analysis_layout)
        scroll_layout.addWidget(analysis_group)
        
        # Risk assessment section
        risk_group = CollapsibleGroupBox("Risk Assessment")
        risk_layout = QGridLayout(risk_group)
        
        # Risk indicators
        self.risk_level_label = QLabel("Risk Level: Unknown")
        self.risk_score_label = QLabel("Risk Score: 0.00")
        self.indicator_count_label = QLabel("Indicators: 0")
        self.high_severity_label = QLabel("High Severity: 0")
        
        # Style risk labels
        self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.risk_score_label.setStyleSheet("font-weight: bold;")
        
        risk_layout.addWidget(self.risk_level_label, 0, 0)
        risk_layout.addWidget(self.risk_score_label, 0, 1)
        risk_layout.addWidget(self.indicator_count_label, 1, 0)
        risk_layout.addWidget(self.high_severity_label, 1, 1)
        
        risk_group.setContentLayout(risk_layout)
        scroll_layout.addWidget(risk_group)
        
        # Scam indicators table
        indicators_group = CollapsibleGroupBox("Scam Indicators")
        indicators_layout = QVBoxLayout(indicators_group)
        
        self.scam_indicators_table = QTableWidget()
        self.scam_indicators_table.setColumnCount(4)
        self.scam_indicators_table.setHorizontalHeaderLabels([
            "Type", "Severity", "Description", "Confidence"
        ])
        self.scam_indicators_table.setMaximumHeight(200)
        indicators_layout.addWidget(self.scam_indicators_table)
        
        indicators_group.setContentLayout(indicators_layout)
        scroll_layout.addWidget(indicators_group)
        
        # Recommendations section
        recommendations_group = CollapsibleGroupBox("Recommendations")
        recommendations_layout = QVBoxLayout(recommendations_group)
        
        self.scam_recommendations_text = QTextEdit()
        self.scam_recommendations_text.setMaximumHeight(150)
        self.scam_recommendations_text.setReadOnly(True)
        recommendations_layout.addWidget(self.scam_recommendations_text)
        
        recommendations_group.setContentLayout(recommendations_layout)
        scroll_layout.addWidget(recommendations_group)
        
        # Batch analysis section
        batch_group = CollapsibleGroupBox("Batch Analysis")
        batch_layout = QVBoxLayout(batch_group)
        
        # Batch input
        batch_input_layout = QHBoxLayout()
        self.batch_tokens_input = QTextEdit()
        self.batch_tokens_input.setMaximumHeight(30)
        self.batch_tokens_input.setPlaceholderText("Enter multiple tokens separated by commas (e.g., BONK, WIF, PEPE)")
        
        self.batch_analyze_button = QPushButton("Analyze All")
        self.batch_analyze_button.clicked.connect(self.batch_analyze_tokens)
        
        batch_input_layout.addWidget(QLabel("Tokens:"))
        batch_input_layout.addWidget(self.batch_tokens_input)
        batch_input_layout.addWidget(self.batch_analyze_button)
        
        batch_layout.addLayout(batch_input_layout)
        
        # Batch results table
        self.batch_results_table = QTableWidget()
        self.batch_results_table.setColumnCount(5)
        self.batch_results_table.setHorizontalHeaderLabels([
            "Token", "Risk Level", "Risk Score", "Indicators", "High Severity"
        ])
        self.batch_results_table.setMaximumHeight(200)
        batch_layout.addWidget(self.batch_results_table)
        
        batch_group.setContentLayout(batch_layout)
        scroll_layout.addWidget(batch_group)
        
        # Educational section
        education_group = CollapsibleGroupBox("Scam Prevention Education")
        education_layout = QVBoxLayout(education_group)
        
        education_text = QTextEdit()
        education_text.setMaximumHeight(150)
        education_text.setReadOnly(True)
        education_text.setPlainText("""
🚨 Common Memecoin Scam Patterns (Based on Webopedia):

1. Coordinated Shilling: Groups flood social media with fake hype
2. MEV Bot Frontrunning: Bots exploit transaction ordering
3. Fake Partnerships: False collaboration claims
4. Social Profile Hacks: Compromised influencer accounts
5. Celebrity Scams: Unauthorized celebrity endorsements
6. Rug Pulls: Developers abandon project after collecting funds

💡 Prevention Tips:
• Do Your Own Research (DYOR)
• Verify team credentials and partnerships
• Check token distribution and liquidity locks
• Be wary of extreme price movements
• Never invest more than you can afford to lose
        """)
        education_layout.addWidget(education_text)
        
        education_group.setContentLayout(education_layout)
        scroll_layout.addWidget(education_group)
        
        # Set up scroll area
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: rgba(27, 31, 59, 0.3);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 245, 212, 0.5);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 245, 212, 0.7);
            }
        """)
        
        scam_layout.addWidget(scroll_area)
        self.tab_widget.addTab(scam_widget, "Scam Detection")
    
    def analyze_token_for_scams(self):
        """Analyze a single token for scams."""
        try:
            symbol = self.scam_token_input.toPlainText().strip().upper()
            if not symbol:
                self.show_trade_notification("Please enter a token symbol")
                return
            
            # Perform analysis
            analysis = self.scam_detector.analyze_token(symbol)
            
            # Update risk assessment
            self.risk_level_label.setText(f"Risk Level: {analysis.overall_risk.upper()}")
            self.risk_score_label.setText(f"Risk Score: {analysis.risk_score:.2f}")
            self.indicator_count_label.setText(f"Indicators: {len(analysis.indicators)}")
            
            high_severity_count = len([i for i in analysis.indicators if i.severity in ['high', 'critical']])
            self.high_severity_label.setText(f"High Severity: {high_severity_count}")
            
            # Color code risk level
            if analysis.overall_risk == 'critical':
                self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FF0000;")
            elif analysis.overall_risk == 'high':
                self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FF6B00;")
            elif analysis.overall_risk == 'medium':
                self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFAA00;")
            elif analysis.overall_risk == 'low':
                self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #00AA00;")
            else:
                self.risk_level_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #00FF00;")
            
            # Update analysis text
            analysis_text = f"Analysis for {symbol}:\n"
            analysis_text += f"Overall Risk: {analysis.overall_risk.upper()}\n"
            analysis_text += f"Risk Score: {analysis.risk_score:.2f}\n"
            analysis_text += f"Data Sources: {', '.join(analysis.data_sources)}\n"
            analysis_text += f"Analysis Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(analysis.analysis_timestamp))}\n\n"
            
            if analysis.indicators:
                analysis_text += "Detected Indicators:\n"
                for indicator in analysis.indicators:
                    analysis_text += f"• {indicator.type}: {indicator.description} (Confidence: {indicator.confidence:.2f})\n"
            else:
                analysis_text += "No scam indicators detected.\n"
            
            self.scam_analysis_text.setPlainText(analysis_text)
            
            # Update indicators table
            self.scam_indicators_table.setRowCount(len(analysis.indicators))
            
            for row, indicator in enumerate(analysis.indicators):
                self.scam_indicators_table.setItem(row, 0, QTableWidgetItem(indicator.type.replace('_', ' ').title()))
                self.scam_indicators_table.setItem(row, 1, QTableWidgetItem(indicator.severity.title()))
                self.scam_indicators_table.setItem(row, 2, QTableWidgetItem(indicator.description))
                self.scam_indicators_table.setItem(row, 3, QTableWidgetItem(f"{indicator.confidence:.2f}"))
                
                # Color code severity
                severity_item = self.scam_indicators_table.item(row, 1)
                if indicator.severity == 'critical':
                    severity_item.setForeground(QColor("#FF0000"))
                elif indicator.severity == 'high':
                    severity_item.setForeground(QColor("#FF6B00"))
                elif indicator.severity == 'medium':
                    severity_item.setForeground(QColor("#FFAA00"))
                else:
                    severity_item.setForeground(QColor("#00AA00"))
            
            # Update recommendations
            recommendations_text = "Recommendations:\n\n"
            for i, rec in enumerate(analysis.recommendations, 1):
                recommendations_text += f"{i}. {rec}\n"
            
            self.scam_recommendations_text.setPlainText(recommendations_text)
            
            # Show notification
            self.show_trade_notification(f"Scam analysis completed for {symbol}: {analysis.overall_risk} risk")
            
        except Exception as e:
            logger.error(f"Failed to analyze token for scams: {e}")
            self.show_trade_notification(f"Analysis failed: {e}")
    
    def batch_analyze_tokens(self):
        """Analyze multiple tokens for scams."""
        try:
            tokens_text = self.batch_tokens_input.toPlainText().strip()
            if not tokens_text:
                self.show_trade_notification("Please enter token symbols")
                return
            
            # Parse tokens
            tokens = [token.strip().upper() for token in tokens_text.split(',') if token.strip()]
            if not tokens:
                self.show_trade_notification("No valid tokens found")
                return
            
            # Perform batch analysis
            results = self.scam_detector.batch_analyze_tokens(tokens)
            
            # Update batch results table
            self.batch_results_table.setRowCount(len(results))
            
            for row, (symbol, analysis) in enumerate(results.items()):
                self.batch_results_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.batch_results_table.setItem(row, 1, QTableWidgetItem(analysis.overall_risk.title()))
                self.batch_results_table.setItem(row, 2, QTableWidgetItem(f"{analysis.risk_score:.2f}"))
                self.batch_results_table.setItem(row, 3, QTableWidgetItem(str(len(analysis.indicators))))
                
                high_severity_count = len([i for i in analysis.indicators if i.severity in ['high', 'critical']])
                self.batch_results_table.setItem(row, 4, QTableWidgetItem(str(high_severity_count)))
                
                # Color code risk level
                risk_item = self.batch_results_table.item(row, 1)
                if analysis.overall_risk == 'critical':
                    risk_item.setForeground(QColor("#FF0000"))
                elif analysis.overall_risk == 'high':
                    risk_item.setForeground(QColor("#FF6B00"))
                elif analysis.overall_risk == 'medium':
                    risk_item.setForeground(QColor("#FFAA00"))
                elif analysis.overall_risk == 'low':
                    risk_item.setForeground(QColor("#00AA00"))
                else:
                    risk_item.setForeground(QColor("#00FF00"))
            
            # Show notification
            self.show_trade_notification(f"Batch analysis completed for {len(tokens)} tokens")
            
        except Exception as e:
            logger.error(f"Failed to batch analyze tokens: {e}")
            self.show_trade_notification(f"Batch analysis failed: {e}")
    
    def execute_buy(self):
        """Execute a buy order."""
        symbol = self.symbol_combo.currentText()
        amount = self.amount_spinbox.value()
        
        # Execute trade through wallet manager
        try:
            # Get current price (simulated)
            import random
            price = Decimal(str(random.uniform(0.000001, 0.1)))
            
            success = self.wallet_manager.execute_trade(
                symbol=symbol,
                amount=Decimal(str(amount)),
                price=price,
                trade_type='buy'
            )
            
            if success:
                self.show_trade_notification(f"Bought {amount} {symbol} at ${price:.6f}")
                self.update_wallet_display()
            else:
                self.show_trade_notification("Buy order failed - insufficient funds")
                
        except Exception as e:
            logger.error(f"Failed to execute buy order: {e}")
            self.show_trade_notification(f"Error: {e}")
        
        # Add to trade history
        self.add_trade_to_history("BUY", symbol, amount, 0.0, "Executed")
        
        # Show notification
        self.show_trade_notification(f"Trade executed: {amount} USD of {symbol} — smooth move!")
        
        logger.info(f"Buy order executed: {amount} USD of {symbol}")
    
    def execute_sell(self):
        """Execute a sell order."""
        symbol = self.symbol_combo.currentText()
        amount = self.amount_spinbox.value()
        
        # Execute trade through wallet manager
        try:
            # Get current price (simulated)
            import random
            price = Decimal(str(random.uniform(0.000001, 0.1)))
            
            success = self.wallet_manager.execute_trade(
                symbol=symbol,
                amount=Decimal(str(amount)),
                price=price,
                trade_type='sell'
            )
            
            if success:
                self.show_trade_notification(f"Sold {amount} {symbol} at ${price:.6f}")
                self.update_wallet_display()
            else:
                self.show_trade_notification("Sell order failed - insufficient tokens")
                
        except Exception as e:
            logger.error(f"Failed to execute sell order: {e}")
            self.show_trade_notification(f"Error: {e}")
        
        # Add to trade history
        self.add_trade_to_history("SELL", symbol, amount, 0.0, "Executed")
        
        logger.info(f"Sell order executed: {amount} USD of {symbol}")
    
    def execute_hold(self):
        """Execute a hold decision."""
        symbol = self.symbol_combo.currentText()
        
        # Add to trade history
        self.add_trade_to_history("HOLD", symbol, 0.0, 0.0, "Decision")
        
        # Show notification
        self.show_trade_notification(f"Hold decision: {symbol} — waiting for better entry!")
        
        logger.info(f"Hold decision executed for {symbol}")
    
    def add_trade_to_history(self, action, symbol, amount, price, status):
        """Add a trade to the history table."""
        current_time = time.strftime('%H:%M:%S')
        
        row_count = self.trade_history_table.rowCount()
        self.trade_history_table.insertRow(row_count)
        
        self.trade_history_table.setItem(row_count, 0, QTableWidgetItem(current_time))
        self.trade_history_table.setItem(row_count, 1, QTableWidgetItem(symbol))
        self.trade_history_table.setItem(row_count, 2, QTableWidgetItem(action))
        self.trade_history_table.setItem(row_count, 3, QTableWidgetItem(f"${amount:.2f}"))
        self.trade_history_table.setItem(row_count, 4, QTableWidgetItem(f"${price:.6f}"))
        self.trade_history_table.setItem(row_count, 5, QTableWidgetItem(status))
        
        # Auto-scroll to bottom
        self.trade_history_table.scrollToBottom()
    
    def show_trade_notification(self, message):
        """Show a trade notification."""
        # Create a simple notification dialog
        msg = QMessageBox()
        msg.setWindowTitle("Trade Notification")
        msg.setText(message)
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background: rgba(27, 31, 59, 0.95);
                color: #FFFFFF;
            }
            QMessageBox QPushButton {
                background: #00F5D4;
                color: #1B1F3B;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
        """)
        msg.exec()
    
    def update_bot_persona(self):
        """Update the bot persona indicator based on market volatility."""
        if self.market_mode == "Live Market":
            self.update_live_bot_persona()
        else:
            self.update_simulation_bot_persona()
    
    def update_simulation_bot_persona(self):
        """Update bot persona with simulated volatility."""
        import random
        
        # Simulate market volatility
        volatility = random.uniform(0, 1)
        
        # Update sprite manager with market state
        self.sprite_manager.update_market_state(volatility)
        
        if volatility > 0.7:
            # High volatility - alert avatar
            sprite = self.sprite_manager.get_sprite("avatar_bot_alert")
            if sprite:
                self.bot_status_indicator.setPixmap(sprite)
            # Start pulse animation
            self.sprite_manager.start_animation("bot_pulse", self.bot_status_indicator)
        elif volatility > 0.4:
            # Medium volatility - happy avatar
            sprite = self.sprite_manager.get_sprite("avatar_bot_happy")
            if sprite:
                self.bot_status_indicator.setPixmap(sprite)
        else:
            # Low volatility - neutral avatar
            sprite = self.sprite_manager.get_sprite("avatar_bot_neutral")
            if sprite:
                self.bot_status_indicator.setPixmap(sprite)
    
    def update_live_bot_persona(self):
        """Update bot persona with live market volatility."""
        if not self.live_market_data:
            return
        
        # Calculate real volatility from live market data
        changes = [abs(data["change"]) for data in self.live_market_data.values()]
        volatility = sum(changes) / len(changes) if changes else 0
        
        # Update sprite manager with market state
        self.sprite_manager.update_market_state(volatility)
        
        if volatility > 0.1:  # >10% average change
            # High volatility - alert avatar
            sprite = self.sprite_manager.get_sprite("avatar_bot_alert")
            if sprite:
                self.bot_status_indicator.setPixmap(sprite)
            # Start pulse animation
            self.sprite_manager.start_animation("bot_pulse", self.bot_status_indicator)
            
            # Update tooltip with live volatility info
            self.bot_status_indicator.setToolTip(f"High Market Volatility Detected!\nAverage Change: {volatility:.2%}\nMode: Live Market")
            
        elif volatility > 0.05:  # >5% average change
            # Medium volatility - happy avatar
            sprite = self.sprite_manager.get_sprite("avatar_bot_happy")
            if sprite:
                self.bot_status_indicator.setPixmap(sprite)
            
            self.bot_status_indicator.setToolTip(f"Moderate Market Activity\nAverage Change: {volatility:.2%}\nMode: Live Market")
            
        else:
            # Low volatility - neutral avatar
            sprite = self.sprite_manager.get_sprite("avatar_bot_neutral")
            if sprite:
                self.bot_status_indicator.setPixmap(sprite)
            
            self.bot_status_indicator.setToolTip(f"Stable Market Conditions\nAverage Change: {volatility:.2%}\nMode: Live Market")
    
    def update_ticker_prices(self):
        """Update ticker prices with market data (simulation or live)."""
        if self.market_mode == "Live Market":
            self.update_live_ticker_prices()
        else:
            self.update_simulation_ticker_prices()
    
    def update_simulation_ticker_prices(self):
        """Update ticker prices with simulated market data."""
        import random
        
        for symbol, label in self.ticker_labels.items():
            # Simulate price movement
            current_price = float(label.text().replace('$', ''))
            change = random.uniform(-0.000001, 0.000001)
            new_price = max(0.000001, current_price + change)
            
            label.setText(f"${new_price:.6f}")
            
            # Update color based on change
            if change > 0:
                label.setStyleSheet("font-family: 'Courier New', monospace; color: #00FF00;")
            else:
                label.setStyleSheet("font-family: 'Courier New', monospace; color: #FF0000;")
    
    def update_live_ticker_prices(self):
        """Update ticker prices with live market data."""
        for symbol, label in self.ticker_labels.items():
            if symbol in self.live_market_data:
                data = self.live_market_data[symbol]
                price = data["price"]
                change = data["change"]
                
                # Format price based on symbol
                if symbol in ["DOGE"]:
                    price_text = f"${price:.4f}"
                elif symbol in ["SHIB", "PEPE", "BONK", "WIF"]:
                    price_text = f"${price:.8f}"
                else:
                    price_text = f"${price:.6f}"
                
                label.setText(price_text)
                
                # Update color based on 24h change
                if change > 0:
                    label.setStyleSheet("font-family: 'Courier New', monospace; color: #00FF00; font-weight: bold;")
                else:
                    label.setStyleSheet("font-family: 'Courier New', monospace; color: #FF0000; font-weight: bold;")
                
                # Add live data indicator
                label.setToolTip(f"Live {symbol} Price: {price_text}\n24h Change: {change:.2%}\nVolume: {data['volume']:,}")
    
    def change_meme_intensity(self, intensity):
        """Change the meme intensity level."""
        if intensity == "Full Send":
            # Add more vibrant colors and effects
            self.setStyleSheet(self.styleSheet() + """
                QPushButton:hover {
                    box-shadow: 0 0 25px rgba(0, 245, 212, 0.8);
                    transform: scale(1.05);
                }
                QGroupBox {
                    border: 3px solid #00F5D4;
                    box-shadow: 0 0 20px rgba(0, 245, 212, 0.3);
                }
            """)
        elif intensity == "Subtle":
            # More muted colors
            self.setStyleSheet(self.styleSheet().replace("#00F5D4", "#4A9B8E"))
        else:
            # Balanced - default theme
            self.setup_styles()
        
        logger.info(f"Meme intensity changed to: {intensity}")
    
    def setup_bottom_panel(self, parent_layout):
        """Setup the bottom panel."""
        bottom_group = QGroupBox("Quick Actions")
        bottom_layout = QHBoxLayout(bottom_group)
        
        # Quick action buttons
        self.sweep_profits_button = QPushButton("Sweep Profits")
        self.sweep_profits_button.clicked.connect(self.sweep_profits)
        
        self.reset_daily_button = QPushButton("Reset Daily Metrics")
        self.reset_daily_button.clicked.connect(self.reset_daily_metrics)
        
        self.export_data_button = QPushButton("Export Data")
        self.export_data_button.clicked.connect(self.export_data)
        
        bottom_layout.addWidget(self.sweep_profits_button)
        bottom_layout.addWidget(self.reset_daily_button)
        bottom_layout.addWidget(self.export_data_button)
        
        # Meme intensity selector
        meme_intensity_label = QLabel("Meme Intensity:")
        meme_intensity_combo = QComboBox()
        meme_intensity_combo.addItems(["Subtle", "Balanced", "Full Send"])
        meme_intensity_combo.setCurrentText("Balanced")
        meme_intensity_combo.currentTextChanged.connect(self.change_meme_intensity)
        
        bottom_layout.addWidget(meme_intensity_label)
        bottom_layout.addWidget(meme_intensity_combo)
        bottom_layout.addStretch()
        
        parent_layout.addWidget(bottom_group)
    
    def setup_styles(self):
        """Setup the NeoMeme Markets theme styles."""
        self.setStyleSheet("""
            /* Main Window - Deep Navy Base */
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #1B1F3B, stop:1 #2A2F5A);
                color: #FFFFFF;
            }
            
            /* Header Title */
            QLabel#title_label {
                font-family: 'Montserrat', sans-serif;
                font-size: 24px;
                font-weight: bold;
                color: #00F5D4;
                background: transparent;
                padding: 10px;
            }
            
            /* Group Boxes - Card Style */
            QGroupBox {
                font-family: 'Inter', sans-serif;
                font-weight: bold;
                font-size: 14px;
                color: #FFFFFF;
                background: rgba(27, 31, 59, 0.8);
                border: 2px solid #00F5D4;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px 0 8px;
                color: #00F5D4;
                font-weight: bold;
            }
            
            /* Buttons - Professional with Glow */
            QPushButton {
                font-family: 'Inter', sans-serif;
                font-size: 14px;
                font-weight: 600;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00F5D4, stop:1 #00C4A3);
                border: none;
                color: #1B1F3B;
                padding: 12px 24px;
                border-radius: 8px;
                min-height: 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00F5D4, stop:1 #00E5C4);
                box-shadow: 0 0 15px rgba(0, 245, 212, 0.5);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #00C4A3, stop:1 #00A393);
            }
            QPushButton:disabled {
                background: #666666;
                color: #999999;
            }
            
            /* Emergency Buttons */
            QPushButton#kill_switch {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF6B6B, stop:1 #E55555);
                color: #FFFFFF;
            }
            QPushButton#kill_switch:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF7B7B, stop:1 #F56565);
                box-shadow: 0 0 15px rgba(255, 107, 107, 0.5);
            }
            
            QPushButton#emergency_stop {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF0000, stop:1 #CC0000);
                color: #FFFFFF;
            }
            QPushButton#emergency_stop:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FF2020, stop:1 #DD0000);
                box-shadow: 0 0 15px rgba(255, 0, 0, 0.5);
            }
            
            /* Tables - Dark Theme */
            QTableWidget {
                font-family: 'Inter', sans-serif;
                background: rgba(27, 31, 59, 0.9);
                gridline-color: #00F5D4;
                border: 1px solid #00F5D4;
                border-radius: 8px;
                color: #FFFFFF;
                selection-background-color: rgba(0, 245, 212, 0.3);
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid rgba(0, 245, 212, 0.2);
            }
            QTableWidget::item:selected {
                background: rgba(0, 245, 212, 0.2);
            }
            QHeaderView::section {
                background: rgba(0, 245, 212, 0.1);
                color: #00F5D4;
                font-weight: bold;
                padding: 8px;
                border: none;
                border-right: 1px solid rgba(0, 245, 212, 0.3);
            }
            
            /* Text Areas */
            QTextEdit {
                font-family: 'Courier New', monospace;
                background: rgba(27, 31, 59, 0.9);
                border: 1px solid #00F5D4;
                border-radius: 8px;
                color: #FFFFFF;
                padding: 8px;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #00F5D4;
                border-radius: 8px;
                background: rgba(27, 31, 59, 0.8);
            }
            QTabBar::tab {
                font-family: 'Inter', sans-serif;
                font-weight: 600;
                background: rgba(27, 31, 59, 0.6);
                color: #FFFFFF;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
            QTabBar::tab:selected {
                background: rgba(0, 245, 212, 0.2);
                color: #00F5D4;
                border-bottom: 2px solid #00F5D4;
            }
            QTabBar::tab:hover {
                background: rgba(0, 245, 212, 0.1);
            }
            
            /* Spin Boxes */
            QSpinBox, QDoubleSpinBox {
                font-family: 'Inter', sans-serif;
                background: rgba(27, 31, 59, 0.9);
                border: 1px solid #00F5D4;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 6px;
                min-width: 80px;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border: 2px solid #00F5D4;
            }
            
            /* Checkboxes */
            QCheckBox {
                font-family: 'Inter', sans-serif;
                color: #FFFFFF;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #00F5D4;
                border-radius: 4px;
                background: rgba(27, 31, 59, 0.9);
            }
            QCheckBox::indicator:checked {
                background: #00F5D4;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTEwIDNMNC41IDguNUwyIDYiIHN0cm9rZT0iIzFCMUYzQiIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+);
            }
            
            /* Progress Bars */
            QProgressBar {
                font-family: 'Inter', sans-serif;
                background: rgba(27, 31, 59, 0.9);
                border: 1px solid #00F5D4;
                border-radius: 6px;
                text-align: center;
                color: #FFFFFF;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00F5D4, stop:1 #FFD93D);
                border-radius: 5px;
            }
            
            /* Status Bar */
            QStatusBar {
                background: rgba(27, 31, 59, 0.9);
                color: #FFFFFF;
                border-top: 1px solid #00F5D4;
            }
            
            /* Labels */
            QLabel {
                font-family: 'Inter', sans-serif;
                color: #FFFFFF;
            }
            
            /* Combo Boxes */
            QComboBox {
                font-family: 'Inter', sans-serif;
                background: rgba(27, 31, 59, 0.9);
                border: 1px solid #00F5D4;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 6px;
                min-width: 100px;
            }
            QComboBox::drop-down {
                border: none;
                background: #00F5D4;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPHBhdGggZD0iTTMgNEw2IDdMOSA0IiBzdHJva2U9IiMxQjFGM0IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+Cjwvc3ZnPg==);
            }
            QComboBox QAbstractItemView {
                background: rgba(27, 31, 59, 0.95);
                border: 1px solid #00F5D4;
                color: #FFFFFF;
                selection-background-color: rgba(0, 245, 212, 0.3);
            }
            
            /* Scrollbars */
            QScrollBar:vertical {
                background: rgba(27, 31, 59, 0.5);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #00F5D4;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #00E5C4;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            
            /* Tooltips */
            QToolTip {
                background: rgba(27, 31, 59, 0.95);
                border: 1px solid #00F5D4;
                border-radius: 6px;
                color: #FFFFFF;
                padding: 8px;
            }
        """)
    
    def update_status(self, status: Dict[str, Any]):
        """Update the status display."""
        try:
            # Update portfolio metrics
            self.portfolio_value_label.setText(f"${status['portfolio_value']:,.2f}")
            self.total_pnl_label.setText(f"${status['total_pnl']:,.2f}")
            self.daily_pnl_label.setText(f"${status['daily_pnl']:,.2f}")
            self.max_drawdown_label.setText(f"{status['max_drawdown']:.2f}%")
            
            # Update risk level
            risk_level = status['risk_level']
            self.risk_level_status_label.setText(risk_level.title())
            
            # Color code risk level
            if risk_level == "critical":
                self.risk_level_status_label.setStyleSheet("color: #ff0000; font-weight: bold;")
            elif risk_level == "high":
                self.risk_level_status_label.setStyleSheet("color: #ff8800; font-weight: bold;")
            elif risk_level == "medium":
                self.risk_level_status_label.setStyleSheet("color: #ffaa00; font-weight: bold;")
            else:
                self.risk_level_status_label.setStyleSheet("color: #00aa00; font-weight: bold;")
            
            # Update status bar
            self.market_mode_label.setText(f"Mode: {self.market_mode}")
            self.risk_level_label.setText(f"Risk: {risk_level.title()}")
            self.kill_switch_label.setText(f"Kill Switch: {'Active' if status['kill_switch_active'] else 'Inactive'}")
            self.position_count_label.setText(f"Positions: {status['position_count']}")
            
            # Update bot status text
            status_text = f"""
Bot Status Update - {time.strftime('%Y-%m-%d %H:%M:%S')}
Portfolio Value: ${status['portfolio_value']:,.2f}
Total P&L: ${status['total_pnl']:,.2f}
Daily P&L: ${status['daily_pnl']:,.2f}
Max Drawdown: {status['max_drawdown']:.2f}%
Risk Level: {risk_level.title()}
Kill Switch: {'Active' if status['kill_switch_active'] else 'Inactive'}
Active Positions: {status['position_count']}
            """.strip()
            
            self.bot_status_text.setText(status_text)
            
        except Exception as e:
            logger.error("Failed to update status", error=str(e))
    
    def activate_kill_switch(self):
        """Activate the kill switch."""
        try:
            reply = QMessageBox.question(
                self, "Confirm Kill Switch",
                "Are you sure you want to activate the kill switch?\n\n"
                "This will immediately stop all trading operations.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Create kill switch file
                kill_switch_file = SAFETY_CONFIG.KILL_SWITCH_FILE_PATH
                with open(kill_switch_file, 'w') as f:
                    f.write(f"Kill switch activated at {time.time()}")
                
                QMessageBox.information(
                    self, "Kill Switch Activated",
                    "Kill switch has been activated.\n"
                    "All trading operations will stop within 10 seconds."
                )
                
                self.add_log("Kill switch activated by user")
                
        except Exception as e:
            logger.error("Failed to activate kill switch", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to activate kill switch: {e}")
    
    def emergency_stop(self):
        """Emergency stop all operations."""
        try:
            reply = QMessageBox.question(
                self, "Confirm Emergency Stop",
                "Are you sure you want to perform an emergency stop?\n\n"
                "This will immediately close all positions and stop the bot.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Close all positions
                for symbol in list(self.risk_manager.positions.keys()):
                    self.risk_manager.close_position(symbol, 0.0, "emergency_stop")
                
                # Activate kill switch
                self.activate_kill_switch()
                
                QMessageBox.information(
                    self, "Emergency Stop Complete",
                    "Emergency stop completed.\n"
                    "All positions have been closed and the bot has been stopped."
                )
                
                self.add_log("Emergency stop performed by user")
                
        except Exception as e:
            logger.error("Failed to perform emergency stop", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to perform emergency stop: {e}")
    
    def pause_bot(self):
        """Pause the bot."""
        self.pause_button.setEnabled(False)
        self.resume_button.setEnabled(True)
        self.add_log("Bot paused by user")
    
    def resume_bot(self):
        """Resume the bot."""
        self.pause_button.setEnabled(True)
        self.resume_button.setEnabled(False)
        self.add_log("Bot resumed by user")
    
    def close_selected_position(self):
        """Close the selected position."""
        try:
            current_row = self.positions_table.currentRow()
            if current_row >= 0:
                symbol_item = self.positions_table.item(current_row, 0)
                if symbol_item:
                    symbol = symbol_item.text()
                    
                    reply = QMessageBox.question(
                        self, "Confirm Position Close",
                        f"Are you sure you want to close position {symbol}?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Get current price (simplified)
                        current_price = 0.0  # TODO: Get actual current price
                        self.risk_manager.close_position(symbol, current_price, "manual_close")
                        self.refresh_positions()
                        self.add_log(f"Position {symbol} closed manually")
                        
        except Exception as e:
            logger.error("Failed to close selected position", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to close position: {e}")
    
    def refresh_positions(self):
        """Refresh the positions table."""
        try:
            self.positions_table.setRowCount(len(self.risk_manager.positions))
            
            for row, (symbol, position) in enumerate(self.risk_manager.positions.items()):
                self.positions_table.setItem(row, 0, QTableWidgetItem(symbol))
                self.positions_table.setItem(row, 1, QTableWidgetItem(position.side))
                self.positions_table.setItem(row, 2, QTableWidgetItem(f"{position.amount:.6f}"))
                self.positions_table.setItem(row, 3, QTableWidgetItem(f"{position.entry_price:.6f}"))
                self.positions_table.setItem(row, 4, QTableWidgetItem(f"{position.current_price or 0.0:.6f}"))
                self.positions_table.setItem(row, 5, QTableWidgetItem(f"{position.unrealized_pnl or 0.0:.2f}"))
                self.positions_table.setItem(row, 6, QTableWidgetItem(position.status.value))
                self.positions_table.setItem(row, 7, QTableWidgetItem(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(position.created_at))))
                
        except Exception as e:
            logger.error("Failed to refresh positions", error=str(e))
    
    def apply_risk_settings(self):
        """Apply the risk settings."""
        try:
            # Update risk manager settings
            self.risk_manager.daily_max_loss_percent = self.daily_max_loss_spinbox.value()
            self.risk_manager.per_trade_pct = self.per_trade_spinbox.value()
            self.risk_manager.max_concurrent_positions = self.max_positions_spinbox.value()
            self.risk_manager.profit_target_pct = self.profit_target_spinbox.value()
            self.risk_manager.hard_stop_pct = self.hard_stop_spinbox.value()
            
            QMessageBox.information(
                self, "Settings Applied",
                "Risk settings have been applied successfully."
            )
            
            self.add_log("Risk settings applied by user")
            
        except Exception as e:
            logger.error("Failed to apply risk settings", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to apply risk settings: {e}")
    
    def reset_risk_settings(self):
        """Reset risk settings to defaults."""
        try:
            self.daily_max_loss_spinbox.setValue(TRADING_CONFIG.DAILY_MAX_LOSS_PERCENT)
            self.per_trade_spinbox.setValue(TRADING_CONFIG.PER_TRADE_PCT)
            self.max_positions_spinbox.setValue(TRADING_CONFIG.MAX_CONCURRENT_POSITIONS)
            self.profit_target_spinbox.setValue(TRADING_CONFIG.PROFIT_TARGET_PCT)
            self.hard_stop_spinbox.setValue(TRADING_CONFIG.HARD_STOP_PCT)
            
            QMessageBox.information(
                self, "Settings Reset",
                "Risk settings have been reset to defaults."
            )
            
            self.add_log("Risk settings reset to defaults by user")
            
        except Exception as e:
            logger.error("Failed to reset risk settings", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to reset risk settings: {e}")
    
    def clear_logs(self):
        """Clear the logs display."""
        self.logs_text.clear()
        self.add_log("Logs cleared by user")
    
    def sweep_profits(self):
        """Sweep profits to cold storage."""
        try:
            if self.risk_manager.should_sweep_profits():
                QMessageBox.information(
                    self, "Profit Sweep",
                    "Profits will be swept to cold storage.\n"
                    "This feature is not yet implemented."
                )
                self.add_log("Profit sweep requested by user")
            else:
                QMessageBox.information(
                    self, "Profit Sweep",
                    "Profit sweep threshold not reached.\n"
                    f"Current threshold: ${TRADING_CONFIG.PROFIT_SWEEP_THRESHOLD:,.2f}"
                )
                
        except Exception as e:
            logger.error("Failed to sweep profits", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to sweep profits: {e}")
    
    def reset_daily_metrics(self):
        """Reset daily metrics."""
        try:
            self.risk_manager.reset_daily_metrics()
            QMessageBox.information(
                self, "Daily Metrics Reset",
                "Daily metrics have been reset successfully."
            )
            self.add_log("Daily metrics reset by user")
            
        except Exception as e:
            logger.error("Failed to reset daily metrics", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to reset daily metrics: {e}")
    
    def export_data(self):
        """Export trading data."""
        try:
            QMessageBox.information(
                self, "Export Data",
                "Data export feature is not yet implemented."
            )
            self.add_log("Data export requested by user")
            
        except Exception as e:
            logger.error("Failed to export data", error=str(e))
            QMessageBox.critical(self, "Error", f"Failed to export data: {e}")
    
    def add_log(self, message: str):
        """Add a message to the logs."""
        try:
            timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
            log_message = f"[{timestamp}] {message}"
            
            self.logs_text.append(log_message)
            
            if self.auto_scroll_checkbox.isChecked():
                self.logs_text.ensureCursorVisible()
                
        except Exception as e:
            logger.error("Failed to add log message", error=str(e))
    
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Stop status thread
            self.status_thread.stop()
            self.status_thread.wait()
            
            # Confirm exit
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Are you sure you want to exit?\n\n"
                "The bot will continue running in the background.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
                
        except Exception as e:
            logger.error("Failed to handle close event", error=str(e))
            event.accept()


def create_gui():
    """Create and show the main GUI window."""
    app = QApplication(sys.argv)
    app.setApplicationName("Meme-Coin Trading Bot")
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    return app, window


if __name__ == "__main__":
    app, window = create_gui()
    sys.exit(app.exec())

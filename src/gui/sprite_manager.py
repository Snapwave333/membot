"""
Sprite Pack Manager for NeoMeme Markets GUI.

This module handles the comprehensive sprite pack system with:
- Visual hierarchy and component categories
- Animation metadata and triggers
- Semantic tags for accessibility
- Asset management with versioning and fallback logic
"""

import json
import os
import time
from typing import Dict, List, Any, Optional
from PySide6.QtCore import QObject, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor
from PySide6.QtWidgets import QWidget, QLabel


class SpritePackManager(QObject):
    """
    Manages the NeoMeme Markets sprite pack system.
    
    Features:
    - Dynamic sprite loading and caching
    - Animation triggers and sequences
    - State variants (hover, pressed, disabled)
    - Accessibility support
    - Fallback logic for missing assets
    """
    
    # Signals for animation events
    animation_started = Signal(str)  # animation_id
    animation_completed = Signal(str)  # animation_id
    sprite_loaded = Signal(str, str)  # sprite_id, file_path
    
    def __init__(self, sprite_pack_path: str = "assets/sprites"):
        super().__init__()
        self.sprite_pack_path = sprite_pack_path
        self.sprite_cache = {}
        self.animations = {}
        self.current_theme = "Classic"
        self.meme_intensity = "Balanced"
        
        # Load sprite pack definition
        self.sprite_pack = self.load_sprite_pack()
        
        # Setup animation timers
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animations)
        self.animation_timer.start(16)  # 60 FPS
        
        # Market state for triggers
        self.market_volatility = 0.0
        self.sentiment_change = False
        
    def load_sprite_pack(self) -> Dict[str, Any]:
        """Load the sprite pack definition from JSON."""
        sprite_pack_file = os.path.join(self.sprite_pack_path, "NeoMemeMarkets.svp")
        
        if os.path.exists(sprite_pack_file):
            try:
                with open(sprite_pack_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to load sprite pack: {e}")
        
        # Return default sprite pack if file doesn't exist
        return self.get_default_sprite_pack()
    
    def get_default_sprite_pack(self) -> Dict[str, Any]:
        """Get the default sprite pack definition."""
        return {
            "spritePackName": "NeoMemeMarkets",
            "version": "1.0.3",
            "author": "NeoMeme Dev Team",
            "theme": "Professional with vibrant meme-inspired accents",
            "resolution": "HD",
            "scaling": {
                "default": "1x",
                "supported": ["1x", "2x", "4x"]
            },
            "fallback": {
                "missingSprite": "placeholder.png",
                "errorSprite": "error_icon.png"
            },
            "categories": {
                "icons": ["buy", "sell", "hold", "sentiment", "themeToggle"],
                "avatars": ["bot_neutral", "bot_happy", "bot_alert"],
                "backgrounds": ["main", "card_trade", "popup", "modal"],
                "buttons": ["primary", "secondary", "toggle", "close"],
                "effects": ["glow", "pulse", "flash", "fade"],
                "overlays": ["tooltip", "notification", "status"]
            },
            "sprites": [
                {
                    "id": "logo_main",
                    "description": "Main logo for NeoMeme Markets",
                    "file": "logo_main.png",
                    "dimensions": {"width": 256, "height": 256},
                    "anchor": "center",
                    "tags": ["branding", "header"]
                },
                {
                    "id": "icon_buy",
                    "description": "Buy button icon - glowing teal arrow",
                    "file": "icon_buy.png",
                    "dimensions": {"width": 64, "height": 64},
                    "anchor": "center",
                    "stateVariants": ["default", "hover", "pressed"],
                    "tags": ["action", "trade"]
                },
                {
                    "id": "icon_sell",
                    "description": "Sell button icon - glowing coral arrow",
                    "file": "icon_sell.png",
                    "dimensions": {"width": 64, "height": 64},
                    "anchor": "center",
                    "stateVariants": ["default", "hover", "pressed"],
                    "tags": ["action", "trade"]
                },
                {
                    "id": "icon_hold",
                    "description": "Hold button icon - golden lock",
                    "file": "icon_hold.png",
                    "dimensions": {"width": 64, "height": 64},
                    "anchor": "center",
                    "stateVariants": ["default", "hover", "pressed"],
                    "tags": ["action", "trade"]
                },
                {
                    "id": "avatar_bot_neutral",
                    "description": "Bot avatar - neutral expression",
                    "file": "avatar_bot_neutral.png",
                    "dimensions": {"width": 128, "height": 128},
                    "anchor": "bottom",
                    "tags": ["avatar", "status"]
                },
                {
                    "id": "avatar_bot_happy",
                    "description": "Bot avatar - happy expression",
                    "file": "avatar_bot_happy.png",
                    "dimensions": {"width": 128, "height": 128},
                    "anchor": "bottom",
                    "tags": ["avatar", "status"]
                },
                {
                    "id": "avatar_bot_alert",
                    "description": "Bot avatar - alert expression",
                    "file": "avatar_bot_alert.png",
                    "dimensions": {"width": 128, "height": 128},
                    "anchor": "bottom",
                    "tags": ["avatar", "status"]
                },
                {
                    "id": "background_main",
                    "description": "Main dashboard background - gradient with geometric overlays",
                    "file": "background_main.jpg",
                    "dimensions": {"width": 1920, "height": 1080},
                    "anchor": "top-left",
                    "tags": ["background", "dashboard"]
                },
                {
                    "id": "card_trade",
                    "description": "Trade card background",
                    "file": "card_trade.png",
                    "dimensions": {"width": 400, "height": 200},
                    "anchor": "top-left",
                    "tags": ["component", "card"]
                },
                {
                    "id": "icon_sentiment_up",
                    "description": "Sentiment indicator - positive",
                    "file": "icon_sentiment_up.png",
                    "dimensions": {"width": 48, "height": 48},
                    "anchor": "center",
                    "tags": ["sentiment", "indicator"]
                },
                {
                    "id": "icon_sentiment_down",
                    "description": "Sentiment indicator - negative",
                    "file": "icon_sentiment_down.png",
                    "dimensions": {"width": 48, "height": 48},
                    "anchor": "center",
                    "tags": ["sentiment", "indicator"]
                },
                {
                    "id": "icon_sentiment_neutral",
                    "description": "Sentiment indicator - neutral",
                    "file": "icon_sentiment_neutral.png",
                    "dimensions": {"width": 48, "height": 48},
                    "anchor": "center",
                    "tags": ["sentiment", "indicator"]
                },
                {
                    "id": "notification_popup",
                    "description": "Toast-style notification background",
                    "file": "notification_popup.png",
                    "dimensions": {"width": 300, "height": 100},
                    "anchor": "top-right",
                    "tags": ["overlay", "notification"]
                },
                {
                    "id": "button_theme_toggle",
                    "description": "Theme toggle button",
                    "file": "button_theme_toggle.png",
                    "dimensions": {"width": 64, "height": 64},
                    "anchor": "center",
                    "tags": ["button", "settings"]
                }
            ],
            "animations": [
                {
                    "id": "bot_pulse",
                    "description": "Bot avatar glow pulse",
                    "targetSprite": "avatar_bot_neutral",
                    "type": "pulse",
                    "duration": 1000,
                    "repeat": True,
                    "easing": "ease-in-out",
                    "trigger": "marketVolatility > 0.7"
                },
                {
                    "id": "sentiment_flash",
                    "description": "Flash effect on sentiment change",
                    "targetSprite": "icon_sentiment_up",
                    "type": "flash",
                    "duration": 500,
                    "repeat": False,
                    "easing": "linear",
                    "trigger": "sentimentChange"
                },
                {
                    "id": "trade_card_fadein",
                    "description": "Fade-in animation for trade cards",
                    "targetSprite": "card_trade",
                    "type": "fade",
                    "duration": 600,
                    "repeat": False,
                    "easing": "ease-out",
                    "trigger": "cardLoad"
                }
            ],
            "accessibility": {
                "altText": {
                    "logo_main": "NeoMeme Markets logo",
                    "icon_buy": "Buy icon",
                    "icon_sell": "Sell icon",
                    "icon_hold": "Hold icon",
                    "avatar_bot_neutral": "Bot avatar with neutral expression",
                    "background_main": "Dashboard background with gradient and geometric shapes"
                },
                "highContrastSupport": True,
                "screenReaderHints": True
            }
        }
    
    def get_sprite(self, sprite_id: str, state: str = "default") -> Optional[QPixmap]:
        """Get a sprite by ID with optional state variant."""
        cache_key = f"{sprite_id}_{state}"
        
        if cache_key in self.sprite_cache:
            return self.sprite_cache[cache_key]
        
        # Find sprite definition
        sprite_def = None
        for sprite in self.sprite_pack["sprites"]:
            if sprite["id"] == sprite_id:
                sprite_def = sprite
                break
        
        if not sprite_def:
            return self.get_fallback_sprite()
        
        # Try to load the sprite file
        file_path = os.path.join(self.sprite_pack_path, sprite_def["file"])
        
        if os.path.exists(file_path):
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                self.sprite_cache[cache_key] = pixmap
                self.sprite_loaded.emit(sprite_id, file_path)
                return pixmap
        
        # Return fallback sprite
        return self.get_fallback_sprite()
    
    def get_fallback_sprite(self) -> QPixmap:
        """Get a fallback sprite when the requested sprite is missing."""
        # Create a simple colored rectangle as fallback
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor(100, 100, 100, 128))  # Semi-transparent gray
        
        painter = QPainter(pixmap)
        painter.setPen(QColor(200, 200, 200))
        painter.drawText(pixmap.rect(), "?", painter.fontMetrics().boundingRect("?"))
        painter.end()
        
        return pixmap
    
    def get_icon(self, sprite_id: str, state: str = "default") -> QIcon:
        """Get a QIcon from a sprite."""
        pixmap = self.get_sprite(sprite_id, state)
        return QIcon(pixmap)
    
    def create_sprite_label(self, sprite_id: str, state: str = "default") -> QLabel:
        """Create a QLabel with a sprite."""
        label = QLabel()
        pixmap = self.get_sprite(sprite_id, state)
        label.setPixmap(pixmap)
        
        # Set accessibility properties
        sprite_def = self.get_sprite_definition(sprite_id)
        if sprite_def and "accessibility" in self.sprite_pack:
            alt_text = self.sprite_pack["accessibility"].get("altText", {}).get(sprite_id, "")
            if alt_text:
                label.setToolTip(alt_text)
        
        return label
    
    def get_sprite_definition(self, sprite_id: str) -> Optional[Dict[str, Any]]:
        """Get the definition of a sprite by ID."""
        for sprite in self.sprite_pack["sprites"]:
            if sprite["id"] == sprite_id:
                return sprite
        return None
    
    def start_animation(self, animation_id: str, target_widget: QWidget = None):
        """Start an animation by ID."""
        animation_def = None
        for animation in self.sprite_pack["animations"]:
            if animation["id"] == animation_id:
                animation_def = animation
                break
        
        if not animation_def:
            return
        
        # Check if animation should be triggered
        if not self.should_trigger_animation(animation_def):
            return
        
        # Create animation object
        animation_obj = {
            "definition": animation_def,
            "target": target_widget,
            "start_time": time.time(),
            "progress": 0.0,
            "active": True
        }
        
        self.animations[animation_id] = animation_obj
        self.animation_started.emit(animation_id)
    
    def should_trigger_animation(self, animation_def: Dict[str, Any]) -> bool:
        """Check if an animation should be triggered based on its trigger condition."""
        trigger = animation_def.get("trigger", "")
        
        if trigger == "marketVolatility > 0.7":
            return self.market_volatility > 0.7
        elif trigger == "sentimentChange":
            return self.sentiment_change
        elif trigger == "cardLoad":
            return True  # Always trigger on card load
        
        return True
    
    def update_animations(self):
        """Update all active animations."""
        current_time = time.time()
        
        for animation_id, animation_obj in list(self.animations.items()):
            if not animation_obj["active"]:
                continue
            
            definition = animation_obj["definition"]
            elapsed = current_time - animation_obj["start_time"]
            duration = definition["duration"] / 1000.0  # Convert to seconds
            
            if elapsed >= duration:
                # Animation completed
                animation_obj["active"] = False
                self.animation_completed.emit(animation_id)
                
                # Restart if repeat is enabled
                if definition.get("repeat", False):
                    self.start_animation(animation_id, animation_obj["target"])
            else:
                # Update animation progress
                progress = elapsed / duration
                animation_obj["progress"] = progress
                
                # Apply animation to target widget
                self.apply_animation(animation_obj)
    
    def apply_animation(self, animation_obj: Dict[str, Any]):
        """Apply animation effects to the target widget."""
        definition = animation_obj["definition"]
        target = animation_obj["target"]
        progress = animation_obj["progress"]
        
        if not target:
            return
        
        animation_type = definition["type"]
        
        if animation_type == "pulse":
            # Pulse effect - scale up and down
            scale = 1.0 + 0.2 * abs(progress - 0.5) * 2
            target.setStyleSheet(f"transform: scale({scale});")
        
        elif animation_type == "flash":
            # Flash effect - opacity change
            opacity = 1.0 - abs(progress - 0.5) * 2
            target.setStyleSheet(f"opacity: {opacity};")
        
        elif animation_type == "fade":
            # Fade effect - opacity transition
            opacity = progress
            target.setStyleSheet(f"opacity: {opacity};")
    
    def update_market_state(self, volatility: float, sentiment_changed: bool = False):
        """Update market state for animation triggers."""
        self.market_volatility = volatility
        self.sentiment_change = sentiment_changed
        
        # Trigger animations based on new state
        for animation in self.sprite_pack["animations"]:
            if self.should_trigger_animation(animation):
                self.start_animation(animation["id"])
    
    def set_theme(self, theme: str):
        """Set the current theme."""
        self.current_theme = theme
    
    def set_meme_intensity(self, intensity: str):
        """Set the meme intensity level."""
        self.meme_intensity = intensity
    
    def get_sprites_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all sprites in a specific category."""
        sprites = []
        for sprite in self.sprite_pack["sprites"]:
            if category in sprite.get("tags", []):
                sprites.append(sprite)
        return sprites
    
    def get_sprites_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get all sprites with a specific tag."""
        sprites = []
        for sprite in self.sprite_pack["sprites"]:
            if tag in sprite.get("tags", []):
                sprites.append(sprite)
        return sprites
    
    def clear_cache(self):
        """Clear the sprite cache."""
        self.sprite_cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the sprite cache."""
        return {
            "cached_sprites": len(self.sprite_cache),
            "cache_keys": list(self.sprite_cache.keys()),
            "active_animations": len([a for a in self.animations.values() if a["active"]]),
            "sprite_pack_version": self.sprite_pack.get("version", "unknown")
        }


# Global sprite manager instance
_sprite_manager = None

def get_sprite_manager() -> SpritePackManager:
    """Get the global sprite manager instance."""
    global _sprite_manager
    if _sprite_manager is None:
        _sprite_manager = SpritePackManager()
    return _sprite_manager

"""
Sprite Generator for NeoMeme Markets GUI.

This module generates placeholder sprites for the trading bot GUI
when actual sprite files are not available.
"""

import os
import sys
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QPen, QBrush, QPolygon
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication


class SpriteGenerator:
    """Generates placeholder sprites for the GUI."""
    
    def __init__(self):
        self.colors = {
            'teal': QColor(0, 245, 212),
            'coral': QColor(255, 107, 107),
            'gold': QColor(255, 217, 61),
            'navy': QColor(27, 31, 59),
            'white': QColor(255, 255, 255),
            'green': QColor(0, 255, 0),
            'red': QColor(255, 0, 0),
            'yellow': QColor(255, 255, 0)
        }
    
    def generate_buy_icon(self, size=64):
        """Generate a buy icon (upward arrow)."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QBrush(self.colors['teal']))
        painter.setPen(QPen(self.colors['navy'], 2))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw upward arrow
        painter.setPen(QPen(self.colors['navy'], 3))
        center_x, center_y = size // 2, size // 2
        arrow_size = size // 4
        
        # Arrow points
        points = [
            QPoint(center_x, center_y - arrow_size),  # Top
            QPoint(center_x - arrow_size//2, center_y),  # Bottom left
            QPoint(center_x - arrow_size//4, center_y),  # Bottom left inner
            QPoint(center_x - arrow_size//4, center_y + arrow_size//2),  # Bottom left outer
            QPoint(center_x + arrow_size//4, center_y + arrow_size//2),  # Bottom right outer
            QPoint(center_x + arrow_size//4, center_y),  # Bottom right inner
            QPoint(center_x + arrow_size//2, center_y),  # Bottom right
        ]
        
        painter.drawPolygon(QPolygon(points))
        painter.end()
        
        return pixmap
    
    def generate_sell_icon(self, size=64):
        """Generate a sell icon (downward arrow)."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QBrush(self.colors['coral']))
        painter.setPen(QPen(self.colors['white'], 2))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw downward arrow
        painter.setPen(QPen(self.colors['white'], 3))
        center_x, center_y = size // 2, size // 2
        arrow_size = size // 4
        
        # Arrow points
        points = [
            QPoint(center_x, center_y + arrow_size),  # Bottom
            QPoint(center_x - arrow_size//2, center_y),  # Top left
            QPoint(center_x - arrow_size//4, center_y),  # Top left inner
            QPoint(center_x - arrow_size//4, center_y - arrow_size//2),  # Top left outer
            QPoint(center_x + arrow_size//4, center_y - arrow_size//2),  # Top right outer
            QPoint(center_x + arrow_size//4, center_y),  # Top right inner
            QPoint(center_x + arrow_size//2, center_y),  # Top right
        ]
        
        painter.drawPolygon(QPolygon(points))
        painter.end()
        
        return pixmap
    
    def generate_hold_icon(self, size=64):
        """Generate a hold icon (lock)."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw background circle
        painter.setBrush(QBrush(self.colors['gold']))
        painter.setPen(QPen(self.colors['navy'], 2))
        painter.drawEllipse(4, 4, size-8, size-8)
        
        # Draw lock
        painter.setPen(QPen(self.colors['navy'], 3))
        center_x, center_y = size // 2, size // 2
        lock_width = size // 3
        lock_height = size // 4
        
        # Lock body
        painter.drawRect(center_x - lock_width//2, center_y, lock_width, lock_height)
        
        # Lock shackle
        shackle_width = lock_width + 8
        shackle_height = lock_height // 2
        painter.drawArc(center_x - shackle_width//2, center_y - shackle_height//2, 
                       shackle_width, shackle_height, 0, 180 * 16)
        
        painter.end()
        
        return pixmap
    
    def generate_bot_avatar(self, expression='neutral', size=128):
        """Generate a bot avatar with different expressions."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw head (circle)
        painter.setBrush(QBrush(self.colors['teal']))
        painter.setPen(QPen(self.colors['navy'], 3))
        painter.drawEllipse(8, 8, size-16, size-16)
        
        # Draw eyes
        eye_size = size // 8
        left_eye_x = size // 3
        right_eye_x = 2 * size // 3
        eye_y = size // 3
        
        painter.setBrush(QBrush(self.colors['white']))
        painter.setPen(QPen(self.colors['navy'], 2))
        painter.drawEllipse(left_eye_x - eye_size//2, eye_y - eye_size//2, eye_size, eye_size)
        painter.drawEllipse(right_eye_x - eye_size//2, eye_y - eye_size//2, eye_size, eye_size)
        
        # Draw pupils
        pupil_size = eye_size // 2
        painter.setBrush(QBrush(self.colors['navy']))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(left_eye_x - pupil_size//2, eye_y - pupil_size//2, pupil_size, pupil_size)
        painter.drawEllipse(right_eye_x - pupil_size//2, eye_y - pupil_size//2, pupil_size, pupil_size)
        
        # Draw mouth based on expression
        mouth_y = 2 * size // 3
        mouth_width = size // 4
        
        if expression == 'happy':
            # Smile
            painter.setPen(QPen(self.colors['navy'], 3))
            painter.drawArc(left_eye_x - mouth_width//2, mouth_y - mouth_width//4, 
                          mouth_width, mouth_width//2, 0, 180 * 16)
        elif expression == 'alert':
            # Frown
            painter.setPen(QPen(self.colors['red'], 3))
            painter.drawArc(left_eye_x - mouth_width//2, mouth_y, 
                          mouth_width, mouth_width//2, 180 * 16, 180 * 16)
        else:  # neutral
            # Straight line
            painter.setPen(QPen(self.colors['navy'], 3))
            painter.drawLine(left_eye_x - mouth_width//2, mouth_y, 
                           left_eye_x + mouth_width//2, mouth_y)
        
        painter.end()
        
        return pixmap
    
    def generate_sentiment_icon(self, sentiment='neutral', size=48):
        """Generate sentiment indicator icons."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if sentiment == 'up':
            # Upward trend arrow
            painter.setBrush(QBrush(self.colors['green']))
            painter.setPen(QPen(self.colors['white'], 2))
            painter.drawEllipse(2, 2, size-4, size-4)
            
            # Arrow
            painter.setPen(QPen(self.colors['white'], 2))
            center_x, center_y = size // 2, size // 2
            arrow_size = size // 3
            
            points = [
                QPoint(center_x, center_y - arrow_size//2),
                QPoint(center_x - arrow_size//3, center_y + arrow_size//3),
                QPoint(center_x + arrow_size//3, center_y + arrow_size//3)
            ]
            painter.drawPolygon(QPolygon(points))
            
        elif sentiment == 'down':
            # Downward trend arrow
            painter.setBrush(QBrush(self.colors['red']))
            painter.setPen(QPen(self.colors['white'], 2))
            painter.drawEllipse(2, 2, size-4, size-4)
            
            # Arrow
            painter.setPen(QPen(self.colors['white'], 2))
            center_x, center_y = size // 2, size // 2
            arrow_size = size // 3
            
            points = [
                QPoint(center_x, center_y + arrow_size//2),
                QPoint(center_x - arrow_size//3, center_y - arrow_size//3),
                QPoint(center_x + arrow_size//3, center_y - arrow_size//3)
            ]
            painter.drawPolygon(QPolygon(points))
            
        else:  # neutral
            # Horizontal line
            painter.setBrush(QBrush(self.colors['yellow']))
            painter.setPen(QPen(self.colors['navy'], 2))
            painter.drawEllipse(2, 2, size-4, size-4)
            
            # Line
            painter.setPen(QPen(self.colors['navy'], 2))
            center_x, center_y = size // 2, size // 2
            line_width = size // 3
            
            painter.drawLine(center_x - line_width//2, center_y, 
                           center_x + line_width//2, center_y)
        
        painter.end()
        
        return pixmap
    
    def generate_logo(self, size=256):
        """Generate the main logo."""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw main circle
        painter.setBrush(QBrush(self.colors['navy']))
        painter.setPen(QPen(self.colors['teal'], 4))
        painter.drawEllipse(8, 8, size-16, size-16)
        
        # Draw "NM" text
        font = QFont("Arial", size//8, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(self.colors['teal'], 2))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "NM")
        
        # Draw decorative elements
        painter.setPen(QPen(self.colors['gold'], 2))
        for i in range(8):
            angle = i * 45
            x = size//2 + (size//3) * (angle * 3.14159 / 180)
            y = size//2 + (size//3) * (angle * 3.14159 / 180)
            painter.drawPoint(int(x), int(y))
        
        painter.end()
        
        return pixmap
    
    def generate_all_sprites(self, output_dir="assets/sprites"):
        """Generate all placeholder sprites."""
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate icons
        self.generate_buy_icon().save(os.path.join(output_dir, "icon_buy.png"))
        self.generate_sell_icon().save(os.path.join(output_dir, "icon_sell.png"))
        self.generate_hold_icon().save(os.path.join(output_dir, "icon_hold.png"))
        
        # Generate avatars
        self.generate_bot_avatar('neutral').save(os.path.join(output_dir, "avatar_bot_neutral.png"))
        self.generate_bot_avatar('happy').save(os.path.join(output_dir, "avatar_bot_happy.png"))
        self.generate_bot_avatar('alert').save(os.path.join(output_dir, "avatar_bot_alert.png"))
        
        # Generate sentiment icons
        self.generate_sentiment_icon('up').save(os.path.join(output_dir, "icon_sentiment_up.png"))
        self.generate_sentiment_icon('down').save(os.path.join(output_dir, "icon_sentiment_down.png"))
        self.generate_sentiment_icon('neutral').save(os.path.join(output_dir, "icon_sentiment_neutral.png"))
        
        # Generate logo
        self.generate_logo().save(os.path.join(output_dir, "logo_main.png"))
        
        print(f"Generated all placeholder sprites in {output_dir}")


if __name__ == "__main__":
    # Create QApplication for PySide6
    app = QApplication(sys.argv)
    
    generator = SpriteGenerator()
    generator.generate_all_sprites()
    
    # Clean up
    app.quit()

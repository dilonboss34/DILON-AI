#!/usr/bin/env python3
# mobile/main_mobile.py
"""
Mobile entry point for JARVIS Assistant
Adapted from desktop version for cross-platform mobile use
"""

import sys
import os
from pathlib import Path
from kivy.utils import platform
from kivy.clock import Clock, mainthread

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from kivy.app import App
    from kivy.lang import Builder
    from kivy.core.window import Window
    from kivy.properties import ObjectProperty, StringProperty, ListProperty
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.label import Label
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.widget import Widget
    from kivy.graphics import Color, Line, Ellipse, Rectangle, PushMatrix, PopMatrix, Rotate
    import math
    import random
except ImportError:
    print("Kivy not installed. Please install kivy for mobile version.")
    print("Install with: pip install kivy")
    sys.exit(1)

# Import adapted mobile logic
from jarvis_mobile import JarvisMobile

# Set window size for testing on desktop
if platform in ('win', 'linux', 'macosx'):
    Window.size = (400, 700)
    Window.clearcolor = (0, 0.02, 0.04, 1)  # Dark blue-black background


class ChatLabel(Label):
    """Custom label for chat messages with background"""
    def __init__(self, is_user=False, **kwargs):
        super().__init__(**kwargs)
        self.is_user = is_user
        self.text_size = (self.width, None)
        self.halign = 'left' if is_user else 'right'
        self.valign = 'top'
        self.size_hint_y = None
        self.padding = [dp(10), dp(10)]
        
        # Set colors based on sender
        if is_user:
            self.color = (0.8, 0.8, 0.8, 1)  # Light gray for user
            self.canvas.before.clear()
            with self.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(0, 0.3, 0.5, 0.3)  # Blue tint
                self.rect = RoundedRectangle(
                    pos=self.pos, 
                    size=self.size,
                    radius=[dp(10),]
                )
        else:
            self.color = (0, 0.8, 1, 1)  # C.PRI for Jarvis
            self.canvas.before.clear()
            with self.canvas.before:
                from kivy.graphics import Color, RoundedRectangle
                Color(0, 0.1, 0.2, 0.5)  # Dark blue background
                self.rect = RoundedRectangle(
                    pos=self.pos, 
                    size=self.size,
                    radius=[dp(10),]
                )
        
        self.bind(pos=self.update_rect, size=self.update_rect)
    
    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
    
    def on_size(self, *args):
        self.text_size = (self.width - dp(20), None)
        self.height = self.texture_size[1] + dp(20)


def dp(x):
    """Simple dp conversion for compatibility"""
    try:
        from kivy.metrics import dp as kivy_dp
        return kivy_dp(x)
    except:
        return x  # Fallback

class JarvisFace(Widget):
    state = StringProperty("INITIALISING")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tick = 0
        self.rings = [0.0, 120.0, 240.0]
        self.scan = 0.0
        self.scan2 = 180.0
        self.halo = 55.0
        Clock.schedule_interval(self.update_canvas, 1.0 / 60.0)
        
    def update_canvas(self, dt):
        self.tick += 1
        is_speaking = self.state == "SPEAKING"
        
        # Update animation variables
        self.halo += ((150 if is_speaking else 55) - self.halo) * 0.1
        
        speeds = [1.3, -0.9, 2.0] if is_speaking else [0.55, -0.35, 0.9]
        for i, spd in enumerate(speeds):
            self.rings[i] = (self.rings[i] + spd) % 360
            
        self.scan = (self.scan + (3.0 if is_speaking else 1.3)) % 360
        self.scan2 = (self.scan2 + (-2.0 if is_speaking else -0.75)) % 360
        
        # Redraw
        self.canvas.clear()
        with self.canvas:
            W, H = self.width, self.height
            cx, cy = self.x + W / 2, self.y + H / 2
            fw = min(W, H)
            
            # Halo
            Color(0, 0.83, 1.0, self.halo / 255.0 * 0.1) # C.PRI
            for i in range(5):
                r = fw * 0.31 * (1.8 - i * 0.15)
                Ellipse(pos=(cx-r, cy-r), size=(r*2, r*2))
                
            # Rings
            Color(0, 0.83, 1.0, self.halo / 255.0)
            arcs = [(0.48, 3, 115, 78), (0.40, 2, 78, 55), (0.32, 1, 56, 40)]
            for idx, (r_frac, w_r, arc_l, gap) in enumerate(arcs):
                ring_r = fw * r_frac
                base = self.rings[idx]
                angle = base
                while angle < base + 360:
                    Line(circle=(cx, cy, ring_r, angle, angle + arc_l), width=w_r)
                    angle += arc_l + gap
            
            # Scanners
            sr = fw * 0.50
            ex = 75 if is_speaking else 44
            Color(0, 0.83, 1.0, min(1.0, self.halo * 1.5 / 255.0))
            Line(circle=(cx, cy, sr, self.scan, self.scan + ex), width=2.5)
            
            Color(1.0, 0.42, 0.0, min(1.0, self.halo / 255.0)) # C.ACC
            Line(circle=(cx, cy, sr, self.scan2, self.scan2 + ex), width=1.5)
            
            # Central Orb
            orb_r = fw * 0.27
            for i in range(8, 0, -1):
                r2 = orb_r * i / 8.0
                frc = i / 8.0
                a = min(1.0, self.halo * 1.1 * frc / 255.0)
                Color(0, 60/255.0 * frc, 110/255.0 * frc, a)
                Ellipse(pos=(cx-r2, cy-r2), size=(r2*2, r2*2))


class JarvisMobileApp(App):
    def build(self):
        """Build the mobile application UI"""
        self.title = "JARVIS Mobile"
        self.icon = "face.png"  # Would need mobile-appropriate icon
        
        # Load the Kivy UI
        return Builder.load_file("ui_mobile.kv")
    
    def on_start(self):
        """Initialize JARVIS when app starts"""
        self.jarvis = JarvisMobile()
        # Start the assistant in background
        self.jarvis.start()
        
        # Schedule UI initialization after the widget is fully built
        Clock.schedule_once(self.init_ui, 0.1)
    
    def init_ui(self, dt):
        """Initialize UI components after they're available"""
        # Get UI references
        self.chat_layout = self.root.ids.chat_layout
        self.command_input = self.root.ids.command_input
        
        # Add welcome message
        self.add_message("JARVIS Mobile online. How can I assist you today?", is_user=False)
    
    def on_stop(self):
        """Cleanup when app stops"""
        if hasattr(self, 'jarvis'):
            self.jarvis.stop()
    
    def on_submit(self):
        """Handle text input submission"""
        text = self.command_input.text.strip()
        if text:
            self.add_message(text, is_user=True)
            self.command_input.text = ""
            # Process the command through JARVIS
            self.process_command(text)
    
    def on_microphone(self):
        """Handle microphone button press"""
        # This would trigger voice input
        self.add_message("🎤 Listening...", is_user=False)
        # In real implementation, start speech recognition
    
    def on_file_attach(self):
        """Handle file attachment"""
        self.add_message("📎 File attachment feature coming soon", is_user=False)
    
    def do_web_search(self):
        """Perform web search"""
        self.add_message("🔍 Web search feature coming soon", is_user=False)
    
    def do_weather(self):
        """Get weather"""
        self.add_message("🌤️ Weather feature coming soon", is_user=False)
    
    def do_camera(self):
        """Access camera"""
        self.add_message("📷 Camera feature coming soon", is_user=False)
    
    @mainthread
    def add_message(self, text, is_user=False):
        """Add a message to the chat display"""
        if not hasattr(self, 'chat_layout'):
            return
            
        label = ChatLabel(text=text, is_user=is_user)
        self.chat_layout.add_widget(label)
        # Scroll to bottom
        self.chat_layout.height = self.chat_layout.minimum_height
    
    def process_command(self, text):
        """Process command through JARVIS AI"""
        if hasattr(self, 'jarvis'):
            # Send text to Gemini as if spoken
            if hasattr(self.jarvis, 'speak'):
                # Send to Gemini
                self.jarvis.speak(text)
        else:
            self.add_message("JARVIS not fully initialized.", is_user=False)
            
    @mainthread
    def set_state(self, state):
        """Update JarvisFace state from AI thread"""
        if hasattr(self.root.ids, 'jarvis_face'):
            self.root.ids.jarvis_face.state = state
        if hasattr(self.root.ids, 'state_label'):
            self.root.ids.state_label.text = state


if __name__ == '__main__':
    JarvisMobileApp().run()
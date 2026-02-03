"""
Settings manager for NP2 editor.
Handles loading and saving of application configuration.
"""

import os
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any

SETTINGS_FILE = os.path.join(os.path.expanduser('~'), '.np2', 'settings.json')
DRAFTS_DIR = os.path.join(os.path.expanduser('~'), '.np2', 'drafts')

@dataclass
class AppSettings:
    """Application settings structure."""
    autosave_mode: str = 'off'  # 'off', 'interval', 'change'
    autosave_interval: int = 30  # seconds
    terminal_follow: bool = False
    theme: str = 'light'
    highlight_occurrences: bool = True
    word_wrap: bool = False
    show_workspace: bool = True
    show_terminal: bool = True
    window_geometry: str = '1200x800'

class SettingsManager:
    """Manages application settings and persistence."""
    
    def __init__(self):
        self.settings = AppSettings()
        self._ensure_dirs()
        self.load()
    
    def _ensure_dirs(self):
        """Ensure settings and drafts directories exist."""
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        os.makedirs(DRAFTS_DIR, exist_ok=True)
    
    def load(self):
        """Load settings from file."""
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    # Update dataclass with loaded data, ignoring unknown keys
                    current_dict = asdict(self.settings)
                    current_dict.update({k: v for k, v in data.items() if k in current_dict})
                    self.settings = AppSettings(**current_dict)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def save(self):
        """Save settings to file."""
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(asdict(self.settings), f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get(self, key: str) -> Any:
        """Get a setting value."""
        return getattr(self.settings, key)
    
    def set(self, key: str, value: Any):
        """Set a setting value and save."""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            self.save()
            
    # Session Persistence Helpers
    
    def get_session_path(self):
        """Get path to session file."""
        return os.path.join(os.path.dirname(SETTINGS_FILE), 'session.json')
    
    def save_session(self, open_files, active_index):
        """
        Save current session.
        
        Args:
            open_files: List of dicts {'path': str, 'content': str, 'modified': bool, 'draft_id': str}
            active_index: Index of active tab
        """
        session = {
            'active_index': active_index,
            'files': open_files
        }
        try:
            with open(self.get_session_path(), 'w') as f:
                json.dump(session, f, indent=2)
        except Exception:
            pass
            
    def load_session(self):
        """Load session data."""
        path = self.get_session_path()
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        return None

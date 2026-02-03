"""
Settings dialog for NP2 editor.
"""

import tkinter as tk
from tkinter import ttk

class SettingsDialog(tk.Toplevel):
    """Dialog for editing application settings."""
    
    def __init__(self, parent, settings_manager):
        """
        Initialize settings dialog.
        
        Args:
            parent: Parent window
            settings_manager: SettingsManager instance
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.settings = settings_manager.settings
        
        self.title("Preferences")
        self.geometry("400x350")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.result = False
        
        self._setup_ui()
        self._load_values()
        
        # Center dialog
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
    def _setup_ui(self):
        """Set up the UI components."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Auto-save settings
        autosave_group = ttk.LabelFrame(main_frame, text="Auto-Save", padding=10)
        autosave_group.pack(fill=tk.X, pady=(0, 10))
        
        self.autosave_mode_var = tk.StringVar()
        ttk.Label(autosave_group, text="Mode:").grid(row=0, column=0, sticky='w', pady=5)
        
        modes = [('Off', 'off'), ('On Change', 'change'), ('Interval', 'interval')]
        mode_frame = ttk.Frame(autosave_group)
        mode_frame.grid(row=0, column=1, sticky='w', padx=10)
        
        for text, value in modes:
            ttk.Radiobutton(mode_frame, text=text, variable=self.autosave_mode_var, 
                           value=value, command=self._toggle_interval).pack(side=tk.LEFT, padx=5)
            
        ttk.Label(autosave_group, text="Interval (seconds):").grid(row=1, column=0, sticky='w', pady=5)
        self.interval_var = tk.StringVar()
        self.interval_entry = ttk.Spinbox(autosave_group, from_=5, to=3600, textvariable=self.interval_var, width=10)
        self.interval_entry.grid(row=1, column=1, sticky='w', padx=10)
        
        # Terminal settings
        term_group = ttk.LabelFrame(main_frame, text="Terminal", padding=10)
        term_group.pack(fill=tk.X, pady=(0, 10))
        
        self.term_follow_var = tk.BooleanVar()
        ttk.Checkbutton(term_group, text="Terminal follows workspace selection", 
                       variable=self.term_follow_var).pack(anchor='w')
                       
        # Buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=5)
        
    def _load_values(self):
        """Load current settings values."""
        self.autosave_mode_var.set(self.settings.autosave_mode)
        self.interval_var.set(str(self.settings.autosave_interval))
        self.term_follow_var.set(self.settings.terminal_follow)
        
        self._toggle_interval()
        
    def _toggle_interval(self):
        """Enable/disable interval entry."""
        if self.autosave_mode_var.get() == 'interval':
            self.interval_entry.state(['!disabled'])
        else:
            self.interval_entry.state(['disabled'])
            
    def _save(self):
        """Save settings."""
        try:
            interval = int(self.interval_var.get())
            if interval < 1:
                interval = 1
        except ValueError:
            interval = 30
            
        self.settings_manager.set('autosave_mode', self.autosave_mode_var.get())
        self.settings_manager.set('autosave_interval', interval)
        self.settings_manager.set('terminal_follow', self.term_follow_var.get())
        
        self.result = True
        self.destroy()

import tkinter as tk
from tkinter import ttk
# Mocking dependencies
import sys
import os
sys.path.append(os.getcwd())

# Mock TextEditor to avoid full App deps
class MockEditor(tk.Text):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.filepath = None
        self.modified = False
        self.language = 'Text'
        self.encoding = 'utf-8'
        self.highlighter = type('obj', (object,), {'set_language': lambda x: None, 'highlight_all': lambda: None})()
    
    def set_content(self, content, filepath=None, encoding='utf-8'):
        self.delete('1.0', tk.END)
        self.insert('1.0', content)
        self.filepath = filepath
    
    def get_content(self):
        return self.get('1.0', tk.END)
        
    def mark_saved(self):
        self.modified = False

# Monkey patch imports in tab_manager if needed, 
# but better to rely on actual imports if env is set up.
# We will just run it. If it fails due to missing utils, we know.

from editor.tab_manager import TabManager
# We need to swap TextEditor with MockEditor for isolation if possible.
# But tab_manager imports TextEditor.
# We can just let it import real one. It should work if app.py is not involved.

root = tk.Tk()
root.geometry("600x400")
root.title("Custom Tab Manager Debug")

# Create manager
tm = TabManager(root)
tm.pack(fill=tk.BOTH, expand=True)

# Add tabs
tm.new_tab(None, "Content 1")
tm.new_tab(None, "Content 2")

def on_tab_change(event):
    print("Tab Changed!")

tm.bind('<<NotebookTabChanged>>', on_tab_change)

root.mainloop()

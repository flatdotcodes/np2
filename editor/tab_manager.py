"""
Tab manager for NP2 editor.
Reverted to ttk.Notebook implementation with custom "header bar" close buttons.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from editor.text_editor import TextEditor
from utils.file_utils import read_file, write_file, add_recent_file
from utils.language_detect import detect_language
import os
from utils.settings import DRAFTS_DIR

class TabManager(ttk.Notebook):
    """Manages multiple file tabs using native ttk.Notebook."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        # State
        self.editors = {} # Map widget path (str) -> TextEditor instance
        
        # Bindings
        # Disable Middle Click
        self.bind('<Button-2>', lambda e: 'break')
        # Context Menu
        self.bind('<Button-3>', self._show_context_menu)
        
    def setup_style(self):
        """Configure tab styles (Compatibility Stub)."""
        # Native notebook doesn't need much custom styling, 
        # but we can ensure standard look here if needed.
        pass
        
    def new_tab(self, filepath=None, content=None):
        """Create a new tab with editor."""
        editor = TextEditor(self)
        tab_id = str(editor)
        self.editors[tab_id] = editor
        
        # Bind Close Button from TextEditor header
        editor.close_btn.bind('<Button-1>', lambda e: self.close_tab(tab_id))
        
        # Generate title
        title = "Untitled"
        if filepath:
            title = os.path.basename(filepath)
        else:
            # Smart numbering logic
            existing_titles = set()
            for t_id in self.tabs():
                existing_titles.add(self.tab(t_id, 'text'))
            
            if "Untitled" not in existing_titles:
                title = "Untitled"
            else:
                num = 1
                while True:
                    candidate = f"Untitled-{num}"
                    if candidate not in existing_titles:
                        title = candidate
                        break
                    num += 1
        
        # Add to Notebook
        self.add(editor, text=title)
        
        # Load Content
        if content is not None:
            editor.set_content(content, filepath)
        elif filepath:
            try:
                c, encoding = read_file(filepath)
                editor.set_content(c, filepath, encoding)
                add_recent_file(filepath)
            except Exception as e:
                editor.set_content(f"Error: {e}")
        else:
            editor.set_content("")
            
        # Bind modified event
        editor.bind('<<ContentModified>>', lambda e: self._update_tab_title(tab_id))
        
        # Select
        self.select(editor)
        return editor

    def close_tab(self, tab_id=None):
        """Close a tab (checking for unsaved changes)."""
        if tab_id is None:
            tab_id = self.select()
            
        if not tab_id: return
        
        editor = self.editors.get(tab_id)
        if not editor: 
            # Fallback if lookup fails (shouldn't happen with notebook)
            # Try to get widget from nametowidget?
            try:
                editor = self.nametowidget(tab_id)
            except KeyError:
                return # Can't find it
        
        # Check modified
        if hasattr(editor, 'modified') and editor.modified:
            title = self.tab(tab_id, 'text').rstrip('*')
            res = messagebox.askyesnocancel("Save", f"Save changes to {title}?")
            if res is None: return False
            if res:
                if not self.save_tab(tab_id): return False
        
        # Remove
        self.forget(tab_id)
        editor.destroy()
        if tab_id in self.editors:
            del self.editors[tab_id]
            
        if not self.tabs():
            self.new_tab()
            
        return True

    def close_all_tabs(self):
        for t_id in list(self.tabs()):
            if not self.close_tab(t_id): return False
        return True

    def save_tab(self, tab_id=None):
        if tab_id is None: tab_id = self.select()
        editor = self.editors.get(tab_id)
        if not editor: return False
        
        if editor.filepath:
            try:
                write_file(editor.filepath, editor.get_content(), editor.encoding)
                editor.mark_saved()
                self._update_tab_title(tab_id)
                add_recent_file(editor.filepath)
                return True
            except Exception as e:
                messagebox.showerror("Error", str(e))
                return False
        else:
            return self.save_tab_as(tab_id)

    def save_tab_as(self, tab_id=None):
        from tkinter import filedialog
        from utils.language_detect import LANGUAGE_EXTENSIONS, detect_language
        
        if tab_id is None: tab_id = self.select()
        
        editor = self.editors.get(tab_id)
        if not editor: return False
            
        filetypes = [('All Files', '*.*')]
        for lang, ext in sorted(LANGUAGE_EXTENSIONS.items()):
            filetypes.append((lang.title(), f'*{ext}'))
            
        default_ext = LANGUAGE_EXTENSIONS.get(editor.language, '.txt')
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=default_ext,
            filetypes=filetypes
        )
        
        if filepath:
            editor.filepath = filepath
            editor.language = detect_language(filepath)
            editor.highlighter.set_language(editor.language)
            return self.save_tab(tab_id)
        
        return False

    def _update_tab_title(self, tab_id):
        editor = self.editors.get(tab_id)
        if not editor: return
        title = self.tab(tab_id, 'text').rstrip('*')
        if editor.filepath: title = os.path.basename(editor.filepath)
        if editor.modified: title += '*'
        self.tab(tab_id, text=title)
        self.event_generate('<<FileModified>>')

    def _show_context_menu(self, event):
        # Identify tab at position
        try:
            index = self.index(f"@{event.x},{event.y}")
            # If clicked on empty space, we might get index, but let's check.
            if index is None: return
            
             # We need tab_id (widget path)
             # self.tabs() returns list of paths
            tab_list = self.tabs()
            if index < len(tab_list):
                 tab_id = tab_list[index]
                 
                 menu = tk.Menu(self, tearoff=0)
                 menu.add_command(label='Close', command=lambda: self.close_tab(tab_id))
                 menu.add_command(label='Close All', command=self.close_all_tabs)
                 menu.tk_popup(event.x_root, event.y_root)
        except tk.TclError:
            pass

    def get_session_data(self):
        """Return list of open file paths."""
        data = []
        for tab_id in self.tabs():
             editor = self.editors.get(tab_id)
             if editor and editor.filepath:
                 data.append(editor.filepath)
        return data

    def restore_session(self, file_paths):
        """Restore tabs from file paths."""
        for item in file_paths:
            # Handle legacy session data (might be dict with metadata)
            path = item
            if isinstance(item, dict):
                path = item.get('path') or item.get('filepath')
                
            if path and isinstance(path, str) and os.path.exists(path):
                try:
                    self.new_tab(path)
                except Exception as e:
                    print(f"Error restoring tab: {e}")

    def get_current_editor(self):
        current = self.select()
        if current:
            # When using native Notebook, select() returns the tab_id (widget path)
            return self.editors.get(current)
        return None

    def get_all_editors(self):
        """Return list of all TextEditor instances."""
        return list(self.editors.values())

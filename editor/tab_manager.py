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
            # Check if file was deleted externally
            if not os.path.exists(editor.filepath):
                msg = f"The file '{os.path.basename(editor.filepath)}' no longer exists on disk.\nDo you want to save it as a new file?"
                if not messagebox.askyesno("File Deleted", msg):
                    return False

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
        """Return list of open tabs with state (filepath, cursor, draft content)."""
        data = []
        
        # Ensure drafts dir exists
        if not os.path.exists(DRAFTS_DIR):
            os.makedirs(DRAFTS_DIR)
            
        for tab_id in self.tabs():
             editor = self.editors.get(tab_id)
             if not editor: continue
             
             state = {
                 'filepath': editor.filepath,
                 'cursor': editor.get_cursor_position(),
                 'title': self.tab(tab_id, 'text').rstrip('*') 
             }
             
             # Save unsaved content to draft (Hot Exit)
             # Save draft if modified, regardless of whether it has a filepath
             if editor.modified:
                 draft_name = f"draft_{abs(hash(tab_id))}.txt"
                 draft_path = os.path.join(DRAFTS_DIR, draft_name)
                 try:
                     with open(draft_path, 'w', encoding='utf-8') as f:
                         f.write(editor.get_content())
                     state['draft_path'] = draft_path
                     state['modified'] = True
                 except Exception as e:
                     print(f"Error saving draft: {e}")
             
             data.append(state)
        return data

    def restore_session(self, session_data):
        """Restore tabs from session data."""
        # Handle legacy list-of-strings format
        if not session_data: return

        for item in session_data:
            path = None
            draft_path = None
            cursor = None
            is_modified = False
            title = None
            
            if isinstance(item, str):
                path = item
            elif isinstance(item, dict):
                path = item.get('filepath') or item.get('path')
                draft_path = item.get('draft_path')
                cursor = item.get('cursor')
                is_modified = item.get('modified', False)
                title = item.get('title')
                
            editor = None
            # 1. Try to load file
            if path and os.path.exists(path):
                try:
                    editor = self.new_tab(path)
                except Exception as e:
                    print(f"Error restoring tab {path}: {e}")
            
            # 2. Try to load draft (Untitled/Unsaved OR Hot Exit)
            # Check draft_path separately to overwrite file content if modified
            if draft_path and os.path.exists(draft_path):
                try:
                    with open(draft_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    if editor:
                         # Overwrite content of opened file (Hot Exit)
                         # We set filepath again to be safe, but new_tab already set it
                         editor.set_content(content, path) 
                    else:
                         # Restore untitled tab
                         editor = self.new_tab(content=content)
                    
                    if title:
                        self.tab(editor, text=title)
                    
                    if is_modified:
                        editor.modified = True
                        editor.text.edit_modified(True)
                        self._update_tab_title(str(editor))
                except Exception as e:
                    print(f"Error restoring draft: {e}")
            elif not editor and path: 
                 # File missing, draft missing. 
                 # We tried new_tab(path) above. If that failed, we have nothing.
                 pass
            
            # 3. Restore cursor (Snap to line start for better view stability)
            if editor and cursor:
                if isinstance(cursor, (list, tuple)) and len(cursor) >= 1:
                    editor.set_cursor_position((cursor[0], 0))
                else:
                    editor.set_cursor_position(cursor)

    def get_current_editor(self):
        current = self.select()
        if current:
            # When using native Notebook, select() returns the tab_id (widget path)
            return self.editors.get(current)
        return None

    def get_all_editors(self):
        """Return list of all TextEditor instances."""
        return list(self.editors.values())

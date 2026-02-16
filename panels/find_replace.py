"""
Find and Replace dialog for NP2 editor.
Provides search and replace functionality.
"""

import tkinter as tk
from tkinter import ttk


class FindReplaceDialog:
    """Find and Replace dialog window."""
    
    def __init__(self, parent, editor):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent window
            editor: TextEditor to search in
        """
        self.parent = parent
        self.editor = editor
        self.dialog = None
        self.find_entry = None
        self.replace_entry = None
        self.match_count = 0
        
        # Options
        self.case_sensitive = tk.BooleanVar(value=False)
        self.whole_word = tk.BooleanVar(value=False)
        self.use_regex = tk.BooleanVar(value=False)
    
    def show(self, replace_mode=False):
        """
        Show the dialog.
        
        Args:
            replace_mode: True to show replace options
        """
        if self.dialog and self.dialog.winfo_exists():
            self.dialog.lift()
            self.find_entry.focus_set()
            return
        
        # Create dialog window
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title('Find and Replace' if replace_mode else 'Find')
        self.dialog.transient(self.parent)
        self.dialog.resizable(True, False)
        
        # Make it stay on top
        self.dialog.attributes('-topmost', True)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Find row
        find_frame = ttk.Frame(main_frame)
        find_frame.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(find_frame, text='🔍 Find:', width=10).pack(side=tk.LEFT)
        self.find_entry = ttk.Entry(find_frame, width=40)
        self.find_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Replace row (if in replace mode)
        if replace_mode:
            replace_frame = ttk.Frame(main_frame)
            replace_frame.pack(fill=tk.X, pady=(0, 5))
            
            ttk.Label(replace_frame, text='↔ Replace:', width=10).pack(side=tk.LEFT)
            self.replace_entry = ttk.Entry(replace_frame, width=40)
            self.replace_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Options frame
        options_frame = ttk.Frame(main_frame)
        options_frame.pack(fill=tk.X, pady=(5, 10))
        
        ttk.Checkbutton(
            options_frame, 
            text='🔤 Case Sensitive', 
            variable=self.case_sensitive
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Checkbutton(
            options_frame, 
            text='📝 Whole Word', 
            variable=self.whole_word
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Checkbutton(
            options_frame, 
            text='⚙ Regex', 
            variable=self.use_regex
        ).pack(side=tk.LEFT)
        
        # Status label
        self.status_label = ttk.Label(main_frame, text='')
        self.status_label.pack(fill=tk.X, pady=(0, 5))
        
        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)
        
        ttk.Button(
            buttons_frame, 
            text='◀ Find Previous', 
            command=self._find_previous
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame, 
            text='▶ Find Next', 
            command=self._find_next
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame, 
            text='✨ Highlight All', 
            command=self._highlight_all
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        if replace_mode:
            ttk.Button(
                buttons_frame, 
                text='↔ Replace', 
                command=self._replace
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            ttk.Button(
                buttons_frame, 
                text='↔↔ Replace All', 
                command=self._replace_all
            ).pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(
            buttons_frame, 
            text='✕ Close', 
            command=self._close
        ).pack(side=tk.RIGHT)
        
        # Bind events
        self.find_entry.bind('<Return>', lambda e: self._find_next())
        self.find_entry.bind('<Escape>', lambda e: self._close())
        self.find_entry.bind('<KeyRelease>', self._on_find_change)
        
        if replace_mode and self.replace_entry:
            self.replace_entry.bind('<Return>', lambda e: self._replace())
            self.replace_entry.bind('<Escape>', lambda e: self._close())
        
        self.dialog.bind('<Escape>', lambda e: self._close())
        
        # Pre-fill with selection
        try:
            selected = self.editor.text.get('sel.first', 'sel.last')
            if selected and '\n' not in selected:
                self.find_entry.insert(0, selected)
                self.find_entry.select_range(0, tk.END)
        except tk.TclError:
            pass
        
        # Focus find entry
        self.find_entry.focus_set()
        
        # Position dialog near parent
        self._position_dialog()
    
    def _position_dialog(self):
        """Position dialog to the right of parent."""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        
        dialog_width = self.dialog.winfo_width()
        
        x = parent_x + parent_width - dialog_width - 50
        y = parent_y + 100
        
        self.dialog.geometry(f'+{x}+{y}')
    
    def _on_find_change(self, event=None):
        """Handle changes to find text."""
        # Ignore Return key release (fixes highlight disappearing)
        if event and event.keysym in ('Return', 'KP_Enter'):
            return
            
        # Clear highlights when text changes
        self.editor.clear_search_highlights()
        self.status_label.configure(text='')
    
    def _find_next(self):
        """Find next occurrence."""
        find_text = self.find_entry.get()
        if not find_text:
            return
        
        pos = self.editor.find_text(
            find_text,
            case_sensitive=self.case_sensitive.get(),
            whole_word=self.whole_word.get(),
            regex=self.use_regex.get()
        )
        
        if pos:
            self.status_label.configure(text=f'Found at line {pos.split(".")[0]}')
        else:
            self.status_label.configure(text='No match found')
    
    def _find_previous(self):
        """Find previous occurrence."""
        find_text = self.find_entry.get()
        if not find_text:
            return
        
        # Get current position
        current = self.editor.text.index('insert')
        
        # Search backwards
        pos = self.editor.text.search(
            find_text,
            current,
            backwards=True,
            stopindex='1.0',
            nocase=not self.case_sensitive.get(),
            regexp=self.use_regex.get()
        )
        
        # Wrap around
        if not pos:
            pos = self.editor.text.search(
                find_text,
                'end',
                backwards=True,
                stopindex=current,
                nocase=not self.case_sensitive.get(),
                regexp=self.use_regex.get()
            )
        
        if pos:
            end = f'{pos}+{len(find_text)}c'
            self.editor.text.tag_remove('search', '1.0', 'end')
            self.editor.text.tag_add('search', pos, end)
            self.editor.text.mark_set('insert', pos)
            self.editor.text.see(pos)
            # self.editor.text.tag_add('sel', pos, end)  # S01 Fix: Don't select
            self.status_label.configure(text=f'Found at line {pos.split(".")[0]}')
        else:
            self.status_label.configure(text='No match found')
    
    def _highlight_all(self):
        """Highlight all occurrences."""
        find_text = self.find_entry.get()
        if not find_text:
            return
        
        count = self.editor.highlight_all_occurrences(find_text)
        self.match_count = count
        self.status_label.configure(text=f'{count} occurrences highlighted')
    
    def _replace(self):
        """Replace current occurrence."""
        if not self.replace_entry:
            return
        
        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        
        if not find_text:
            return
        
        replaced = self.editor.replace_text(
            find_text,
            replace_text,
            case_sensitive=self.case_sensitive.get()
        )
        
        if replaced:
            self.status_label.configure(text='Replaced')
            # Find next after replace
            self._find_next()
        else:
            self.status_label.configure(text='No match at cursor')
    
    def _replace_all(self):
        """Replace all occurrences."""
        if not self.replace_entry:
            return
        
        find_text = self.find_entry.get()
        replace_text = self.replace_entry.get()
        
        if not find_text:
            return
        
        count = self.editor.replace_all(
            find_text,
            replace_text,
            case_sensitive=self.case_sensitive.get()
        )
        
        self.status_label.configure(text=f'Replaced {count} occurrences')
    
    def _close(self):
        """Close the dialog."""
        if self.dialog:
            self.editor.clear_search_highlights()
            self.dialog.destroy()
            self.dialog = None
    
    def set_editor(self, editor):
        """
        Set the editor to search in.
        
        Args:
            editor: TextEditor to search in
        """
        self.editor = editor

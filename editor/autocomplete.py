"""
Autocomplete/text prediction for NP2 editor.
Provides word suggestions based on document content.
"""

import re
import tkinter as tk


class AutoComplete:
    """Handles autocomplete functionality for the text editor."""
    
    def __init__(self, text_widget):
        """
        Initialize autocomplete.
        
        Args:
            text_widget: Tkinter Text widget
        """
        self.text_widget = text_widget
        self.popup = None
        self.listbox = None
        self.words = set()
        self.min_word_length = 2
        self.min_prefix_length = 3  # Require 3 chars before showing
        self.enabled = True
        self._bindings_added = False
        
        # Bind key release with add=True to not override existing bindings
        self.text_widget.bind('<KeyRelease>', self._on_key_release, add=True)
        self.text_widget.bind('<FocusOut>', self._hide_popup, add=True)
    
    def _build_word_list(self):
        """Build word list from document content."""
        # Optimization: Don't scan huge files
        if self.text_widget.index('end-1c') == '1.0':
            return

        # Skip if file is too large (causes CPU spikes)
        content = self.text_widget.get('1.0', 'end-1c')
        if len(content) > 50000:  # 50k char limit
            self.words = set()  # Clear words for large files
            return
        
        # Extract words (alphanumeric and underscores)
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
        matches = re.findall(pattern, content)
        
        # Limit word count to prevent slow operations
        unique_words = {w for w in matches if len(w) >= self.min_word_length}
        if len(unique_words) > 1000:
            # Take first 1000 to avoid processing overhead
            self.words = set(list(unique_words)[:1000])
        else:
            self.words = unique_words
    
    def _get_current_word(self):
        """Get the word currently being typed."""
        # Get text from line start to cursor
        cursor_pos = self.text_widget.index('insert')
        line_start = f'{cursor_pos.split(".")[0]}.0'
        text_before_cursor = self.text_widget.get(line_start, cursor_pos)
        
        # Find current word
        match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)$', text_before_cursor)
        return match.group(1) if match else ''
    
    def _get_suggestions(self, prefix):
        """
        Get word suggestions for a prefix.
        
        Args:
            prefix: Word prefix to match
            
        Returns:
            List of matching words
        """
        if len(prefix) < self.min_prefix_length:
            return []
        
        prefix_lower = prefix.lower()
        matches = [w for w in self.words if w.lower().startswith(prefix_lower) and w != prefix]
        
        # Sort by length, then alphabetically
        return sorted(matches, key=lambda x: (len(x), x.lower()))[:10]
    
    def _on_key_release(self, event):
        """Handle key release events."""
        if not self.enabled:
            return
        
        # Ignore navigation keys
        ignore_keys = {'Shift_L', 'Shift_R', 'Control_L', 'Control_R', 
                       'Alt_L', 'Alt_R', 'Escape', 'Return', 'Tab',
                       'Up', 'Down', 'Left', 'Right', 'Home', 'End',
                       'Prior', 'Next', 'Insert', 'Delete', 'BackSpace'}
        
        if event.keysym in ignore_keys:
            if event.keysym == 'Escape':
                self._hide_popup()
            return

        # Get current word immediately to decide if we should show suggestions
        current_word = self._get_current_word()
        if not current_word or len(current_word) < self.min_prefix_length:
            self._hide_popup()
            return
            
        # Debounce word list rebuilding (heavy operation)
        if hasattr(self, '_build_job') and self._build_job:
            self.text_widget.after_cancel(self._build_job)
        self._build_job = self.text_widget.after(300, lambda: self._update_suggestions(current_word))

    def _update_suggestions(self, current_word):
        """Build word list and show suggestions."""
        self._build_word_list()
        
        # Re-check current word (might have changed? No, we use the one from trigger time?
        # Actually better to re-get current word to be safe, or use passed one if valid.
        # But cursor might have moved. Let's start with rebuild.
        
        # Get suggestions based on CURRENT word at cursor (user might have typed more)
        real_current = self._get_current_word()
        if not real_current or len(real_current) < self.min_prefix_length:
            self._hide_popup()
            return

        suggestions = self._get_suggestions(real_current)
        if suggestions:
            self._show_popup(suggestions)
        else:
            self._hide_popup()
    
    def _show_popup(self, suggestions):
        """
        Show the autocomplete popup.
        
        Args:
            suggestions: List of suggestions to show
        """
        # Create popup if needed
        if not self.popup:
            self.popup = tk.Toplevel(self.text_widget)
            self.popup.wm_overrideredirect(True)
            self.popup.wm_attributes('-topmost', True)
            
            self.listbox = tk.Listbox(
                self.popup,
                width=30,
                height=min(len(suggestions), 10),
                font=('Consolas', 10),
                selectmode=tk.SINGLE,
                activestyle='none',
                bg='#2d2d2d',
                fg='#f0f0f0',
                selectbackground='#0078d4',
                selectforeground='#ffffff',
                borderwidth=1,
                relief='solid',
            )
            self.listbox.pack(fill=tk.BOTH, expand=True)
            
            # Bind listbox events
            self.listbox.bind('<Double-Button-1>', self._on_select)
            self.listbox.bind('<Return>', self._on_select)
            
            # Bind keyboard navigation
            self.text_widget.bind('<Down>', self._select_next)
            self.text_widget.bind('<Up>', self._select_prev)
            self.text_widget.bind('<Tab>', self._on_select)
            self.text_widget.bind('<Return>', self._on_enter)
        
        # Update listbox content
        self.listbox.delete(0, tk.END)
        for suggestion in suggestions:
            self.listbox.insert(tk.END, suggestion)
        
        # Update height
        self.listbox.configure(height=min(len(suggestions), 10))
        
        # Select first item
        self.listbox.selection_set(0)
        
        # Position popup
        try:
            x, y, _, height = self.text_widget.bbox('insert')
            root_x = self.text_widget.winfo_rootx() + x
            root_y = self.text_widget.winfo_rooty() + y + height + 2
            self.popup.wm_geometry(f'+{root_x}+{root_y}')
            self.popup.deiconify()
        except Exception:
            self._hide_popup()
    
    def _hide_popup(self, event=None):
        """Hide the autocomplete popup."""
        if self.popup:
            self.popup.withdraw()
    
    def _select_next(self, event):
        """Select next item in popup."""
        if self.popup and self.popup.winfo_viewable():
            current = self.listbox.curselection()
            if current:
                idx = current[0]
                if idx < self.listbox.size() - 1:
                    self.listbox.selection_clear(idx)
                    self.listbox.selection_set(idx + 1)
                    self.listbox.see(idx + 1)
            return 'break'
    
    def _select_prev(self, event):
        """Select previous item in popup."""
        if self.popup and self.popup.winfo_viewable():
            current = self.listbox.curselection()
            if current:
                idx = current[0]
                if idx > 0:
                    self.listbox.selection_clear(idx)
                    self.listbox.selection_set(idx - 1)
                    self.listbox.see(idx - 1)
            return 'break'
    
    def _on_enter(self, event):
        """Handle Enter key."""
        if self.popup and self.popup.winfo_viewable():
            self._on_select(event)
            return 'break'
    
    def _on_select(self, event=None):
        """Handle selection of a suggestion."""
        if not self.popup or not self.popup.winfo_viewable():
            return
        
        selection = self.listbox.curselection()
        if not selection:
            return 'break'
        
        # Get selected word
        word = self.listbox.get(selection[0])
        
        # Get current word to replace
        # Get current word to replace (full word at cursor)
        # We need to find the start and end of the word under cursor
        cursor_pos = self.text_widget.index('insert')
        line, col = map(int, cursor_pos.split('.'))
        
        # Get line text
        line_text = self.text_widget.get(f'{line}.0', f'{line}.end')
        
        # Find word boundaries
        start_col = col
        while start_col > 0 and (line_text[start_col-1].isalnum() or line_text[start_col-1] == '_'):
            start_col -= 1
            
        end_col = col
        while end_col < len(line_text) and (line_text[end_col].isalnum() or line_text[end_col] == '_'):
            end_col += 1
            
        word_start = f'{line}.{start_col}'
        word_end = f'{line}.{end_col}'
        
        self.text_widget.delete(word_start, word_end)
        self.text_widget.insert(word_start, word)
        
        self._hide_popup()
        return 'break'
    
    def set_enabled(self, enabled):
        """
        Enable or disable autocomplete.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        if not enabled:
            self._hide_popup()
    
    def add_words(self, words):
        """
        Add custom words to the word list.
        
        Args:
            words: Iterable of words to add
        """
        self.words.update(words)
    
    def destroy(self):
        """Clean up resources."""
        if self.popup:
            self.popup.destroy()
            self.popup = None

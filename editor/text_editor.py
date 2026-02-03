"""
Core text editor widget for NP2.
Rich text editor with line numbers, syntax highlighting, and more.
"""

import os
import tkinter as tk
from tkinter import ttk
from editor.syntax import SyntaxHighlighter
from editor.autocomplete import AutoComplete
from utils.language_detect import detect_language, SUPPORTED_LANGUAGES


class LineNumbers(tk.Canvas):
    """Line numbers widget for the text editor."""
    
    def __init__(self, parent, text_widget, **kwargs):
        """
        Initialize line numbers.
        
        Args:
            parent: Parent widget
            text_widget: Associated Text widget
        """
        super().__init__(parent, **kwargs)
        self.text_widget = text_widget
        self.font = ('Consolas', 11)
        
        # Colors (will be updated by theme) - use light defaults
        self.fg_color = '#237893'
        self.bg_color = '#f3f3f3'
        
        self.lint_markers = {}  # {line_num: color}
        
        self.configure(bg=self.bg_color, highlightthickness=0, width=50)
    
    def redraw(self):
        """Redraw line numbers."""
        self.delete('all')
        
        # Get visible line range
        first_visible = self.text_widget.index('@0,0')
        last_visible = self.text_widget.index(f'@0,{self.text_widget.winfo_height()}')
        
        first_line = int(first_visible.split('.')[0])
        last_line = int(last_visible.split('.')[0])
        
        # Get total lines for width calculation
        total_lines = int(self.text_widget.index('end-1c').split('.')[0])
        width = max(len(str(total_lines)) * 10 + 20, 50)
        self.configure(width=width)
        
        # Draw line numbers
        for line_num in range(first_line, last_line + 1):
            try:
                dline_info = self.text_widget.dlineinfo(f'{line_num}.0')
                if dline_info:
                    y = dline_info[1]
                    
                    # Draw lint marker if present
                    if line_num in self.lint_markers:
                        color = self.lint_markers[line_num]
                        # Draw small circle
                        self.create_oval(
                            5, y + 5, 10, y + 10,
                            fill=color,
                            outline=color
                        )
                    
                    self.create_text(
                        width - 10,
                        y,
                        anchor='ne',
                        text=str(line_num),
                        font=self.font,
                        fill=self.fg_color
                    )
            except Exception:
                pass
    
    def set_colors(self, fg, bg):
        """Set colors for line numbers."""
        self.fg_color = fg
        self.bg_color = bg
        self.configure(bg=bg)
        self.redraw()

    def set_lint_markers(self, markers):
        """
        Set lint markers.
        
        Args:
            markers: Dict mapping line numbers to color strings
        """
        self.lint_markers = markers
        self.redraw()


class TextEditor(tk.Frame):
    """
    Rich text editor widget with line numbers, syntax highlighting,
    autocomplete, and more.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the text editor.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)
        
        self.filepath = None
        self.encoding = 'utf-8'
        self.language = 'text'
        self.modified = False
        self.theme = 'light'
        
        # Occurrence highlighting
        self.occurrence_tag = 'occurrence'
        self.search_tag = 'search'
        self.current_line_tag = 'current_line'
        self.occurrence_positions = []  # List of (start, end) positions
        self.current_occurrence_index = -1
        self.occurrence_highlight_enabled = True  # Toggle for feature
        self.highlighted_word = None  # Currently highlighted word
        
        self._setup_ui()
        self._setup_bindings()
    
    def _setup_ui(self):
        """Set up the UI components."""
        # Header Bar (Sliver with Close Button)
        self.header = tk.Frame(self, height=18, bg='#e1e1e1')
        self.header.pack(side=tk.TOP, fill=tk.X)
        self.header.pack_propagate(False) # Force height
        
        # Close Button (X)
        self.close_btn = tk.Label(self.header, text=' x ', font=('Arial', 8), bg='#e1e1e1', fg='#555', cursor='hand2')
        self.close_btn.pack(side=tk.RIGHT, padx=2)
        self.close_btn.bind('<Enter>', lambda e: self.close_btn.configure(bg='#cc0000', fg='white'))
        self.close_btn.bind('<Leave>', lambda e: self.close_btn.configure(bg='#e1e1e1', fg='#555'))
        
        # Main container
        self.container = tk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)
        
        # Text widget with scrollbars
        self.text = tk.Text(
            self.container,
            wrap=tk.NONE,
            font=('Consolas', 11),
            undo=True,
            autoseparators=True,
            maxundo=-1,
            padx=5,
            pady=5,
            insertwidth=2,
        )
        
        # Scrollbars
        self.v_scroll = ttk.Scrollbar(self.container, orient=tk.VERTICAL, command=self.text.yview)
        self.h_scroll = ttk.Scrollbar(self.container, orient=tk.HORIZONTAL, command=self.text.xview)
        self.text.configure(yscrollcommand=self._on_scroll, xscrollcommand=self.h_scroll.set)
        
        # Line numbers
        self.line_numbers = LineNumbers(self.container, self.text)
        
        # Grid layout
        self.line_numbers.grid(row=0, column=0, sticky='ns')
        self.text.grid(row=0, column=1, sticky='nsew')
        self.v_scroll.grid(row=0, column=2, sticky='ns')
        self.h_scroll.grid(row=1, column=1, sticky='ew')
        
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(1, weight=1)
        
        # Occurrence navigation bar (hidden by default)
        # Now that duplicate text widget is gone, this is the safe and correct place.
        self.occurrence_bar = tk.Frame(self.text, bg='#f0f0f0', height=28, relief=tk.RAISED, bd=1)
        # self.occurrence_bar.pack_propagate(False) # S07 Fix: Allow resizing to fit content
        
        # Bar content
        self.occurrence_label = tk.Label(self.occurrence_bar, text='', bg='#f0f0f0', font=('Consolas', 9))
        self.occurrence_label.pack(side=tk.LEFT, padx=10)
        
        # Close button
        close_btn = tk.Button(self.occurrence_bar, text='✕', command=self._close_occurrence_bar,
                               relief=tk.FLAT, bg='#f0f0f0', font=('Consolas', 9), width=2)
        close_btn.pack(side=tk.RIGHT, padx=2)
        
        # Navigation buttons
        next_btn = tk.Button(self.occurrence_bar, text='▼', command=self.next_occurrence,
                              relief=tk.GROOVE, bd=1, bg='#e0e0e0', font=('Consolas', 9), width=2)
        next_btn.pack(side=tk.RIGHT, padx=2)
        
        prev_btn = tk.Button(self.occurrence_bar, text='▲', command=self.prev_occurrence,
                              relief=tk.GROOVE, bd=1, bg='#e0e0e0', font=('Consolas', 9), width=2)
        prev_btn.pack(side=tk.RIGHT, padx=2)
        

        
        # Syntax highlighter
        self.highlighter = SyntaxHighlighter(self.text, self.theme)
        
        # Autocomplete
        self.autocomplete = AutoComplete(self.text)
        
        # Configure tags for highlighting - use light theme colors
        self.text.tag_configure(self.occurrence_tag, background='#add6ff')
        self.text.tag_configure(self.search_tag, background='#f8961e')
        self.text.tag_configure(self.current_line_tag, background='#fffbdd')  # Default light
        self.text.tag_lower(self.current_line_tag)  # Ensure it is behind text
        self.text.tag_raise('sel')  # Ensure selection stays on top
        
        # Apply initial theme
        self._apply_theme()
    
    def _setup_bindings(self):
        """Set up event bindings."""
        # Content change events
        self.text.bind('<<Modified>>', self._on_modified)
        self.text.bind('<KeyRelease>', self._on_key_release, add='+')
        self.text.bind('<ButtonRelease-1>', self._on_click)
        
        # Scroll sync for line numbers
        self.text.bind('<Configure>', lambda e: self.line_numbers.redraw())
        self.text.bind('<MouseWheel>', lambda e: self.after(1, self.line_numbers.redraw))
        self.text.bind('<<Selection>>', self._on_selection_change)
    
    def _on_scroll(self, *args):
        """Handle scroll events."""
        self.v_scroll.set(*args)
        self.line_numbers.redraw()
    
    def _on_modified(self, event=None):
        """Handle modification events."""
        if self.text.edit_modified():
            if not self.modified:
                self.modified = True
                self.event_generate('<<ContentModified>>')
    
    def _on_key_release(self, event=None):
        """Handle key release for highlighting updates."""
        # Update current line highlight immediately
        self._highlight_current_line()
        
        # Schedule highlighting update
        if hasattr(self, '_highlight_job') and self._highlight_job:
            self.after_cancel(self._highlight_job)
        self._highlight_job = self.after(100, self._update_highlighting)
        
        # Update line numbers
        self.line_numbers.redraw()
    
    def _on_click(self, event=None):
        """Handle click events."""
        self.line_numbers.redraw()
        self._highlight_current_line()
    
    def _on_selection_change(self, event=None):
        """Handle selection change - highlight occurrences when text is selected."""
        self._highlight_current_line()
        
        # Debounce selection changes
        if hasattr(self, '_selection_job') and self._selection_job:
            self.after_cancel(self._selection_job)
        self._selection_job = self.after(150, self._check_selection)
    
    def _check_selection(self):
        """Check current selection and highlight occurrences."""
        try:
            sel_start = self.text.index('sel.first')
            sel_end = self.text.index('sel.last')
            selected = self.text.get(sel_start, sel_end).strip()
            
            if selected and len(selected) > 1:
                self.highlight_all_occurrences(selected)
            else:
                self._maybe_clear_occurrences()
        except tk.TclError:
            # No selection - clear highlights
            self._maybe_clear_occurrences()
    
    def _maybe_clear_occurrences(self):
        """Clear occurrence highlights if not in double-click mode."""
        # This method is called when selection is cleared.
        # We only want to clear if there are existing occurrences,
        # and not if the user is just double-clicking to select a word,
        # which would immediately re-highlight.
        if self.occurrence_positions:
            self.clear_occurrence_highlights()
            self._hide_occurrence_bar()
    
    def _show_occurrence_bar(self):
        """Show the occurrence navigation bar (overlay)."""
        # Calculate width based on content
        self.occurrence_bar.update_idletasks()
        
        # Overlay in top-right corner of TEXT widget
        # x=-5 for small padding from right edge of text area
        self.occurrence_bar.place(relx=1.0, x=-5, y=5, anchor='ne')
        # Ensure it's on top
        self.occurrence_bar.lift()
    
    def _hide_occurrence_bar(self):
        """Hide the occurrence navigation bar."""
        self.occurrence_bar.place_forget()
    
    def _close_occurrence_bar(self):
        """Close occurrence bar and clear highlights."""
        self.clear_occurrence_highlights()
        self._hide_occurrence_bar()
    
    def _update_occurrence_bar(self):
        """Update the occurrence bar label."""
        if self.occurrence_positions and self.highlighted_word:
            total = len(self.occurrence_positions)
            current = self.current_occurrence_index + 1 if self.current_occurrence_index >= 0 else 0
            filename = os.path.basename(self.filepath) if self.filepath else 'Untitled'
            self.occurrence_label.configure(text=f'"{self.highlighted_word}" - {current}/{total} in {filename}')
        else:
            self.occurrence_label.configure(text='')
    
    def _update_highlighting(self):
        """Update syntax highlighting for visible region."""
        try:
            first_visible = self.text.index('@0,0')
            last_visible = self.text.index(f'@0,{self.text.winfo_height()}')
            self.highlighter.highlight_region(first_visible, last_visible)
        except Exception:
            pass
    
    def _apply_theme(self):
        """Apply the current theme."""
        colors = self.highlighter.get_theme_colors()
        
        self.text.configure(
            background=colors['background'],
            foreground=colors['foreground'],
            insertbackground=colors['foreground'],
            selectbackground=colors['selection'],
        )
        
        self.text.tag_configure(self.current_line_tag, background=colors['line_highlight'])
        
        self.line_numbers.set_colors(colors['line_number'], colors['line_number_bg'])
        self.configure(bg=colors['background'])
    
    def set_content(self, content, filepath=None, encoding='utf-8'):
        """
        Set the editor content.
        
        Args:
            content: Text content
            filepath: Optional file path
            encoding: File encoding
        """
        self.text.delete('1.0', 'end')
        self.text.insert('1.0', content)
        
        self.filepath = filepath
        self.encoding = encoding
        self.modified = False
        self.text.edit_modified(False)
        self.text.edit_reset()
        
        # Detect language
        if filepath:
            self.language = detect_language(filepath, content)
            self.highlighter.set_language(self.language)
        
        # Apply highlighting
        self.highlighter.highlight_all()
        self.line_numbers.redraw()
    
    def get_content(self):
        """Get the editor content."""
        return self.text.get('1.0', 'end-1c')
    
    def set_language(self, language):
        """
        Set the programming language.
        
        Args:
            language: Language name
        """
        self.language = language
        self.highlighter.set_language(language)
        self.highlighter.highlight_all()
    
    def set_theme(self, theme):
        """
        Set the color theme.
        
        Args:
            theme: Theme name ('dark' or 'light')
        """
        self.theme = theme
        self.highlighter.set_theme(theme)
        self._apply_theme()
    
    def highlight_all_occurrences(self, text):
        """
        Highlight all occurrences of text.
        
        Args:
            text: Text to highlight
        """
        # Clear previous highlights
        self.clear_occurrence_highlights()
        self.occurrence_positions = []
        self.current_occurrence_index = -1
        self.highlighted_word = text
        
        if not text or not self.occurrence_highlight_enabled:
            self._hide_occurrence_bar()
            return 0
        
        # Find and highlight all occurrences
        start = '1.0'
        count = 0
        
        while True:
            pos = self.text.search(text, start, stopindex='end', nocase=True)
            if not pos:
                break
            
            end = f'{pos}+{len(text)}c'
            self.text.tag_add(self.occurrence_tag, pos, end)
            self.occurrence_positions.append((pos, end))
            start = end
            count += 1
        
        # Show navigation bar if occurrences found
        if count > 0:
            # Try to find current selection in occurrences to set index
            try:
                sel_start = self.text.index('sel.first')
                for i, (pos, _) in enumerate(self.occurrence_positions):
                    if self.text.compare(pos, '==', sel_start):
                        self.current_occurrence_index = i
                        break
            except tk.TclError:
                pass
                
            self._show_occurrence_bar()
            self._update_occurrence_bar()
        
        return count
    
    def clear_occurrence_highlights(self):
        """Clear all occurrence highlights."""
        self.text.tag_remove(self.occurrence_tag, '1.0', 'end')
        self.occurrence_positions = []
        self.current_occurrence_index = -1
    
    def next_occurrence(self) -> bool:
        """
        Navigate to next occurrence.
        
        Returns:
            True if navigation succeeded
        """
        if not self.occurrence_positions:
            return False
        
        self.current_occurrence_index = (self.current_occurrence_index + 1) % len(self.occurrence_positions)
        pos, end = self.occurrence_positions[self.current_occurrence_index]
        
        self.text.mark_set('insert', pos)
        self.text.mark_set('insert', pos)
        self.text.see(pos)
        # Scroll a bit more to show context if possible (center it)
        try:
            self.text.update_idletasks()
            line_info = self.text.dlineinfo(pos)
            if line_info is None: # Not visible yet, force center
                # Quick scroll to center: see -> get y -> scroll
                # Tkinter see() brings it into view. To center, we need math.
                # Simple hack: see, then scroll up a few lines if at top
                pass
        except Exception:
            pass
            
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_add('sel', pos, end)
        self._update_occurrence_bar()
        return True
    
    def prev_occurrence(self) -> bool:
        """
        Navigate to previous occurrence.
        
        Returns:
            True if navigation succeeded
        """
        if not self.occurrence_positions:
            return False
        
        self.current_occurrence_index = (self.current_occurrence_index - 1) % len(self.occurrence_positions)
        pos, end = self.occurrence_positions[self.current_occurrence_index]
        
        self.text.mark_set('insert', pos)
        self.text.mark_set('insert', pos)
        self.text.see(pos)
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_remove('sel', '1.0', 'end')
        self.text.tag_add('sel', pos, end)
        self._update_occurrence_bar()
        return True
    
    def set_occurrence_highlight_enabled(self, enabled: bool):
        """Enable or disable occurrence highlighting."""
        self.occurrence_highlight_enabled = enabled
        if not enabled:
            self.clear_occurrence_highlights()
    
    def clear_search_highlights(self):
        """Clear search highlights."""
        self.text.tag_remove(self.search_tag, '1.0', 'end')
        
    def _highlight_current_line(self):
        """Highlight the current line."""
        # Remove existing highlight
        self.text.tag_remove(self.current_line_tag, '1.0', 'end')
        
        # Add highlight to current line
        try:
            line_str = self.text.index('insert').split('.')[0]
            line = int(line_str)
            start = f'{line}.0'
            end = f'{line + 1}.0'
            self.text.tag_add(self.current_line_tag, start, end)
        except Exception:
            pass
    
    def find_text(self, text, case_sensitive=False, whole_word=False, regex=False, start=None):
        """
        Find text in the editor.
        
        Args:
            text: Text to find
            case_sensitive: Case sensitive search
            whole_word: Match whole words only
            regex: Use regex search
            start: Starting position
            
        Returns:
            Position of found text or None
        """
        if not text:
            return None
        
        if start is None:
            start = self.text.index('insert+1c')
        
        # Search options
        nocase = not case_sensitive
        
        # Perform search
        pos = self.text.search(
            text, 
            start, 
            stopindex='end', 
            nocase=nocase,
            regexp=regex
        )
        
        # Wrap around if not found
        if not pos:
            pos = self.text.search(
                text, 
                '1.0', 
                stopindex=start, 
                nocase=nocase,
                regexp=regex
            )
        
        if pos:
            # Highlight found text (S01 Fix: Don't select, just highlight)
            end = f'{pos}+{len(text)}c'
            self.text.tag_remove(self.search_tag, '1.0', 'end')
            self.text.tag_add(self.search_tag, pos, end)
            self.text.mark_set('insert', end)
            self.text.see(pos)
            # S01 Fix: Removed tag_add('sel')
        
        return pos
    
    def replace_text(self, find_text, replace_text, case_sensitive=False):
        """
        Replace current selection or find next.
        
        Args:
            find_text: Text to find
            replace_text: Replacement text
            case_sensitive: Case sensitive search
            
        Returns:
            True if replaced
        """
        try:
            # S01 Fix: Check selection OR search tag
            target_start = None
            target_end = None
            
            # First check selection
            try:
                target_start = self.text.index('sel.first')
                target_end = self.text.index('sel.last')
            except tk.TclError:
                # No selection, check search tag
                ranges = self.text.tag_ranges(self.search_tag)
                if ranges:
                    target_start = ranges[0]
                    target_end = ranges[1]
            
            if not target_start:
                return False
                
            selected = self.text.get(target_start, target_end)
            
            # Check if text matches
            match = (selected == find_text if case_sensitive 
                    else selected.lower() == find_text.lower())
            
            if match:
                self.text.delete(target_start, target_end)
                self.text.insert(sel_start, replace_text)
                return True
        except tk.TclError:
            pass
        
        # Find next
        self.find_text(find_text, case_sensitive)
        return False
    
    def replace_all(self, find_text, replace_text, case_sensitive=False):
        """
        Replace all occurrences.
        
        Args:
            find_text: Text to find
            replace_text: Replacement text
            case_sensitive: Case sensitive search
            
        Returns:
            Number of replacements
        """
        if not find_text:
            return 0
        
        count = 0
        start = '1.0'
        nocase = not case_sensitive
        
        while True:
            pos = self.text.search(find_text, start, stopindex='end', nocase=nocase)
            if not pos:
                break
            
            end = f'{pos}+{len(find_text)}c'
            self.text.delete(pos, end)
            self.text.insert(pos, replace_text)
            start = f'{pos}+{len(replace_text)}c'
            count += 1
        
        return count
    
    def goto_line(self, line_number):
        """
        Go to a specific line.
        
        Args:
            line_number: Line number to go to
        """
        self.text.mark_set('insert', f'{line_number}.0')
        self.text.see(f'{line_number}.0')
        self.line_numbers.redraw()
        self._highlight_current_line()
        
    def set_lint_markers(self, markers):
        """
        Set lint markers on line numbers.
        
        Args:
            markers: Dict mapping line numbers to color strings
        """
        self.line_numbers.set_lint_markers(markers)
    
    def get_cursor_position(self):
        """
        Get current cursor position.
        
        Returns:
            Tuple of (line, column)
        """
        pos = self.text.index('insert')
        line, col = pos.split('.')
        return int(line), int(col)
    
    def set_word_wrap(self, enabled):
        """
        Enable or disable word wrap.
        
        Args:
            enabled: True to enable word wrap
        """
        self.text.configure(wrap=tk.WORD if enabled else tk.NONE)
        if enabled:
            self.h_scroll.grid_remove()
        else:
            self.h_scroll.grid()
    
    def undo(self):
        """Undo last action."""
        try:
            self.text.edit_undo()
        except tk.TclError:
            pass
    
    def redo(self):
        """Redo last undone action."""
        try:
            self.text.edit_redo()
        except tk.TclError:
            pass
    
    def cut(self):
        """Cut selection to clipboard."""
        self.text.event_generate('<<Cut>>')
    
    def copy(self):
        """Copy selection to clipboard."""
        self.text.event_generate('<<Copy>>')
    
    def paste(self):
        """Paste from clipboard."""
        self.text.event_generate('<<Paste>>')
    
    def select_all(self):
        """Select all text."""
        self.text.tag_add('sel', '1.0', 'end')
    
    def mark_saved(self):
        """Mark the file as saved."""
        self.modified = False
        self.text.edit_modified(False)
    
    def destroy(self):
        """Clean up resources."""
        if hasattr(self, 'autocomplete'):
            self.autocomplete.destroy()
        super().destroy()

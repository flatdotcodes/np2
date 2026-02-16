"""
Main application window for NP2 editor.
Assembles all components into the complete editor interface.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from editor.tab_manager import TabManager
from panels.find_replace import FindReplaceDialog
from panels.workspace import WorkspacePanel
from panels.bottom_panel import BottomPanel
from panels.settings_dialog import SettingsDialog
from linting.linter import Linter
from utils.language_detect import SUPPORTED_LANGUAGES
from utils.language_detect import SUPPORTED_LANGUAGES
from utils.file_utils import get_recent_files
from utils.settings import SettingsManager


class NP2App:
    """Main application class for NP2 text editor."""
    
    def __init__(self, root):
        """
        Initialize the application.
        
        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title('NP2 - Text Editor')
        self.root.geometry('1200x800')
        self.root.minsize(800, 600)  # Minimum window size
        
        # State
        self.theme = 'dark'
        self.word_wrap = False
        self.show_workspace = True
        self.show_terminal = True
        
        # Initialize settings
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.settings

        # Setup
        self._setup_style()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_status_bar()  # Setup status bar before main area to ensure it's at bottom
        self._setup_main_area()
        self._setup_bindings()
        
        # Apply initial settings
        self._apply_settings()
        
        # Initialize dialogs
        self.find_dialog = FindReplaceDialog(self.root, None)
        
        # Load session or create initial tab
        if not self._load_session():
            self.tab_manager.new_tab()
        
        # Handle window close
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _setup_style(self):
        """Set up the application style - using default Tkinter appearance."""
        # Use default system theme, no custom colors
        pass
    
    def _setup_menu(self):
        """Set up the menu bar."""
        menubar = tk.Menu(self.root)
        self.root.configure(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=file_menu)
        
        file_menu.add_command(label='📄 New', accelerator='Ctrl+N', command=self._new_file)
        file_menu.add_command(label='📂 Open...', accelerator='Ctrl+O', command=self._open_file)
        file_menu.add_command(label='📁 Open Folder...', command=self._open_folder)
        file_menu.add_separator()
        file_menu.add_command(label='💾 Save', accelerator='Ctrl+S', command=self._save_file)
        file_menu.add_command(label='💾 Save As...', accelerator='Ctrl+Shift+S', command=self._save_file_as)
        file_menu.add_separator()
        file_menu.add_command(label='⚙ Preferences...', command=self._show_preferences)
        file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label='📋 Recent Files', menu=self.recent_menu)
        self._update_recent_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label='❌ Close Tab', accelerator='Ctrl+W', command=self._close_tab)
        file_menu.add_command(label='🚪 Exit', accelerator='Alt+F4', command=self._on_close)
        
        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Edit', menu=edit_menu)
        
        edit_menu.add_command(label='↩ Undo', accelerator='Ctrl+Z', command=self._undo)
        edit_menu.add_command(label='↪ Redo', accelerator='Ctrl+Y', command=self._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label='✂ Cut', accelerator='Ctrl+X', command=self._cut)
        edit_menu.add_command(label='📋 Copy', accelerator='Ctrl+C', command=self._copy)
        edit_menu.add_command(label='📋 Paste', accelerator='Ctrl+V', command=self._paste)
        edit_menu.add_separator()
        edit_menu.add_command(label='🔲 Select All', accelerator='Ctrl+A', command=self._select_all)
        self.linting_enabled = tk.BooleanVar(value=True)
        # Trace linting enabled to run linter immediately when enabled
        self.linting_enabled.trace_add('write', lambda *args: self._run_linter() if self.linting_enabled.get() else None)
        
        # Search menu
        search_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Search', menu=search_menu)
        
        search_menu.add_command(label='🔍 Find...', accelerator='Ctrl+F', command=self._find)
        search_menu.add_command(label='↔ Replace...', accelerator='Ctrl+H', command=self._replace)
        search_menu.add_separator()
        search_menu.add_command(label='📍 Go to Line...', accelerator='Ctrl+G', command=self._goto_line)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Tools', menu=tools_menu)
        
        tools_menu.add_command(label='⚡ Run Linter', accelerator='Ctrl+Shift+L', command=self._run_linter)
        tools_menu.add_separator()
        tools_menu.add_checkbutton(label='⚠️ Enable Auto-Linting', variable=self.linting_enabled)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='View', menu=view_menu)
        
        self.workspace_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label='📁 Workspace Panel', variable=self.workspace_var, 
                                   command=self._toggle_workspace)
        
        self.terminal_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label='⌨ Terminal Panel', variable=self.terminal_var,
                                   command=self._toggle_terminal, accelerator='Ctrl+`')
        
        view_menu.add_separator()
        
        self.wrap_var = tk.BooleanVar(value=False)
        view_menu.add_checkbutton(label='📏 Word Wrap', variable=self.wrap_var,
                                   command=self._toggle_word_wrap)
        
        self.occurrence_highlight_var = tk.BooleanVar(value=True)
        view_menu.add_checkbutton(label='🔍 Highlight Occurrences', variable=self.occurrence_highlight_var,
                                   command=self._toggle_occurrence_highlight)
        

        

        
        # Language menu - using radiobuttons to show current selection
        self.lang_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Language', menu=self.lang_menu)
        
        self.current_lang_var = tk.StringVar(value='text')
        for lang in sorted(SUPPORTED_LANGUAGES):
            self.lang_menu.add_radiobutton(
                label=lang.title(), 
                variable=self.current_lang_var,
                value=lang,
                command=lambda l=lang: self._set_language(l)
            )
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=help_menu)
        
        help_menu.add_command(label='ℹ About', command=self._show_about)
    
    def _setup_toolbar(self):
        """Set up the toolbar."""
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # File buttons
        ttk.Button(toolbar, text='📄 New', width=10, command=self._new_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='📂 Open', width=10, command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='💾 Save', width=10, command=self._save_file).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Edit buttons
        ttk.Button(toolbar, text='↩ Undo', width=10, command=self._undo).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='↪ Redo', width=10, command=self._redo).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Search buttons
        ttk.Button(toolbar, text='🔍 Find', width=10, command=self._find).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text='↔ Replace', width=10, command=self._replace).pack(side=tk.LEFT, padx=2)
    
    def _setup_main_area(self):
        """Set up the main editing area."""
        # Main paned window (horizontal: workspace | editor/terminal)
        self.main_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.main_pane.pack(fill=tk.BOTH, expand=True)
        
        # Workspace panel (left) - with frame wrapper for minsize
        self.workspace_frame = ttk.Frame(self.main_pane, width=200)
        self.workspace_frame.pack_propagate(False)  # Maintain minimum width
        self.workspace = WorkspacePanel(
            self.workspace_frame, 
            on_file_open=self._open_file_path,
            on_folder_select=self._on_folder_select
        )
        self.workspace.pack(fill=tk.BOTH, expand=True)
        self.main_pane.add(self.workspace_frame, weight=1)
        
        # Right pane (editor + bottom panel)
        self.right_pane = ttk.PanedWindow(self.main_pane, orient=tk.VERTICAL)
        self.main_pane.add(self.right_pane, weight=4)
        
        # Tab manager / editor
        self.tab_manager = TabManager(self.right_pane)
        self.right_pane.add(self.tab_manager, weight=3)
        
        # Bottom panel (terminal + problems) - no frame wrapper needed
        self.bottom_panel = BottomPanel(self.right_pane, on_problem_click=self._on_goto_line)
        self.right_pane.add(self.bottom_panel, weight=1)
        
        # Initialize linter
        self.linter = Linter(on_results=self._on_lint_results)
        
        # Bind tab change event
        self.tab_manager.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = ttk.Frame(self.root)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Left: file info
        self.status_file = ttk.Label(self.status_bar, text='Ready')
        self.status_file.pack(side=tk.LEFT, padx=10)
        
        # Right: cursor position
        self.status_pos = ttk.Label(self.status_bar, text='Ln 1, Col 1')
        self.status_pos.pack(side=tk.RIGHT, padx=10)
        
        # Language selector
        self.status_lang = ttk.Label(self.status_bar, text='Plain Text')
        self.status_lang.pack(side=tk.RIGHT, padx=10)
        
        # Encoding
        self.status_encoding = ttk.Label(self.status_bar, text='UTF-8')
        self.status_encoding.pack(side=tk.RIGHT, padx=10)
    
    def _setup_bindings(self):
        """Set up keyboard bindings."""
        self.root.bind('<Control-n>', lambda e: self._new_file())
        self.root.bind('<Control-o>', lambda e: self._open_file())
        self.root.bind('<Control-s>', lambda e: self._save_file())
        self.root.bind('<Control-Shift-S>', lambda e: self._save_file_as())
        self.root.bind('<Control-w>', lambda e: self._close_tab())
        
        self.root.bind('<Control-z>', lambda e: self._undo())
        self.root.bind('<Control-y>', lambda e: self._redo())
        
        self.root.bind('<Control-f>', lambda e: self._find())
        self.root.bind('<Control-h>', lambda e: self._replace())
        self.root.bind('<Control-g>', lambda e: self._goto_line())
        
        self.root.bind('<Control-grave>', lambda e: self._toggle_terminal_shortcut())
        self.root.bind('<Control-Shift-L>', lambda e: self._run_linter())
        
        # Occurrence navigation
        self.root.bind('<F3>', lambda e: self._next_occurrence())
        self.root.bind('<Shift-F3>', lambda e: self._prev_occurrence())
        
        # Update status bar on cursor movement
        self.root.bind_all('<KeyRelease>', self._on_global_key_release)
        self.root.bind_all('<ButtonRelease-1>', self._update_status)
        
        # Auto-save bindings
        self.tab_manager.bind('<<FileModified>>', self._on_file_modified)
    
    # File operations
    def _new_file(self):
        """Create a new file."""
        self.tab_manager.new_tab()
    
    def _open_file(self):
        """Open a file dialog."""
        filepath = filedialog.askopenfilename(
            filetypes=[
                ('All Files', '*.*'),
                ('Python', '*.py'),
                ('JavaScript', '*.js'),
                ('HTML', '*.html'),
                ('Text', '*.txt'),
            ]
        )
        
        if filepath:
            self._open_file_path(filepath)
    
    def _open_file_path(self, filepath):
        """Open a specific file."""
        # Check if already open
        for tab_id in self.tab_manager.tabs():
            editor = self.tab_manager.editors.get(tab_id)
            if editor and editor.filepath == filepath:
                self.tab_manager.select(tab_id)
                return
        
        self.tab_manager.new_tab(filepath)
        self._update_recent_menu()
        
        # Auto-lint on open
        if self.linting_enabled.get():
            self._run_linter()
    
    def _open_folder(self):
        """Open folder in workspace."""
        path = filedialog.askdirectory()
        if path:
            self.workspace.open_folder(path)
        if path:
            self.workspace.open_folder(path)
            # Terminal sync is now handled by workspace auto-selection of root node
    
    def _save_file(self):
        """Save current file."""
        if self.tab_manager.save_tab():
            self._update_recent_menu()
            # Auto-lint on save
            if self.linting_enabled.get():
                self._run_linter()
    
    def _save_file_as(self):
        """Save current file with new name."""
        self.tab_manager.save_tab_as()
        self._update_recent_menu()
    
    def _close_tab(self):
        """Close current tab."""
        self.tab_manager.close_tab()
    
    def _update_recent_menu(self):
        """Update recent files menu."""
        self.recent_menu.delete(0, tk.END)
        
        for filepath in get_recent_files():
            name = os.path.basename(filepath)
            self.recent_menu.add_command(
                label=f'📄 {name}',
                command=lambda f=filepath: self._open_file_path(f)
            )
    
    # Edit operations
    def _undo(self):
        """Undo."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.undo()
    
    def _redo(self):
        """Redo."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.redo()
    
    def _cut(self):
        """Cut."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.cut()
    
    def _copy(self):
        """Copy."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.copy()
    
    def _paste(self):
        """Paste."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.paste()
    
    def _select_all(self):
        """Select all."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.select_all()
    
    # Search operations
    def _find(self):
        """Show find dialog."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            self.find_dialog.editor = editor
            self.find_dialog.show(replace_mode=False)
    
    def _replace(self):
        """Show replace dialog."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            self.find_dialog.editor = editor
            self.find_dialog.show(replace_mode=True)
    
    def _goto_line(self):
        """Show go to line dialog."""
        editor = self.tab_manager.get_current_editor()
        if not editor:
            return
        
        # Simple dialog
        dialog = tk.Toplevel(self.root)
        dialog.title('Go to Line')
        dialog.transient(self.root)
        dialog.resizable(False, False)
        
        frame = ttk.Frame(dialog, padding=10)
        frame.pack()
        
        ttk.Label(frame, text='📍 Line number:').pack(side=tk.LEFT)
        entry = ttk.Entry(frame, width=10)
        entry.pack(side=tk.LEFT, padx=5)
        entry.focus_set()
        
        def go():
            try:
                line = int(entry.get())
                editor.goto_line(line)
                dialog.destroy()
            except ValueError:
                pass
        
        ttk.Button(frame, text='Go', command=go).pack(side=tk.LEFT)
        entry.bind('<Return>', lambda e: go())
        dialog.bind('<Escape>', lambda e: dialog.destroy())
    
    # View operations
    def _toggle_workspace(self):
        """Toggle workspace panel visibility."""
        if self.workspace_var.get():
            # Add workspace frame back
            panes = list(self.main_pane.panes())
            if panes:
                self.main_pane.insert(0, self.workspace_frame, weight=1)
            else:
                self.main_pane.add(self.workspace_frame, weight=1)
        else:
            self.main_pane.forget(self.workspace_frame)
    
    def _toggle_terminal(self):
        """Update bottom panel visibility based on variable state."""
        # Called by menu checkbutton (variable already toggled)
        if self.terminal_var.get():
            self.right_pane.add(self.bottom_panel, weight=1)
            self.bottom_panel.focus_input()
        else:
            self.right_pane.forget(self.bottom_panel)
            
    def _toggle_terminal_shortcut(self):
        """Toggle bottom panel variable and update."""
        # Called by keyboard shortcut (toggle variable manually)
        self.terminal_var.set(not self.terminal_var.get())
        self._toggle_terminal()
    
    def _toggle_word_wrap(self):
        """Toggle word wrap."""
        self.word_wrap = self.wrap_var.get()
        
        for editor in self.tab_manager.get_all_editors():
            editor.set_word_wrap(self.word_wrap)
    
    def _toggle_occurrence_highlight(self):
        """Toggle occurrence highlighting feature."""
        enabled = self.occurrence_highlight_var.get()
        for editor in self.tab_manager.get_all_editors():
            editor.set_occurrence_highlight_enabled(enabled)
    
    def _next_occurrence(self):
        """Navigate to next occurrence."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.next_occurrence()
    
    def _prev_occurrence(self):
        """Navigate to previous occurrence."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.prev_occurrence()
    
    def _set_theme(self, theme):
        """Set color theme."""
        self.theme = theme
        
        for editor in self.tab_manager.get_all_editors():
            editor.set_theme(theme)
        
        # Re-setup style
        self._setup_style()
    
    def _set_language(self, language):
        """Set language for current editor."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            editor.set_language(language)
            editor.highlighter.highlight_all()  # Re-apply highlighting
            self.current_lang_var.set(language)  # Update menu checkmark
            self.status_lang.configure(text=language.title())
    
    # Linting
    def _run_linter(self):
        """Run linter on current file."""
        editor = self.tab_manager.get_current_editor()
        if not editor:
            return
        
        # Use temp file for linting to avoid auto-saving user's file
        if editor.filepath:
            # Create temp dir if needed
            temp_dir = os.path.join(os.path.expanduser('~'), '.np2', 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create temp file with same extension as original (to help linter)
            ext = os.path.splitext(editor.filepath)[1]
            temp_filename = f"lint_temp_{os.path.basename(editor.filepath)}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            try:
                # Write current content to temp file
                with open(temp_path, 'w', encoding=editor.encoding) as f:
                    f.write(editor.get_content())
                
                # Store ORIGINAL filepath for callback (so markers are applied to editor)
                self._lint_filepath = editor.filepath
                
                # Run linter on temp file, but with ORIGINAL CWD (for imports)
                self.linter.lint_file(
                    temp_path, 
                    editor.language, 
                    cwd=os.path.dirname(editor.filepath)
                )
                
                # Show feedback
                self.status_file.configure(text=f'Linting {os.path.basename(editor.filepath)}...')
                
            except Exception as e:
                print(f"Lint error: {e}")
        else:
             # Can't lint untitled files easily (no import context)
             pass
    
    def _on_lint_results(self, errors):
        """Handle lint results callback."""
        filepath = getattr(self, '_lint_filepath', None)
        self.bottom_panel.show_lint_results(errors, filepath)
        
        # Update editor dots
        editor = self.tab_manager.get_current_editor()
        if editor and editor.filepath == filepath:
            markers = {}
            for error in errors:
                # Color code based on severity
                color = 'red' if error.severity == 'error' else ('orange' if error.severity == 'warning' else 'blue')
                # Only set if not already set (keep highest severity if multiple)
                if error.line not in markers:
                    markers[error.line] = color
                elif markers[error.line] != 'red' and color == 'red':
                    markers[error.line] = color
            
            editor.set_lint_markers(markers)
        
        # Update status
        count = len(errors)
        if count == 0:
            self.status_file.configure(text='No problems found')
        else:
            self.status_file.configure(text=f'{count} problem(s) found')
            
    def _on_global_key_release(self, event=None):
        """Handle global key release."""
        self._update_status(event)
        self._start_lint_timer()
        
    def _start_lint_timer(self, event=None):
        """Start auto-lint timer."""
        if not self.linting_enabled.get():
            return
            
        if hasattr(self, '_lint_timer') and self._lint_timer:
            self.root.after_cancel(self._lint_timer)
            
        self._lint_timer = self.root.after(1000, self._auto_lint)
        
    def _auto_lint(self):
        """Run linter automatically."""
        # Only if configured and editor exists
        editor = self.tab_manager.get_current_editor()
        if editor and editor.filepath: # Must be saved file to lint
             # Check if editor has focus (don't interrupt terminal)
             focus = self.root.focus_get()
             if focus == editor.text:
                 self._run_linter()
    
    def _on_goto_line(self, line):
        """Handle go to line from problems panel."""
        try:
            line_num = int(line)
            editor = self.tab_manager.get_current_editor()
            if editor:
                editor.goto_line(line_num)
        except Exception:
            pass
    
    # Events
    def _on_tab_changed(self, event=None):
        """Handle tab change."""
        editor = self.tab_manager.get_current_editor()
        if editor:
            self.find_dialog.set_editor(editor)
            self.current_lang_var.set(editor.language)  # Sync language menu
            self._update_status()
            
            # Sync terminal if enabled
            if self.settings.terminal_follow and editor.filepath:
                self.bottom_panel.set_working_directory(os.path.dirname(editor.filepath))
    
    def _update_status(self, event=None):
        """Update status bar."""
        editor = self.tab_manager.get_current_editor()
        if not editor:
            return
        
        # Position
        line, col = editor.get_cursor_position()
        self.status_pos.configure(text=f'Ln {line}, Col {col + 1}')
        
        # Language
        self.status_lang.configure(text=editor.language.title())
        
        # Encoding
        self.status_encoding.configure(text=editor.encoding.upper())
        
        # File info
        if editor.filepath:
            name = os.path.basename(editor.filepath)
            self.status_file.configure(text=name)
        else:
            self.status_file.configure(text='Untitled')
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            'About NP2',
            'NP2 - Text Editor\n\n'
            'A Notepad++ inspired editor built with Python and Tkinter.\n\n'
            'Features:\n'
            '• Tabs for multiple files\n'
            '• Syntax highlighting (50+ languages)\n'
            '• Find and Replace\n'
            '• Text prediction\n'
            '• Workspace panel\n'
            '• Integrated terminal\n'
            '• Linting support'
        )
    
    def _on_close(self):
        """Handle window close event."""
        # Save bounds
        self.settings_manager.set('window_geometry', self.root.geometry())
        
        # Save session (persists drafts)
        self._save_session()
        
        # Directly destroy without prompting for individual tabs
        # Session persistence handles the data safety.
        self.root.destroy()
            
    def _show_preferences(self):
        """Show preferences dialog."""
        dialog = SettingsDialog(self.root, self.settings_manager)
        self.root.wait_window(dialog)
        
        if dialog.result:
             self._apply_settings()
             
    def _on_folder_select(self, path):
        """Handle folder selection to sync terminal."""
        if self.settings.terminal_follow:
            self.bottom_panel.set_working_directory(path)
            
    def _on_file_modified(self, event=None):
        """Handle file modification for auto-save."""
        if self.settings.autosave_mode.lower() == 'change':
            # Save current tab if modified
            editor = self.tab_manager.get_current_editor()
            if editor and editor.filepath and editor.modified:
                self.tab_manager.save_tab()
                
    def _start_autosave_timer(self):
        """Start auto-save timer."""
        # Cancel existing timer
        if hasattr(self, '_autosave_timer') and self._autosave_timer:
            self.root.after_cancel(self._autosave_timer)
            self._autosave_timer = None
            
        mode = self.settings.autosave_mode.lower()
        if mode == 'interval':
            try:
                interval_ms = int(self.settings.autosave_interval) * 1000
                if interval_ms > 0:
                    self._autosave_timer = self.root.after(interval_ms, self._check_autosave)
            except (ValueError, TypeError):
                pass # Invalid interval
            
    def _check_autosave(self):
        """Check and perform auto-save."""
        if self.settings.autosave_mode.lower() == 'interval':
            # Save all modified files that have a path
            for tab_id in self.tab_manager.tabs():
                editor = self.tab_manager.editors.get(tab_id)
                if editor and editor.filepath and editor.modified:
                    self.tab_manager.save_tab(tab_id)
            
            # Restart timer
            self._start_autosave_timer()

    def _save_session(self):
        """Save current session."""
        open_files = self.tab_manager.get_session_data()
        active_index = self.tab_manager.index(self.tab_manager.select()) if self.tab_manager.tabs() else 0
        self.settings_manager.save_session(open_files, active_index)
        
    def _load_session(self):
        """Load session."""
        session = self.settings_manager.load_session()
        if session:
            try:
                active_index = session.get('active_index', 0)
                files = session.get('files', [])
                if files:
                    self.tab_manager.restore_session(files)
                    if 0 <= active_index < len(self.tab_manager.tabs()):
                        self.tab_manager.select(active_index)
                    return True
            except Exception as e:
                print(f"Error restoring session: {e}")
        return False
        
    def _apply_settings(self):
        """Apply loaded settings."""
        self.theme = self.settings.theme
        self.word_wrap = self.settings.word_wrap
        self.wrap_var.set(self.settings.word_wrap)
        self.show_workspace = self.settings.show_workspace
        self.workspace_var.set(self.settings.show_workspace)
        self.show_terminal = self.settings.show_terminal
        self.terminal_var.set(self.settings.show_terminal)
        self.root.geometry(self.settings.window_geometry)
        
        self.occurrence_highlight_var.set(self.settings.highlight_occurrences)
        
        # Update all editors
        if hasattr(self, 'tab_manager'):
            for tab_id in self.tab_manager.tabs():
                editor = self.tab_manager.editors.get(tab_id)
                if editor:
                    editor.set_word_wrap(self.settings.word_wrap)
                    editor.set_highlight_occurrences(self.settings.highlight_occurrences)
                    # Theme is handled by _set_theme below
        
        # Toggle panels based on settings
        if not self.show_workspace:
             self.main_pane.forget(self.workspace_frame)
        if not self.show_terminal:
             self.right_pane.forget(self.bottom_panel)
             
        # Apply Logic Settings
        self._start_autosave_timer()
        
        # Apply theme
        self._set_theme(self.theme)
        
        # Re-apply tab styles as theme change might reset them
        if hasattr(self, 'tab_manager'):
            self.tab_manager.setup_style()


def main():
    """Application entry point."""
    root = tk.Tk()
    app = NP2App(root)
    root.mainloop()


if __name__ == '__main__':
    main()

"""
Bottom panel with tabs for Terminal and Problems (linter output).
"""

import os
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk


class BottomPanel(ttk.Frame):
    """Tabbed bottom panel with Terminal and Problems tabs."""
    
    def __init__(self, parent, on_problem_click=None, **kwargs):
        """
        Initialize the bottom panel.
        
        Args:
            parent: Parent widget
            on_problem_click: Callback when a problem is clicked (line: int)
        """
        super().__init__(parent, **kwargs)
        
        self.on_problem_click_callback = on_problem_click
        self.output_queue = queue.Queue()
        self.process = None
        self.working_dir = os.getcwd()
        self.command_history = []
        self.history_index = 0
        self.lint_errors = []
        
        self._setup_ui()
        self._start_update_loop()
    
    def _setup_ui(self):
        """Set up the UI."""
        # Header with tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # Terminal tab
        self.terminal_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.terminal_frame, text='Terminal')
        self._setup_terminal()
        
        # Problems tab
        self.problems_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.problems_frame, text='Problems (0)')
        self._setup_problems()
    
    def _setup_terminal(self):
        """Set up terminal tab."""
        # Input area at bottom (Pack FIRST to ensure visibility)
        input_frame = ttk.Frame(self.terminal_frame)
        input_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        
        self.prompt_label = ttk.Label(input_frame, text='> ', font=('Consolas', 10))
        self.prompt_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.input = tk.Entry(input_frame, font=('Consolas', 10), relief=tk.SUNKEN, bd=2)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=2)
        
        # Bind events
        self.input.bind('<Return>', self._on_enter)
        self.input.bind('<Up>', self._history_up)
        self.input.bind('<Down>', self._history_down)
        
        # Output area (Pack SECOND to take remaining space)
        output_container = ttk.Frame(self.terminal_frame)
        output_container.pack(fill=tk.BOTH, expand=True)
        
        self.output = tk.Text(
            output_container,
            wrap=tk.WORD,
            font=('Consolas', 10),
            padx=5,
            pady=5,
        )
        self.output.bind('<Button-1>', lambda e: self.input.focus_set())
        
        scrollbar = ttk.Scrollbar(output_container, orient=tk.VERTICAL, command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure output tags
        self.output.tag_configure('prompt', foreground='blue')
        self.output.tag_configure('command', foreground='#000080')
        self.output.tag_configure('error', foreground='red')
        self.output.tag_configure('success', foreground='green')
        
        # Bind events
        self.input.bind('<Return>', self._on_enter)
        self.input.bind('<Up>', self._history_up)
        self.input.bind('<Down>', self._history_down)
        
        # Welcome message
        self._append_output('NP2 Terminal - PowerShell\n', 'prompt')
        self._append_output(f'Working directory: {self.working_dir}\n\n', 'prompt')
    
    def _on_tab_changed(self, event):
        """Handle tab change."""
        # Focus input if terminal tab selected
        if self.notebook.select() == str(self.terminal_frame):
            self.input.focus_set()

    def _setup_problems(self):
        """Set up problems tab."""
        # Toolbar
        toolbar = ttk.Frame(self.problems_frame)
        toolbar.pack(fill=tk.X)
        
        ttk.Button(toolbar, text='Clear', command=self.clear_problems).pack(side=tk.RIGHT, padx=2, pady=2)
        
        # Problems list
        columns = ('severity', 'file', 'line', 'message')
        self.problems_tree = ttk.Treeview(self.problems_frame, columns=columns, show='headings')
        
        self.problems_tree.heading('severity', text='Type')
        self.problems_tree.heading('file', text='File')
        self.problems_tree.heading('line', text='Line')
        self.problems_tree.heading('message', text='Message')
        
        self.problems_tree.column('severity', width=60, stretch=False)
        self.problems_tree.column('file', width=150, stretch=False)
        self.problems_tree.column('line', width=50, stretch=False)
        self.problems_tree.column('message', width=400, stretch=True)
        
        scrollbar = ttk.Scrollbar(self.problems_frame, orient=tk.VERTICAL, command=self.problems_tree.yview)
        self.problems_tree.configure(yscrollcommand=scrollbar.set)
        
        self.problems_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection change to go to error (single click)
        self.problems_tree.bind('<<TreeviewSelect>>', self._on_problem_click)
    
    def _on_enter(self, event=None):
        """Handle Enter key to execute command."""
        command = self.input.get().strip()
        self.input.delete(0, tk.END)
        
        if not command:
            return
        
        # Add to history
        self.command_history.append(command)
        self.history_index = len(self.command_history)
        
        # Display command
        self._append_output(f'> {command}\n', 'command')
        
        # Handle built-in commands
        if command.lower() == 'clear' or command.lower() == 'cls':
            self.clear_terminal()
            return
        
        if command.lower().startswith('cd '):
            new_dir = command[3:].strip().strip('"\'')
            self._change_directory(new_dir)
            return
        
        # Execute command
        self._execute_command(command)
    
    def _change_directory(self, path):
        """Change working directory."""
        try:
            if not os.path.isabs(path):
                path = os.path.join(self.working_dir, path)
            
            path = os.path.abspath(path)
            
            if os.path.isdir(path):
                self.working_dir = path
                os.chdir(path)
                self.prompt_label.configure(text='> ')
                self._append_output(f'[Terminal] Changed directory to: {path}\n\n', 'success')
            else:
                self._append_output(f'Directory not found: {path}\n\n', 'error')
        except Exception as e:
            self._append_output(f'Error: {e}\n\n', 'error')
    
    def _execute_command(self, command):
        """Execute a shell command."""
        def run():
            try:
                full_command = f'powershell.exe -NoProfile -Command "cd \'{self.working_dir}\'; {command}"'
                
                self.process = subprocess.Popen(
                    full_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    text=True,
                    bufsize=1,
                    cwd=self.working_dir,
                )
                
                for line in self.process.stdout:
                    self.output_queue.put(('output', line))
                
                self.process.wait()
                
                if self.process.returncode != 0:
                    self.output_queue.put(('error', f'Exit code: {self.process.returncode}\n'))
                
                self.output_queue.put(('done', '\n'))
                
            except Exception as e:
                self.output_queue.put(('error', f'Error: {e}\n\n'))
            finally:
                self.process = None
        
        thread = threading.Thread(target=run, daemon=True)
        thread.start()
    
    def _start_update_loop(self):
        """Start the output update loop."""
        try:
            while True:
                msg_type, text = self.output_queue.get_nowait()
                
                if msg_type == 'error':
                    self._append_output(text, 'error')
                else:
                    self._append_output(text)
                    
        except queue.Empty:
            pass
        
        self.after(50, self._start_update_loop)
    
    def _append_output(self, text, tag=None):
        """Append text to output."""
        self.output.configure(state=tk.NORMAL)
        
        if tag:
            self.output.insert(tk.END, text, tag)
        else:
            self.output.insert(tk.END, text)
        
        self.output.see(tk.END)
        self.output.configure(state=tk.DISABLED)
    
    def _history_up(self, event=None):
        """Navigate command history up."""
        if self.command_history and self.history_index > 0:
            self.history_index -= 1
            self.input.delete(0, tk.END)
            self.input.insert(0, self.command_history[self.history_index])
        return 'break'
    
    def _history_down(self, event=None):
        """Navigate command history down."""
        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.input.delete(0, tk.END)
            self.input.insert(0, self.command_history[self.history_index])
        elif self.history_index == len(self.command_history) - 1:
            self.history_index = len(self.command_history)
            self.input.delete(0, tk.END)
        return 'break'
    
    def clear_terminal(self):
        """Clear the terminal output."""
        self.output.configure(state=tk.NORMAL)
        self.output.delete('1.0', tk.END)
        self.output.configure(state=tk.DISABLED)
    
    def kill_process(self):
        """Kill the current running process."""
        if self.process:
            try:
                self.process.terminate()
                self._append_output('\n[Process terminated]\n\n', 'error')
            except Exception:
                pass
    
    def focus_input(self):
        """Focus the input field."""
        self.input.focus_set()
        self.notebook.select(0)  # Switch to terminal tab
    
    # Problems methods
    def show_lint_results(self, errors, filepath=None):
        """
        Show lint results in problems tab.
        
        Args:
            errors: List of LintError objects
            filepath: Source file path
        """
        self.lint_errors = errors
        
        # Update tab label
        count = len(errors)
        self.notebook.tab(1, text=f'Problems ({count})')
        
        # Clear existing
        for item in self.problems_tree.get_children():
            self.problems_tree.delete(item)
        
        # Add errors
        filename = os.path.basename(filepath) if filepath else ''
        
        for error in errors:
            severity_icon = '❌' if error.severity == 'error' else ('⚠' if error.severity == 'warning' else 'ℹ')
            self.problems_tree.insert('', tk.END, values=(
                severity_icon,
                filename,
                error.line,
                f'[{error.code}] {error.message}' if error.code else error.message
            ), tags=(error.severity,))
        
        # Configure tags
        self.problems_tree.tag_configure('error', foreground='red')
        self.problems_tree.tag_configure('warning', foreground='orange')
        self.problems_tree.tag_configure('info', foreground='blue')
        
        # Switch to problems tab if there are errors
        if errors:
            self.notebook.select(1)
    
    def clear_problems(self):
        """Clear all problems."""
        for item in self.problems_tree.get_children():
            self.problems_tree.delete(item)
        self.lint_errors = []
        self.notebook.tab(1, text='Problems (0)')
    
    def _on_problem_click(self, event):
        """Handle click on problem to navigate to it."""
        selection = self.problems_tree.selection()
        if selection:
            item = self.problems_tree.item(selection[0])
            values = item['values']
            if len(values) >= 3:
                line = values[2]
                # Call callback directly
                if self.on_problem_click_callback:
                    self.on_problem_click_callback(line)
    
    def set_working_directory(self, path):
        """Set the working directory."""
        if os.path.isfile(path):
            path = os.path.dirname(path)
            
        # Ignore if already in this directory
        if hasattr(self, 'working_dir') and os.path.abspath(path) == os.path.abspath(self.working_dir):
            return
        
        if os.path.isdir(path):
            # Normalize path for Windows
            path = path.replace('/', '\\')
            self._change_directory(path)
            # Send empty command to refresh prompt
            self.run_command("")
    
    def run_command(self, command):
        """Run a command programmatically."""
        self.input.delete(0, tk.END)
        self.input.insert(0, command)
        self._on_enter()

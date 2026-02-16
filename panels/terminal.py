"""
Integrated terminal panel for NP2 editor.
Provides a command-line interface within the editor.
"""

import os
import subprocess
import threading
import queue
import tkinter as tk
from tkinter import ttk


class TerminalPanel(ttk.Frame):
    """Integrated terminal panel."""
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the terminal panel.
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent, **kwargs)
        
        self.process = None
        self.output_queue = queue.Queue()
        self.working_dir = os.getcwd()
        self.command_history = []
        self.history_index = 0
        
        self._setup_ui()
        self._start_update_loop()
    
    def _setup_ui(self):
        """Set up the UI."""
        # Header
        header = ttk.Frame(self)
        header.pack(fill=tk.X)
        
        ttk.Label(header, text='⌨ TERMINAL', font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT, padx=5, pady=3)
        
        ttk.Button(
            header, 
            text='🗑 Clear', 
            width=8,
            command=self.clear
        ).pack(side=tk.RIGHT, padx=2)
        
        ttk.Button(
            header, 
            text='⚡ Kill', 
            width=8,
            command=self.kill_process
        ).pack(side=tk.RIGHT, padx=2)
        
        # Output area
        output_frame = ttk.Frame(self)
        output_frame.pack(fill=tk.BOTH, expand=True)
        
        self.output = tk.Text(
            output_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            state=tk.DISABLED,
            padx=5,
            pady=5,
        )
        
        scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output.yview)
        self.output.configure(yscrollcommand=scrollbar.set)
        
        self.output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Configure output tags
        self.output.tag_configure('prompt', foreground='blue')
        self.output.tag_configure('command', foreground='#000080')
        self.output.tag_configure('error', foreground='red')
        self.output.tag_configure('success', foreground='green')
        
        # Input area
        input_frame = ttk.Frame(self)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.prompt_label = ttk.Label(input_frame, text='>', font=('Consolas', 10))
        self.prompt_label.pack(side=tk.LEFT, padx=(5, 0))
        
        self.input = tk.Entry(input_frame, font=('Consolas', 10), relief=tk.SUNKEN, bd=2)
        self.input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=3)
        
        # Bind events
        self.input.bind('<Return>', self._on_enter)
        self.input.bind('<Up>', self._history_up)
        self.input.bind('<Down>', self._history_down)
        
        # Welcome message
        self._append_output('NP2 Terminal - PowerShell\n', 'prompt')
        self._append_output(f'Working directory: {self.working_dir}\n\n', 'prompt')
    
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
            self.clear()
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
            # Handle relative paths
            if not os.path.isabs(path):
                path = os.path.join(self.working_dir, path)
            
            path = os.path.abspath(path)
            
            if os.path.isdir(path):
                self.working_dir = path
                os.chdir(path)
                self._append_output(f'Changed to: {path}\n\n', 'success')
            else:
                self._append_output(f'Directory not found: {path}\n\n', 'error')
        except Exception as e:
            self._append_output(f'Error: {e}\n\n', 'error')
    
    def _execute_command(self, command):
        """Execute a shell command."""
        def run():
            try:
                # Use PowerShell on Windows
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
                
                # Read output
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
        
        # Run in background thread
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
        
        # Schedule next update
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
    
    def clear(self):
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
    
    def set_working_directory(self, path):
        """
        Set the working directory.
        
        Args:
            path: Directory path
        """
        if os.path.isfile(path):
            path = os.path.dirname(path)
        
        if os.path.isdir(path):
            self._change_directory(path)
    
    def run_command(self, command):
        """
        Run a command programmatically.
        
        Args:
            command: Command to run
        """
        self.input.delete(0, tk.END)
        self.input.insert(0, command)
        self._on_enter()
    
    def focus_input(self):
        """Focus the input field."""
        self.input.focus_set()

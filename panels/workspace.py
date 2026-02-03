"""
Workspace/folder panel for NP2 editor.
Provides a tree view for navigating folder contents.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog


class WorkspacePanel(ttk.Frame):
    """Workspace folder tree panel."""
    
    def __init__(self, parent, on_file_open=None, on_folder_select=None, **kwargs):
        """
        Initialize the workspace panel.
        
        Args:
            parent: Parent widget
            on_file_open: Callback when file is opened (filepath)
            on_folder_select: Callback when folder is selected (path)
        """
        super().__init__(parent, **kwargs)
        
        self.on_file_open = on_file_open
        self.on_folder_select = on_folder_select
        self.current_folder = None
        self.nodes = {}  # node_id -> path
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the UI."""
        # Header frame
        header = ttk.Frame(self)
        header.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(header, text='📁 WORKSPACE', font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        
        ttk.Button(
            header, 
            text='📂 Open Folder', 
            command=self.open_folder
        ).pack(side=tk.RIGHT)
        
        # Tree view with scrollbar
        tree_frame = ttk.Frame(self)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tree = ttk.Treeview(tree_frame, selectmode='browse', show='tree')
        
        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind events
        self.tree.bind('<Double-1>', self._on_double_click)
        self.tree.bind('<<TreeviewOpen>>', self._on_expand)
        self.tree.bind('<<TreeviewSelect>>', self._on_select)
        self.tree.bind('<Button-3>', self._on_right_click)
    
    def _on_select(self, event):
        """Handle tree selection."""
        if not self.on_folder_select:
            return
            
        selection = self.tree.selection()
        if not selection:
            return
            
        node_id = selection[0]
        path = self.nodes.get(node_id)
        
        if path and os.path.isdir(path):
            self.on_folder_select(path)
    
    def open_folder(self, folder_path=None):
        """
        Open a folder in the workspace.
        
        Args:
            folder_path: Path to folder, or None to show dialog
        """
        if folder_path is None:
            folder_path = filedialog.askdirectory(title='Open Folder')
        
        if not folder_path or not os.path.isdir(folder_path):
            return
        
        self.current_folder = folder_path
        
        # Clear tree
        self.tree.delete(*self.tree.get_children())
        self.nodes.clear()
        
        # Add root node
        folder_name = os.path.basename(folder_path) or folder_path
        root_id = self.tree.insert('', 'end', text=f'📁 {folder_name}', open=True)
        self.nodes[root_id] = folder_path
        
        # Load contents
        self._load_children(root_id, folder_path)
        
        # Select root node automatically (triggers terminal sync)
        self.tree.selection_set(root_id)
        # Manually trigger on_select because standard selection_set doesn't always trigger event
        if self.on_folder_select:
             self.on_folder_select(folder_path)
    
    def _load_children(self, parent_id, path):
        """
        Load children of a folder.
        
        Args:
            parent_id: Parent tree node ID
            path: Folder path
        """
        try:
            items = os.listdir(path)
            items.sort(key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
            
            for item in items:
                # Skip hidden files/folders
                if item.startswith('.'):
                    continue
                
                item_path = os.path.join(path, item)
                
                if os.path.isdir(item_path):
                    # Folder
                    node_id = self.tree.insert(parent_id, 'end', text=f'📁 {item}')
                    self.nodes[node_id] = item_path
                    
                    # Add placeholder for expansion
                    if self._has_children(item_path):
                        self.tree.insert(node_id, 'end', text='Loading...')
                else:
                    # File
                    icon = self._get_file_icon(item)
                    node_id = self.tree.insert(parent_id, 'end', text=f'{icon} {item}')
                    self.nodes[node_id] = item_path
        except PermissionError:
            self.tree.insert(parent_id, 'end', text='⚠ Permission denied')
        except Exception as e:
            self.tree.insert(parent_id, 'end', text=f'⚠ Error: {str(e)[:30]}')
    
    def _has_children(self, path):
        """Check if folder has visible children."""
        try:
            for item in os.listdir(path):
                if not item.startswith('.'):
                    return True
        except Exception:
            pass
        return False
    
    def _get_file_icon(self, filename):
        """Get icon for file type."""
        ext = os.path.splitext(filename)[1].lower()
        
        icon_map = {
            '.py': '🐍',
            '.js': '📜',
            '.ts': '📘',
            '.html': '🌐',
            '.css': '🎨',
            '.json': '📋',
            '.xml': '📄',
            '.md': '📝',
            '.txt': '📄',
            '.yaml': '⚙',
            '.yml': '⚙',
            '.toml': '⚙',
            '.ini': '⚙',
            '.cfg': '⚙',
            '.sh': '⌨',
            '.bat': '⌨',
            '.ps1': '⌨',
            '.c': '©',
            '.cpp': '©',
            '.h': '©',
            '.java': '☕',
            '.go': '🔷',
            '.rs': '🦀',
            '.rb': '💎',
            '.php': '🐘',
            '.sql': '🗃',
            '.png': '🖼',
            '.jpg': '🖼',
            '.jpeg': '🖼',
            '.gif': '🖼',
            '.svg': '🖼',
            '.ico': '🖼',
        }
        
        return icon_map.get(ext, '📄')
    
    def _on_double_click(self, event):
        """Handle double-click to open file."""
        selection = self.tree.selection()
        if not selection:
            return
        
        node_id = selection[0]
        path = self.nodes.get(node_id)
        
        if path and os.path.isfile(path):
            if self.on_file_open:
                self.on_file_open(path)
    
    def _on_expand(self, event):
        """Handle tree node expansion."""
        selection = self.tree.selection()
        if not selection:
            return
        
        node_id = selection[0]
        path = self.nodes.get(node_id)
        
        if path and os.path.isdir(path):
            # Check if this is a lazy load
            children = self.tree.get_children(node_id)
            if len(children) == 1:
                first_child = self.tree.item(children[0])
                if first_child['text'] == 'Loading...':
                    # Remove placeholder and load real children
                    self.tree.delete(children[0])
                    self._load_children(node_id, path)
    
    def _on_right_click(self, event):
        """Handle right-click for context menu."""
        # Select item under cursor
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            path = self.nodes.get(item)
            
            if path:
                menu = tk.Menu(self, tearoff=0)
                
                if os.path.isfile(path):
                    menu.add_command(
                        label='📄 Open', 
                        command=lambda: self.on_file_open(path) if self.on_file_open else None
                    )
                    menu.add_separator()
                
                menu.add_command(
                    label='📁 Open in Explorer', 
                    command=lambda: self._open_in_explorer(path)
                )
                menu.add_command(
                    label='📋 Copy Path', 
                    command=lambda: self._copy_path(path)
                )
                menu.add_separator()
                menu.add_command(
                    label='🔄 Refresh', 
                    command=self._refresh_current
                )
                
                menu.tk_popup(event.x_root, event.y_root)
    
    def _open_in_explorer(self, path):
        """Open path in file explorer."""
        import subprocess
        
        if os.path.isfile(path):
            path = os.path.dirname(path)
        
        subprocess.run(['explorer', path])
    
    def _copy_path(self, path):
        """Copy path to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(path)
    
    def _refresh_current(self):
        """Refresh the current folder."""
        if self.current_folder:
            self.open_folder(self.current_folder)
    
    def refresh(self):
        """Refresh the workspace."""
        self._refresh_current()

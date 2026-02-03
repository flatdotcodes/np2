import tkinter as tk
from tkinter import ttk

class TabManager(ttk.Notebook):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.images = {}
        self.editors = {}
        self.setup_style()
        self.pack(fill=tk.BOTH, expand=True)

    def setup_style(self):
        style = ttk.Style()
        
        # Black square 10x10 GIF
        self.images['close'] = tk.PhotoImage(name='img_close', data='''
            R0lGODlhCgAKAAAAMAAAAAAAAP///wAAACH5BAEAAAAALAAAAAAKAAoAAAIRhI+py+0Po5y02ouz3rz7rxQAOw==
        ''')
        self.images['close_active'] = tk.PhotoImage(name='img_close_active', data='''
            R0lGODlhCgAKAAAAMAAAAAAAAP///wAAACH5BAEAAAAALAAAAAAKAAoAAAIRhI+py+0Po5y02ouz3rz7rxQAOw==
        ''') 
        
        try:
            # Layout
            style.layout("TNotebook.Tab", [
                ("Notebook.tab", {
                    "sticky": "nswe", 
                    "children": [
                        ("Notebook.padding", {
                            "side": "top", 
                            "sticky": "nswe",
                            "children": [
                                ("Notebook.focus", {
                                    "side": "top", 
                                    "sticky": "nswe",
                                    "children": [
                                        ("Notebook.label", {"side": "left", "sticky": ""}),
                                        ("Notebook.close", {"side": "left", "sticky": ""}),
                                    ]
                                })
                            ]
                        })
                    ]
                })
            ])
            
            # Use object
            style.element_create("close", "image", self.images['close'],
                ("active", self.images['close_active']), border=0, sticky='')
        except tk.TclError as e:
            print(f"Error: {e}")

root = tk.Tk()
root.geometry("400x300")
root.title("Tab Visual Test")

tabs = TabManager(root)
f1 = tk.Frame(tabs, bg='red')
f2 = tk.Frame(tabs, bg='blue')
tabs.add(f1, text="Tab 1")
tabs.add(f2, text="Tab 2")

root.mainloop()

import tkinter as tk
from tkinter import ttk

root = tk.Tk()
style = ttk.Style()

print("Initial Layout:", style.layout("TNotebook.Tab"))

try:
    # 1. Image
    img = tk.PhotoImage(data='''
        R0lGODlhDAAMAIABAAAAAP///yH5BAEAAAEALAAAAAAMAAwAAAIgjI+py+0Po5y02ouz3rz7D4biSJbmiabqyrbuC8fyTNf6DwA7
    ''')
    
    # 2. Element
    try:
        style.element_create("close", "image", img, border=8, sticky='')
        print("Element created successfully")
    except Exception as e:
        print("Element creation failed/exists:", e)
        
    # 3. Layout - INTENTIONAL ERROR TEST (empty)
    # style.layout("TNotebook.Tab", [])
    
    # 4. Layout - Proposed
    layout_def = [
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
    ]
    style.layout("TNotebook.Tab", layout_def)
    print("Layout applied successfully")
    
except Exception as e:
    print("Layout application failed:", e)

print("Final Layout:", style.layout("TNotebook.Tab"))
root.destroy()

import tkinter as tk
from tkinter import ttk

root = tk.Tk()
style = ttk.Style()

print("Current Tab Layout:")
print(style.layout("Tab"))

# helper to see if element exists
try:
    print("\nElement 'close' exists:", style.element_options('close'))
except Exception as e:
    print("\nElement 'close' error:", e)

root.destroy()

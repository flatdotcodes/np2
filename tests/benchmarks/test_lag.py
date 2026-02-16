import tkinter as tk
import time

def load_file():
    with open(r'c:\Users\ben\Dev\np2\test_files\model (1).bbmodel', 'r', encoding='utf-8') as f:
        content = f.read()
    text.insert('1.0', content)
    print(f"Loaded {len(content)} chars")

root = tk.Tk()
text = tk.Text(root, wrap='word', font=('Consolas', 11))
text.pack(fill='both', expand=True)

load_file()

root.mainloop()

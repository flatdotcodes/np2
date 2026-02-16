import tkinter as tk
import time
import random

def load_file():
    # Generate 18k line if file not found
    try:
        with open(r'c:\Users\ben\Dev\np2\test_files\model (1).bbmodel', 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        content = 'a' * 20000

    text.insert('1.0', content)
    print(f"Loaded {len(content)} chars")

def benchmark_typing():
    start = time.time()
    for i in range(100):
        text.insert('insert', 'x')
        text.update_idletasks() # Force redraw
    end = time.time()
    print(f"Typing 100 chars took: {(end-start)*1000:.2f} ms")
    root.quit()

root = tk.Tk()
text = tk.Text(root, wrap='none', font=('Consolas', 11), undo=True, maxundo=-1)
text.pack(fill='both', expand=True)

root.after(1000, load_file)
root.after(2000, benchmark_typing)

root.mainloop()

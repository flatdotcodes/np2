import tkinter as tk
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from editor.text_editor import TextEditor

def load_file():
    try:
        with open(r'c:\Users\ben\Dev\np2\test_files\model (1).bbmodel', 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        content = 'a' * 20000
    
    editor.set_content(content, filepath='test.bbmodel')
    print(f"Loaded {len(content)} chars")

def benchmark_scroll():
    print("Testing horizontal scroll...")
    start = time.time()
    
    # Simulate scrolling to end of line
    for i in range(20):
        editor.text.xview_scroll(10, 'units')
        editor.update_idletasks()
        
    elapsed = (time.time() - start) * 1000
    print(f"20 scroll operations took: {elapsed:.2f} ms ({elapsed/20:.2f} ms/scroll)")
    root.quit()

root = tk.Tk()
editor = TextEditor(root)
editor.pack(fill='both', expand=True)
editor.set_word_wrap(False)
editor.set_highlight_occurrences(False)

root.after(500, load_file)
root.after(1500, benchmark_scroll)

root.mainloop()

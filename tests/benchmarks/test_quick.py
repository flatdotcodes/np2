import tkinter as tk
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from editor.text_editor import TextEditor

def load_file():
    # Load actual user file
    try:
        with open(r'c:\Users\ben\Dev\np2\test_files\model (1).bbmodel', 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        content = '{"key_' + '", "key_'.join(str(i) for i in range(1000)) + '"}'
    
    editor.set_content(content, filepath='test.bbmodel')
    print(f"Loaded {len(content)} chars")

def benchmark():
    print("Typing 20 chars...")
    start = time.time()
    for i in range(20):
        editor.text.insert('insert', 'k')
        editor.update_idletasks()
        
    elapsed = (time.time() - start) * 1000
    print(f"Typing 20 chars took: {elapsed:.2f} ms ({elapsed/20:.2f} ms/char)")
    root.quit()

root = tk.Tk()
editor = TextEditor(root)
editor.pack(fill='both', expand=True)
editor.set_word_wrap(False)
editor.set_highlight_occurrences(False)

root.after(500, load_file)
root.after(1500, benchmark)

root.mainloop()

import tkinter as tk
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from editor.text_editor import TextEditor
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def load_file():
    # Generate 5000 unique words
    words = [f"key_{i}" for i in range(5000)]
    content = " ".join(words)
    editor.set_content(content, filepath='test.json')
    print(f"Loaded {len(content)} chars, {len(words)} words")

def benchmark_typing():
    print("Benchmarking typing with autocomplete...")
    start = time.time()
    for i in range(50): # 50 chars
        editor.text.insert('insert', 'k')
        editor.text.event_generate('<<Modified>>')
        editor.text.event_generate('<KeyRelease>') # Triggers AutoComplete
        editor.update_idletasks()
        
    end = time.time()
    print(f"Typing 50 chars took: {(end-start)*1000:.2f} ms")
    
    root.quit()

root = tk.Tk()
editor = TextEditor(root)
editor.pack(fill='both', expand=True)

# Set defaults
editor.set_word_wrap(False)
editor.set_highlight_occurrences(False)

root.after(1000, load_file)
root.after(2000, benchmark_typing)

root.mainloop()

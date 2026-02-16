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
    # Generate 18k line
    content = 'a' * 20000
    editor.set_content(content, filepath='test.json')
    print(f"Loaded {len(content)} chars")

def benchmark_typing():
    print("Benchmarking typing...")
    start = time.time()
    # Simulate typing by inserting directly (programmatic)
    # This bypasses event bindings for keys, so we must manually trigger events if needed?
    # No, we want to test if 'insert' slows down due to 'modified' traces?
    # TextEditor binds <<Modified>>.
    # TextEditor binds <KeyRelease>.
    
    # We will invoke insert 100 times.
    for i in range(100):
        editor.text.insert('insert', 'x')
        editor.text.event_generate('<<Modified>>') # Simulate modification
        editor.text.event_generate('<KeyRelease>') # Simulate key release
        editor.update_idletasks()
        
    end = time.time()
    print(f"Typing 100 chars took: {(end-start)*1000:.2f} ms")
    
    # Check if perf_log.txt was created
    if os.path.exists('perf_log.txt'):
        print("Perf log found:")
        with open('perf_log.txt', 'r') as f:
            print(f.read())
    else:
        print("No perf log found (all methods < 2ms)")
        
    root.quit()

root = tk.Tk()
# Create dummy tab manager interface if needed? 
# TextEditor uses self.master for nothing critical?
# It uses self.bind.
editor = TextEditor(root)
editor.pack(fill='both', expand=True)

# Set defaults to match user report
editor.set_word_wrap(False)
editor.set_highlight_occurrences(False)

root.after(1000, load_file)
root.after(2000, benchmark_typing)

root.mainloop()

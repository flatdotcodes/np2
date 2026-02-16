"""
Bare Tkinter Text widget test - NO custom code.
This proves whether the lag is in Tkinter itself.
"""
import tkinter as tk
import time

root = tk.Tk()
root.title("BARE TKINTER TEST - No Custom Code")

# Create BARE text widget - no custom bindings
text = tk.Text(root, wrap='none', font=('Consolas', 11))
text.pack(fill='both', expand=True, side='left')

# Add scrollbars
v_scroll = tk.Scrollbar(root, orient='vertical', command=text.yview)
v_scroll.pack(side='right', fill='y')
h_scroll = tk.Scrollbar(root, orient='horizontal', command=text.xview)
h_scroll.pack(side='bottom', fill='x')
text.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

# Load the actual file
try:
    with open(r'c:\Users\ben\Dev\np2\test_files\model (1).bbmodel', 'r', encoding='utf-8') as f:
        content = f.read()
except:
    content = 'a' * 20000

text.insert('1.0', content)
print(f"Loaded {len(content)} chars")
print("Try scrolling to the right and selecting text.")
print("If it lags, this is a TKINTER LIMITATION, not NP2 code.")

root.mainloop()

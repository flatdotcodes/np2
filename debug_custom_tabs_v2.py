import tkinter as tk
from editor.tab_manager import TabManager

root = tk.Tk()
root.geometry("600x400")
root.title("Tab Manager Visual Verification")

# Create manager
tm = TabManager(root)
tm.pack(fill=tk.BOTH, expand=True)

# Add mock tabs
tm.new_tab(None, "First Tab")
tm.new_tab(None, "Second Tab")
tm.new_tab(None, "Third Tab")

# Verify click selection
def on_tab_change(event):
    print(f"Tab Changed! Active: {tm._get_tab_data(tm._active_tab_id)['text']}")

tm.bind('<<NotebookTabChanged>>', on_tab_change)

# Test Close after 1s
def test_close():
    print("Closing First Tab...")
    # Get first tab id
    full_list = tm.tabs()
    if full_list:
        tm.close_tab(full_list[0])
        print("First Tab Closed.")
    else:
        print("No tabs to close")

root.after(1000, test_close)

root.mainloop()

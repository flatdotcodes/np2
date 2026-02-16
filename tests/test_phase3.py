"""
Test Phase 3 logic (Settings, Persistence).
"""
import sys
import os
import shutil
import tkinter as tk
from tkinter import ttk

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.settings import SettingsManager, DRAFTS_DIR
from editor.tab_manager import TabManager

def test_settings():
    print("Testing SettingsManager...")
    mgr = SettingsManager()
    mgr.set('autosave_mode', 'interval')
    mgr.save()
    
    mgr2 = SettingsManager()
    assert mgr2.get('autosave_mode') == 'interval'
    print("Settings persistence: PASS")

def test_session_persistence():
    print("Testing Session Persistence...")
    root = tk.Tk()
    nb = TabManager(root)
    
    # Create untitled tab with content
    editor = nb.new_tab(content="Draft content")
    editor.modified = True
    
    # Create named tab
    # (Mocking filepath requires existing file, skip for now or create temp)
    
    # Get session data
    data = nb.get_session_data()
    
    # Verify draft
    assert len(data) == 1
    draft_path = data[0].get('draft_path')
    assert draft_path is not None
    assert os.path.exists(draft_path)
    
    with open(draft_path, 'r') as f:
        content = f.read()
    assert content == "Draft content"
    print("Draft saving: PASS")
    
    # Cleanup
    shutil.rmtree(DRAFTS_DIR, ignore_errors=True)
    root.destroy()

if __name__ == '__main__':
    try:
        test_settings()
        test_session_persistence()
        print("ALL TESTS PASSED")
    except Exception as e:
        print(f"TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

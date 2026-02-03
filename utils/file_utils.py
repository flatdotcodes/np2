"""
File utilities for NP2 editor.
Handles file operations, encoding detection, and recent files.
"""

import os
import json

# Default encoding
DEFAULT_ENCODING = 'utf-8'

# Recent files storage location
RECENT_FILES_PATH = os.path.join(os.path.expanduser('~'), '.np2_recent.json')
MAX_RECENT_FILES = 20


def read_file(filepath):
    """
    Read file content with encoding detection.
    
    Args:
        filepath: Path to file
        
    Returns:
        Tuple of (content, encoding)
    """
    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'ascii']
    
    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                content = f.read()
            return content, encoding
        except UnicodeDecodeError:
            continue
        except Exception as e:
            raise e
    
    # Last resort: read as binary and decode with replacement
    with open(filepath, 'rb') as f:
        content = f.read().decode('utf-8', errors='replace')
    return content, 'utf-8'


def write_file(filepath, content, encoding=DEFAULT_ENCODING):
    """
    Write content to file.
    
    Args:
        filepath: Path to file
        content: Content to write
        encoding: Encoding to use
        
    Returns:
        True if successful
    """
    try:
        # Create directory if it doesn't exist
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        
        with open(filepath, 'w', encoding=encoding, newline='') as f:
            f.write(content)
        return True
    except Exception as e:
        raise e


def get_recent_files():
    """
    Get list of recently opened files.
    
    Returns:
        List of file paths
    """
    try:
        if os.path.exists(RECENT_FILES_PATH):
            with open(RECENT_FILES_PATH, 'r', encoding='utf-8') as f:
                files = json.load(f)
            # Filter out files that no longer exist
            return [f for f in files if os.path.exists(f)]
    except Exception:
        pass
    return []


def add_recent_file(filepath):
    """
    Add a file to the recent files list.
    
    Args:
        filepath: Path to file
    """
    try:
        filepath = os.path.abspath(filepath)
        files = get_recent_files()
        
        # Remove if already in list
        if filepath in files:
            files.remove(filepath)
        
        # Add to front
        files.insert(0, filepath)
        
        # Limit list size
        files = files[:MAX_RECENT_FILES]
        
        # Save
        with open(RECENT_FILES_PATH, 'w', encoding='utf-8') as f:
            json.dump(files, f)
    except Exception:
        pass


def clear_recent_files():
    """Clear the recent files list."""
    try:
        if os.path.exists(RECENT_FILES_PATH):
            os.remove(RECENT_FILES_PATH)
    except Exception:
        pass


def get_file_info(filepath):
    """
    Get file information.
    
    Args:
        filepath: Path to file
        
    Returns:
        Dict with file info or None
    """
    try:
        stat = os.stat(filepath)
        return {
            'path': filepath,
            'name': os.path.basename(filepath),
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'exists': True,
        }
    except Exception:
        return None


def is_binary_file(filepath, sample_size=8192):
    """
    Check if a file is binary.
    
    Args:
        filepath: Path to file
        sample_size: Number of bytes to check
        
    Returns:
        True if file appears to be binary
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(sample_size)
        
        # Check for null bytes
        if b'\x00' in chunk:
            return True
        
        # Check ratio of non-text bytes
        text_chars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)))
        non_text = len([b for b in chunk if b not in text_chars])
        
        return non_text / len(chunk) > 0.30 if chunk else False
    except Exception:
        return False

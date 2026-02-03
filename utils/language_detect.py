"""
Language detection utilities for NP2 editor.
Detects programming language from file extension and content.
"""

# Maps file extensions to Pygments lexer names
EXTENSION_MAP = {
    # Python
    '.py': 'python',
    '.pyw': 'python',
    '.pyi': 'python',
    
    # JavaScript/TypeScript
    '.js': 'javascript',
    '.jsx': 'jsx',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.mjs': 'javascript',
    '.cjs': 'javascript',
    
    # Web
    '.html': 'html',
    '.htm': 'html',
    '.css': 'css',
    '.scss': 'scss',
    '.sass': 'sass',
    '.less': 'less',
    
    # Data formats
    '.json': 'json',
    '.xml': 'xml',
    '.yaml': 'yaml',
    '.yml': 'yaml',
    '.toml': 'toml',
    '.ini': 'ini',
    '.cfg': 'ini',
    
    # C family
    '.c': 'c',
    '.h': 'c',
    '.cpp': 'cpp',
    '.hpp': 'cpp',
    '.cc': 'cpp',
    '.cxx': 'cpp',
    '.cs': 'csharp',
    
    # Java/JVM
    '.java': 'java',
    '.kt': 'kotlin',
    '.scala': 'scala',
    '.groovy': 'groovy',
    
    # Ruby
    '.rb': 'ruby',
    '.erb': 'erb',
    
    # PHP
    '.php': 'php',
    
    # Go
    '.go': 'go',
    
    # Rust
    '.rs': 'rust',
    
    # Swift
    '.swift': 'swift',
    
    # Shell
    '.sh': 'bash',
    '.bash': 'bash',
    '.zsh': 'zsh',
    '.fish': 'fish',
    '.ps1': 'powershell',
    '.psm1': 'powershell',
    '.bat': 'batch',
    '.cmd': 'batch',
    
    # SQL
    '.sql': 'sql',
    
    # Markdown/Text
    '.md': 'markdown',
    '.markdown': 'markdown',
    '.rst': 'rst',
    '.txt': 'text',
    
    # Config files
    '.dockerfile': 'docker',
    '.makefile': 'make',
    
    # Lua
    '.lua': 'lua',
    
    # Perl
    '.pl': 'perl',
    '.pm': 'perl',
    
    # R
    '.r': 'r',
    '.R': 'r',
}

# Shebang to language mapping
SHEBANG_MAP = {
    'python': 'python',
    'python3': 'python',
    'python2': 'python',
    'node': 'javascript',
    'bash': 'bash',
    'sh': 'bash',
    'zsh': 'zsh',
    'ruby': 'ruby',
    'perl': 'perl',
    'php': 'php',
}

# All supported languages for manual selection
SUPPORTED_LANGUAGES = sorted(set(EXTENSION_MAP.values()))

# Reverse map: language to primary extension
LANGUAGE_EXTENSIONS = {
    'python': '.py',
    'javascript': '.js',
    'jsx': '.jsx',
    'typescript': '.ts',
    'tsx': '.tsx',
    'html': '.html',
    'css': '.css',
    'scss': '.scss',
    'sass': '.sass',
    'less': '.less',
    'json': '.json',
    'xml': '.xml',
    'yaml': '.yaml',
    'toml': '.toml',
    'ini': '.ini',
    'c': '.c',
    'cpp': '.cpp',
    'csharp': '.cs',
    'java': '.java',
    'kotlin': '.kt',
    'scala': '.scala',
    'groovy': '.groovy',
    'ruby': '.rb',
    'erb': '.erb',
    'php': '.php',
    'go': '.go',
    'rust': '.rs',
    'swift': '.swift',
    'bash': '.sh',
    'zsh': '.zsh',
    'fish': '.fish',
    'powershell': '.ps1',
    'batch': '.bat',
    'sql': '.sql',
    'markdown': '.md',
    'latex': '.tex',
    'perl': '.pl',
    'lua': '.lua',
    'haskell': '.hs',
    'elixir': '.ex',
    'erlang': '.erl',
    'clojure': '.clj',
    'dart': '.dart',
    'r': '.r',
    'text': '.txt',
}


def detect_from_extension(filename):
    """
    Detect language from file extension.
    
    Args:
        filename: Name or path of the file
        
    Returns:
        Language name or 'text' if not detected
    """
    if not filename:
        return 'text'
    
    import os
    _, ext = os.path.splitext(filename.lower())
    
    # Handle special filenames
    basename = os.path.basename(filename.lower())
    if basename == 'dockerfile':
        return 'docker'
    if basename == 'makefile':
        return 'make'
    if basename == '.gitignore':
        return 'gitignore'
    if basename == '.env':
        return 'bash'
    
    return EXTENSION_MAP.get(ext, 'text')


def detect_from_shebang(content):
    """
    Detect language from shebang line.
    
    Args:
        content: File content (first few lines)
        
    Returns:
        Language name or None if not detected
    """
    if not content:
        return None
    
    lines = content.split('\n')
    if not lines:
        return None
    
    first_line = lines[0].strip()
    
    if not first_line.startswith('#!'):
        return None
    
    # Parse shebang
    shebang = first_line[2:].strip()
    
    # Handle /usr/bin/env style
    if 'env ' in shebang:
        parts = shebang.split()
        if len(parts) >= 2:
            interpreter = parts[-1]
        else:
            return None
    else:
        # Direct path like /usr/bin/python
        import os
        interpreter = os.path.basename(shebang.split()[0])
    
    return SHEBANG_MAP.get(interpreter)


def detect_language(filename, content=None):
    """
    Detect programming language from filename and optionally content.
    
    Args:
        filename: Name or path of the file
        content: Optional file content for shebang detection
        
    Returns:
        Language name
    """
    # Try shebang first if content available
    if content:
        shebang_lang = detect_from_shebang(content)
        if shebang_lang:
            return shebang_lang
    
    # Fall back to extension
    return detect_from_extension(filename)


def get_lexer_for_language(language):
    """
    Get Pygments lexer for a language.
    
    Args:
        language: Language name
        
    Returns:
        Pygments lexer or None
    """
    try:
        from pygments.lexers import get_lexer_by_name
        return get_lexer_by_name(language)
    except Exception:
        return None

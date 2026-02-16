"""
Syntax highlighting engine for NP2 editor.
Uses Pygments for language-specific highlighting.
"""

try:
    from pygments import lex
    from pygments.lexers import get_lexer_by_name, TextLexer
    from pygments.token import Token
    PYGMENTS_AVAILABLE = True
except ImportError:
    PYGMENTS_AVAILABLE = False


# Color schemes - Modern VS Code inspired
THEMES = {
    'dark': {
        Token.Keyword: '#569cd6',
        Token.Keyword.Constant: '#569cd6',
        Token.Keyword.Declaration: '#569cd6',
        Token.Keyword.Namespace: '#c586c0',
        Token.Keyword.Type: '#4ec9b0',
        
        Token.Name: '#9cdcfe',
        Token.Name.Builtin: '#4ec9b0',
        Token.Name.Function: '#dcdcaa',
        Token.Name.Class: '#4ec9b0',
        Token.Name.Decorator: '#dcdcaa',
        Token.Name.Exception: '#4ec9b0',
        Token.Name.Variable: '#9cdcfe',
        
        Token.String: '#ce9178',
        Token.String.Doc: '#6a9955',
        Token.String.Escape: '#d7ba7d',
        Token.String.Regex: '#d16969',
        
        Token.Number: '#b5cea8',
        
        Token.Operator: '#d4d4d4',
        Token.Punctuation: '#d4d4d4',
        
        Token.Comment: '#6a9955',
        Token.Comment.Single: '#6a9955',
        Token.Comment.Multiline: '#6a9955',
        
        Token.Error: '#f44747',
        
        'background': '#1e1e1e',
        'foreground': '#d4d4d4',
        'selection': '#264f78',
        'line_highlight': '#2a2d2e',
        'line_number': '#858585',
        'line_number_bg': '#1e1e1e',
    },
    'light': {
        Token.Keyword: '#0000ff',
        Token.Keyword.Constant: '#0000ff',
        Token.Keyword.Declaration: '#0000ff',
        Token.Keyword.Namespace: '#af00db',
        Token.Keyword.Type: '#267f99',
        
        Token.Name: '#001080',
        Token.Name.Builtin: '#267f99',
        Token.Name.Function: '#795e26',
        Token.Name.Class: '#267f99',
        Token.Name.Decorator: '#795e26',
        Token.Name.Exception: '#267f99',
        Token.Name.Variable: '#001080',
        
        Token.String: '#a31515',
        Token.String.Doc: '#008000',
        Token.String.Escape: '#ee0000',
        Token.String.Regex: '#811f3f',
        
        Token.Number: '#098658',
        
        Token.Operator: '#000000',
        Token.Punctuation: '#000000',
        
        Token.Comment: '#008000',
        Token.Comment.Single: '#008000',
        Token.Comment.Multiline: '#008000',
        
        Token.Error: '#ff0000',
        
        'background': '#ffffff',
        'foreground': '#000000',
        'selection': '#add6ff',
        'line_highlight': '#fffbdd',
        'line_number': '#237893',
        'line_number_bg': '#f3f3f3',
    },
}


class SyntaxHighlighter:
    """Handles syntax highlighting for the text editor."""
    
    def __init__(self, text_widget, theme='light'):
        """
        Initialize the highlighter.
        
        Args:
            text_widget: Tkinter Text widget to highlight
            theme: Color theme name ('dark' or 'light')
        """
        self.text_widget = text_widget
        self.theme = THEMES.get(theme, THEMES['light'])
        self.lexer = TextLexer() if PYGMENTS_AVAILABLE else None
        self.language = 'text'
        
        self._setup_tags()
    
    def _setup_tags(self):
        """Configure text tags for highlighting."""
        if not PYGMENTS_AVAILABLE:
            return
        
        # Create tags for each token type
        for token_type, color in self.theme.items():
            if isinstance(token_type, str):
                continue  # Skip non-token entries like 'background'
            
            tag_name = str(token_type)
            self.text_widget.tag_configure(tag_name, foreground=color)
        
        # Configure widget colors
        self.text_widget.configure(
            background=self.theme['background'],
            foreground=self.theme['foreground'],
            insertbackground=self.theme['foreground'],
            selectbackground=self.theme['selection'],
        )
    
    def set_language(self, language):
        """
        Set the programming language for highlighting.
        
        Args:
            language: Language name (e.g., 'python', 'javascript')
        """
        self.language = language
        
        if not PYGMENTS_AVAILABLE:
            return
        
        try:
            self.lexer = get_lexer_by_name(language)
        except Exception:
            self.lexer = TextLexer()
    
    def set_theme(self, theme_name):
        """
        Set the color theme.
        
        Args:
            theme_name: Theme name ('dark' or 'light')
        """
        self.theme = THEMES.get(theme_name, THEMES['dark'])
        self._setup_tags()
        self.highlight_all()
    
    def highlight_all(self):
        """Highlight the entire document."""
        if not PYGMENTS_AVAILABLE or not self.lexer:
            return
        
        # Get all content
        content = self.text_widget.get('1.0', 'end-1c')
        
        # Remove old tags
        for token_type in self.theme:
            if not isinstance(token_type, str):
                self.text_widget.tag_remove(str(token_type), '1.0', 'end')
        
        # Apply new highlighting
        self._apply_highlighting(content, '1.0')
    
    def highlight_region(self, start, end):
        """
        Highlight a specific region.
        
        Args:
            start: Start index (e.g., '1.0')
            end: End index (e.g., 'end')
        """
        if not PYGMENTS_AVAILABLE or not self.lexer:
            return
        
        # Expand to full lines for proper context
        line_start = self.text_widget.index(f'{start} linestart')
        line_end = self.text_widget.index(f'{end} lineend')
        
        # Content too large for regex highlighting?
        # Get content first (fix for UnboundLocalError)
        content = self.text_widget.get(line_start, line_end)
        
        if len(content) > 4000:
             return
             
        # Remove old tags in region
        for token_type in self.theme:
            if not isinstance(token_type, str):
                self.text_widget.tag_remove(str(token_type), line_start, line_end)

        # Optimization: Skip highlighting for very long lines to prevent lag
        if len(content) > 4000:
            return
        
        # Apply new highlighting
        self._apply_highlighting(content, line_start)
    
    def _apply_highlighting(self, content, start_index):
        """
        Apply syntax highlighting to content.
        
        Args:
            content: Text content to highlight
            start_index: Starting position in widget
        """
        if not content:
            return
        
        try:
            tokens = lex(content, self.lexer)
            
            current_pos = start_index
            
            for token_type, token_value in tokens:
                if not token_value:
                    continue
                
                # Calculate end position
                lines = token_value.split('\n')
                
                if len(lines) == 1:
                    # Single line token
                    end_pos = f'{current_pos}+{len(token_value)}c'
                else:
                    # Multi-line token
                    current_line, current_col = map(int, self.text_widget.index(current_pos).split('.'))
                    end_line = current_line + len(lines) - 1
                    end_col = len(lines[-1]) if len(lines) > 1 else current_col + len(token_value)
                    end_pos = f'{end_line}.{end_col}'
                
                # Apply tag for token type
                tag_name = str(token_type)
                
                # Try to find a matching tag (check parent types too)
                temp_type = token_type
                while temp_type and tag_name not in [str(t) for t in self.theme if not isinstance(t, str)]:
                    temp_type = temp_type.parent
                    if temp_type:
                        tag_name = str(temp_type)
                
                if tag_name in [str(t) for t in self.theme if not isinstance(t, str)]:
                    self.text_widget.tag_add(tag_name, current_pos, end_pos)
                
                # Move current position
                current_pos = end_pos
                
        except Exception:
            pass  # Silently fail on highlighting errors
    
    def get_theme_colors(self):
        """
        Get current theme colors.
        
        Returns:
            Dict of theme colors
        """
        return {
            'background': self.theme['background'],
            'foreground': self.theme['foreground'],
            'selection': self.theme['selection'],
            'line_highlight': self.theme['line_highlight'],
            'line_number': self.theme['line_number'],
            'line_number_bg': self.theme['line_number_bg'],
        }

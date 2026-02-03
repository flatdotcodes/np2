"""
Linting integration for NP2 editor.
Runs external linters and reports errors.
"""

import os
import re
import subprocess
import threading
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LintError:
    """Represents a linting error or warning."""
    line: int
    column: int
    message: str
    severity: str  # 'error', 'warning', 'info'
    code: Optional[str] = None


class Linter:
    """Runs external linters and parses results."""
    
    # Linter configurations
    LINTERS = {
        'python': {
            'command': ['python', '-m', 'pylint', '--output-format=text', '--msg-template={line}:{column}: {msg_id}: {msg}'],
            'pattern': r'^(\d+):(\d+): ([A-Z]\d+): (.+)$',
            'severity_map': {
                'E': 'error',    # Error
                'F': 'error',    # Fatal
                'W': 'warning',  # Warning
                'C': 'info',     # Convention
                'R': 'info',     # Refactor
            }
        },
        'python_flake8': {
            'command': ['python', '-m', 'flake8', '--format=%(row)d:%(col)d: %(code)s: %(text)s'],
            'pattern': r'^(\d+):(\d+): ([A-Z]\d+): (.+)$',
            'severity_map': {
                'E': 'error',
                'W': 'warning',
                'F': 'error',
            }
        },
    }
    
    def __init__(self, on_results=None):
        """
        Initialize the linter.
        
        Args:
            on_results: Callback when linting completes (errors: List[LintError])
        """
        self.on_results = on_results
        self.current_process = None
        self.errors: List[LintError] = []
    
    def lint_file(self, filepath, language='python'):
        """
        Run linting on a file.
        
        Args:
            filepath: Path to file
            language: Programming language
        """
        # Get linter config
        config = self.LINTERS.get(language)
        if not config:
            self.errors = []
            if self.on_results:
                self.on_results([])
            return
        
        # Run linting in background
        thread = threading.Thread(
            target=self._run_linter,
            args=(filepath, config),
            daemon=True
        )
        thread.start()
    
    def _run_linter(self, filepath, config):
        """Run linter in background thread."""
        try:
            # Build command
            command = config['command'] + [filepath]
            
            # Run linter
            self.current_process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.path.dirname(filepath),
            )
            
            stdout, stderr = self.current_process.communicate(timeout=30)
            
            # Parse output
            errors = self._parse_output(stdout, config)
            
            self.errors = errors
            
            if self.on_results:
                self.on_results(errors)
                
        except subprocess.TimeoutExpired:
            if self.current_process:
                self.current_process.kill()
        except FileNotFoundError:
            # Linter not installed
            self.errors = []
            if self.on_results:
                self.on_results([])
        except Exception:
            self.errors = []
            if self.on_results:
                self.on_results([])
        finally:
            self.current_process = None
    
    def _parse_output(self, output, config) -> List[LintError]:
        """Parse linter output into LintError objects."""
        errors = []
        pattern = re.compile(config['pattern'], re.MULTILINE)
        severity_map = config.get('severity_map', {})
        
        for match in pattern.finditer(output):
            try:
                line = int(match.group(1))
                column = int(match.group(2))
                code = match.group(3)
                message = match.group(4)
                
                # Determine severity from code prefix
                severity = severity_map.get(code[0], 'info')
                
                errors.append(LintError(
                    line=line,
                    column=column,
                    message=message,
                    severity=severity,
                    code=code,
                ))
            except Exception:
                pass
        
        return errors
    
    def cancel(self):
        """Cancel current linting operation."""
        if self.current_process:
            try:
                self.current_process.kill()
            except Exception:
                pass
    
    def get_errors_for_line(self, line: int) -> List[LintError]:
        """Get all errors for a specific line."""
        return [e for e in self.errors if e.line == line]
    
    def get_error_count(self) -> dict:
        """Get count of errors by severity."""
        counts = {'error': 0, 'warning': 0, 'info': 0}
        for error in self.errors:
            counts[error.severity] = counts.get(error.severity, 0) + 1
        return counts


class LintGutter:
    """Displays lint markers in the editor gutter."""
    
    def __init__(self, text_widget, line_numbers):
        """
        Initialize the lint gutter.
        
        Args:
            text_widget: Text widget to display lint markers on
            line_numbers: LineNumbers canvas widget
        """
        self.text_widget = text_widget
        self.line_numbers = line_numbers
        self.linter = Linter(on_results=self._on_lint_results)
        self.errors: List[LintError] = []
        self.markers = {}
        
        # Configure text tags for underlining
        self.text_widget.tag_configure('lint_error', underline=True, underlinefg='#f14c4c')
        self.text_widget.tag_configure('lint_warning', underline=True, underlinefg='#cca700')
        self.text_widget.tag_configure('lint_info', underline=True, underlinefg='#3794ff')
    
    def lint_file(self, filepath, language='python'):
        """Run linting on a file."""
        self.linter.lint_file(filepath, language)
    
    def _on_lint_results(self, errors: List[LintError]):
        """Handle lint results."""
        self.errors = errors
        self._update_markers()
    
    def _update_markers(self):
        """Update lint markers in the editor."""
        # Clear existing markers
        self.text_widget.tag_remove('lint_error', '1.0', 'end')
        self.text_widget.tag_remove('lint_warning', '1.0', 'end')
        self.text_widget.tag_remove('lint_info', '1.0', 'end')
        
        # Add new markers
        for error in self.errors:
            tag = f'lint_{error.severity}'
            
            # Underline the error location
            start = f'{error.line}.{error.column}'
            end = f'{error.line}.end'
            
            try:
                self.text_widget.tag_add(tag, start, end)
            except Exception:
                pass
    
    def get_tooltip_text(self, line: int) -> Optional[str]:
        """Get tooltip text for a line."""
        errors = self.linter.get_errors_for_line(line)
        
        if not errors:
            return None
        
        lines = []
        for error in errors:
            icon = '❌' if error.severity == 'error' else ('⚠' if error.severity == 'warning' else 'ℹ')
            lines.append(f'{icon} [{error.code}] {error.message}')
        
        return '\n'.join(lines)
    
    def clear(self):
        """Clear all lint markers."""
        self.errors = []
        self._update_markers()

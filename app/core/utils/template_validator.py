"""Template validation utilities"""
import re
from typing import List, Dict, Tuple
from html.parser import HTMLParser

class TemplateValidator:
    """Validate HTML templates for common issues"""
    
    @staticmethod
    def validate_html_structure(html_content: str) -> Tuple[bool, List[str]]:
        """Validate basic HTML structure"""
        errors = []
        
        # Check for DOCTYPE
        if not html_content.strip().startswith('<!DOCTYPE'):
            errors.append("Missing DOCTYPE declaration")
        
        # Check for required tags
        required_tags = ['<html', '<head', '<body']
        for tag in required_tags:
            if tag not in html_content.lower():
                errors.append(f"Missing required tag: {tag}")
        
        # Check for closing tags
        if '<html' in html_content.lower() and '</html>' not in html_content.lower():
            errors.append("Missing closing </html> tag")
        
        if '<head' in html_content.lower() and '</head>' not in html_content.lower():
            errors.append("Missing closing </head> tag")
            
        if '<body' in html_content.lower() and '</body>' not in html_content.lower():
            errors.append("Missing closing </body> tag")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def extract_variables(html_content: str) -> List[str]:
        """Extract template variables from HTML content"""
        # Find all {{variable}} patterns
        pattern = r'\{\{([^}]+)\}\}'
        variables = re.findall(pattern, html_content)
        return [var.strip() for var in variables]
    
    @staticmethod
    def validate_variables(html_content: str) -> Tuple[bool, List[str]]:
        """Validate template variables"""
        errors = []
        variables = TemplateValidator.extract_variables(html_content)
        
        for var in variables:
            # Check for invalid characters in variable names
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', var):
                errors.append(f"Invalid variable name: {var}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_css(html_content: str) -> Tuple[bool, List[str]]:
        """Basic CSS validation"""
        errors = []
        
        # Check for unclosed style tags
        style_open = html_content.count('<style')
        style_close = html_content.count('</style>')
        
        if style_open != style_close:
            errors.append("Mismatched <style> and </style> tags")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_template(html_content: str) -> Dict[str, any]:
        """Comprehensive template validation"""
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'variables': [],
            'stats': {}
        }
        
        # HTML structure validation
        html_valid, html_errors = TemplateValidator.validate_html_structure(html_content)
        if not html_valid:
            results['errors'].extend(html_errors)
            results['is_valid'] = False
        
        # Variable validation
        var_valid, var_errors = TemplateValidator.validate_variables(html_content)
        if not var_valid:
            results['errors'].extend(var_errors)
            results['is_valid'] = False
        
        # CSS validation
        css_valid, css_errors = TemplateValidator.validate_css(html_content)
        if not css_valid:
            results['errors'].extend(css_errors)
            results['is_valid'] = False
        
        # Extract variables
        results['variables'] = TemplateValidator.extract_variables(html_content)
        
        # Template statistics
        results['stats'] = {
            'character_count': len(html_content),
            'line_count': html_content.count('\n') + 1,
            'variable_count': len(results['variables']),
            'unique_variables': len(set(results['variables']))
        }
        
        # Warnings
        if results['stats']['character_count'] > 50000:
            results['warnings'].append("Template is very large (>50KB)")
        
        if results['stats']['variable_count'] == 0:
            results['warnings'].append("Template contains no variables")
        
        return results
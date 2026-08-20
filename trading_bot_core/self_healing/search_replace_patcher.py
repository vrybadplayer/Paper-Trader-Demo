"""
Search Replace Patcher
Uses libcst to search and replace code patterns using libcst for automated error repair.
"""

import libcst as cst
import libcst.matchers as m
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SearchReplacePatcher:
    """
    Uses libcst to search for specific code patterns and replace them with corrected versions.
    This enables automated error repair by identifying common bug patterns and applying fixes.
    """
    
    def __init__(self):
        """Initialize the search replace patcher."""
        self.patches_applied = 0
    
    def patch_file(self, file_path: str, search_pattern: str, replace_pattern: str) -> bool:
        """
        Apply a simple string-based search and replace to a file.
        
        Args:
            file_path: Path to the file to patch
            search_pattern: String to search for
            replace_pattern: String to replace with
            
        Returns:
            bool: True if patch was applied, False otherwise
        """
        try:
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Check if pattern exists
            if search_pattern not in content:
                logger.debug(f"Pattern not found in {file_path}: {search_pattern}")
                return False
            
            # Apply the replacement
            new_content = content.replace(search_pattern, replace_pattern)
            
            # Write the file back
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            self.patches_applied += 1
            logger.info(f"Applied patch to {file_path}: replaced '{search_pattern}' with '{replace_pattern}'")
            return True
        except Exception as e:
            logger.error(f"Error patching file {file_path}: {e}")
            return False
    
    def patch_with_cst(self, file_path: str, matcher: m.Matcher, 
                      replacement_func: callable) -> bool:
        """
        Apply a libcst-based patch using a matcher and replacement function.
        
        Args:
            file_path: Path to the file to patch
            matcher: Libcst matcher to identify nodes
            replacement_func: Function that takes a matched node and returns replacement node
            
        Returns:
            bool: True if patch was applied, False otherwise
        """
        try:
            # Read the file
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the content
            tree = cst.parse_module(content)
            
            # Create a transformer
            class Patcher(cst.CSTTransformer):
                def __init__(self, matcher, replacement_func):
                    self.matcher = matcher
                    self.replacement_func = replacement_func
                    self.changed = False
                
                def leave(self, original_node, updated_node):
                    if m.matches(original_node, self.matcher):
                        try:
                            replacement_node = self.replacement_func(original_node)
                            if replacement_node is not None:
                                self.changed = True
                                return replacement_node
                        except Exception as e:
                            logger.error(f"Error in replacement function: {e}")
                    return updated_node
            
            # Apply the transformer
            patcher = Patcher(matcher, replacement_func)
            new_tree = tree.visit(patcher)
            
            if patcher.changed:
                # Write the file back
                with open(file_path, 'w') as f:
                    f.write(new_tree.code)
                
                self.patches_applied += 1
                logger.info(f"Applied CST patch to {file_path}")
                return True
            else:
                logger.debug(f"No matches found for CST patch in {file_path}")
                return False
        except Exception as e:
            logger.error(f"Error applying CST patch to {file_path}: {e}")
            return False
    
    def fix_common_bugs(self, file_path: str) -> List[str]:
        """
        Attempt to fix common bugs in a Python file using predefined patterns.
        
        Args:
            file_path: Path to the Python file to fix
            
        Returns:
            List of descriptions of fixes applied
        """
        fixes_applied = []
        
        try:
            with open(file_path, 'r') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return fixes_applied
        
        # Define common bug patterns and their fixes
        bug_patterns = [
            # Fix missing colon in if statements
            {
                'search': r'if\s+.*\s*$',
                'replace': lambda m: m.group(0) + ':',
                'description': 'Added missing colon to if statement',
                'use_regex': True
            },
            # Fix missing colon in for loops
            {
                'search': r'for\s+.*\s*$',
                'replace': lambda m: m.group(0) + ':',
                'description': 'Added missing colon to for loop',
                'use_regex': True
            },
            # Fix missing colon in while loops
            {
                'search': r'while\s+.*\s*$',
                'replace': lambda m: m.group(0) + ':',
                'description': 'Added missing colon to while loop',
                'use_regex': True
            },
            # Fix missing colon in function definitions
            {
                'search': r'def\s+.*\s*$',
                'replace': lambda m: m.group(0) + ':',
                'description': 'Added missing colon to function definition',
                'use_regex': True
            },
            # Fix missing colon in class definitions
            {
                'search': r'class\s+.*\s*$',
                'replace': lambda m: m.group(0) + ':',
                'description': 'Added missing colon to class definition',
                'use_regex': True
            },
            # Fix missing colon in elif/else
            {
                'search': r'(elif|else)\s*$',
                'replace': lambda m: m.group(0) + ':',
                'description': 'Added missing colon to elif/else',
                'use_regex': True
            },
            # Fix common typo: "excpetion" -> "exception"
            {
                'search': 'excpetion',
                'replace': 'exception',
                'description': 'Fixed typo: excpetion -> exception',
                'use_regex': False
            },
            # Fix common typo: "recieve" -> "receive"
            {
                'search': 'recieve',
                'replace': 'receive',
                'description': 'Fixed typo: recieve -> receive',
                'use_regex': False
            },
            # Fix missing import for common modules
            {
                'search': 'from typing import',
                'replace': lambda m: m.group(0) + ' List, Dict, Any, Optional',
                'description': 'Added common typing imports',
                'use_regex': False,
                'condition': lambda c: 'List' not in c and 'Dict' not in c and 'from typing import' in c
            }
        ]
        
        # Apply each pattern
        for pattern in bug_patterns:
            try:
                if pattern['use_regex']:
                    import re
                    if pattern.get('condition') and not pattern['condition'](content):
                        continue
                    
                    def repl(match):
                        return pattern['replace'](match)
                    
                    new_content, count = re.subn(
                        pattern['search'], 
                        repl, 
                        content
                    )
                    
                    if count > 0:
                        content = new_content
                        fixes_applied.append(pattern['description'])
                        logger.info(f"Applied regex fix to {file_path}: {pattern['description']}")
                else:
                    if pattern['search'] in content:
                        if pattern.get('condition') and not pattern['condition'](content):
                            continue
                        
                        content = content.replace(pattern['search'], pattern['replace'])
                        fixes_applied.append(pattern['description'])
                        logger.info(f"Applied string fix to {file_path}: {pattern['description']}")
            except Exception as e:
                logger.error(f"Error applying pattern {pattern['description']}: {e}")
        
        # Write back the fixed content if any changes were made
        if fixes_applied:
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
            except Exception as e:
                logger.error(f"Error writing fixed content to {file_path}: {e}")
                return []
        
        return fixes_applied
    
    def get_patches_applied(self) -> int:
        """Get the number of patches applied."""
        return self.patches_applied
    
    def reset_counter(self):
        """Reset the patches applied counter."""
        self.patches_applied = 0

# Example usage (for testing)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a test file with bugs
    test_content = '''
def problematic_function(x, y
    if x > y
        print("x is greater than y")
    elif x < y
        print("x is less than y")
    else
        print("x equals y")
    recive_value = 0
    excpetion_occurred = False
    return recive_value

class MyClass
    def my_method(self)
        pass
'''
    
    with open('test_buggy_file.py', 'w') as f:
        f.write(test_content)
    
    # Create patcher and fix bugs
    patcher = SearchReplacePatcher()
    fixes = patcher.fix_common_bugs('test_buggy_file.py')
    
    print(f"Applied fixes: {fixes}")
    
    # Show the fixed content
    with open('test_buggy_file.py', 'r') as f:
        fixed_content = f.read()
    print("Fixed content:")
    print(fixed_content)
    
    # Clean up
    import os
    os.remove('test_buggy_file.py')
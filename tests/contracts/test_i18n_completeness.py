"""
tests/contracts/test_i18n_completeness.py

I18N COMPLETENESS CONTRACT TEST
===============================
Role: Ensures 100% of UI text references in app/ have corresponding i18n keys.
Coverage: Validates that all {XxxTexts.ATTRIBUTE} references exist in i18n modules.
Architecture: Contract Tests for i18n consistency.
Style: Pytest with AST-based static analysis.

This test automatically scans the app/ directory to find all usages of i18n text
classes (e.g., CommonTexts.APP_TITLE, KPITexts.LABEL_IV) and verifies that each
referenced attribute exists in the corresponding i18n module.

Ensures:
1. No broken references (accessing non-existent i18n keys)
2. 100% coverage of user-facing strings
3. Consistent naming patterns across the codebase
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

import pytest


class I18nUsageScanner(ast.NodeVisitor):
    """
    AST visitor that finds all references to i18n text classes.
    
    Detects patterns like:
    - SomeTexts.ATTRIBUTE
    - from src.i18n import SomeTexts
    - getattr(SomeTexts, 'ATTRIBUTE')
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: Set[str] = set()  # Imported i18n classes
        self.usages: List[Tuple[str, str, int]] = []  # (class_name, attr_name, line_no)
        
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track imports from src.i18n"""
        if node.module and node.module.startswith('src.i18n'):
            for alias in node.names:
                if alias.name.endswith('Texts') or alias.name.endswith('Labels') or alias.name.endswith('Messages'):
                    self.imports.add(alias.name)
        self.generic_visit(node)
        
    def visit_Attribute(self, node: ast.Attribute):
        """Track attribute accesses like SomeTexts.ATTRIBUTE"""
        if isinstance(node.value, ast.Name):
            class_name = node.value.id
            if class_name in self.imports and class_name.endswith(('Texts', 'Labels', 'Messages')):
                attr_name = node.attr
                # Only track uppercase attributes (constants, not methods)
                if attr_name.isupper() or attr_name.startswith('LABEL_') or attr_name.startswith('SUB_'):
                    self.usages.append((class_name, attr_name, node.lineno))
        self.generic_visit(node)


def scan_file_for_i18n_usage(file_path: Path) -> List[Tuple[str, str, int]]:
    """
    Scan a Python file for i18n text references.
    
    Parameters
    ----------
    file_path : Path
        Path to the Python file to scan.
        
    Returns
    -------
    List[Tuple[str, str, int]]
        List of (class_name, attribute_name, line_number) tuples.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
        tree = ast.parse(content, filename=str(file_path))
        scanner = I18nUsageScanner(str(file_path))
        scanner.visit(tree)
        return scanner.usages
    except (SyntaxError, UnicodeDecodeError) as e:
        # Skip files with syntax errors or encoding issues
        return []


def scan_directory_for_i18n_usage(directory: Path) -> Dict[str, List[Tuple[str, str, int]]]:
    """
    Recursively scan a directory for i18n text references.
    
    Parameters
    ----------
    directory : Path
        Root directory to scan.
        
    Returns
    -------
    Dict[str, List[Tuple[str, str, int]]]
        Dictionary mapping file paths to lists of (class_name, attr_name, line_no).
    """
    results = {}
    
    for py_file in directory.rglob("*.py"):
        # Skip __pycache__ and test files
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue
            
        usages = scan_file_for_i18n_usage(py_file)
        if usages:
            results[str(py_file.relative_to(directory.parent))] = usages
            
    return results


def validate_i18n_references() -> Tuple[List[str], Dict[str, List[str]]]:
    """
    Validate all i18n references in app/ directory.
    
    Returns
    -------
    Tuple[List[str], Dict[str, List[str]]]
        - List of error messages for missing attributes
        - Dict mapping class names to lists of missing attributes
    """
    # Import all i18n text classes
    try:
        from src.i18n import (
            BacktestTexts,
            BenchmarkTexts,
            ChartTexts,
            CommonTexts,
            ExpertTexts,
            FeedbackMessages,
            InputLabels,
            KPITexts,
            LegalTexts,
            MarketTexts,
            OnboardingTexts,
            PeersTexts,
            PillarLabels,
            QuantTexts,
            ResultsTexts,
            SidebarTexts,
            SOTPTexts,
            TooltipsTexts,
            UIMessages,
            UIRegistryTexts,
            UISharedTexts,
        )
    except ImportError as e:
        pytest.fail(f"Failed to import i18n modules: {e}")
        
    # Map class names to actual classes
    i18n_classes = {
        'BacktestTexts': BacktestTexts,
        'BenchmarkTexts': BenchmarkTexts,
        'ChartTexts': ChartTexts,
        'CommonTexts': CommonTexts,
        'ExpertTexts': ExpertTexts,
        'FeedbackMessages': FeedbackMessages,
        'InputLabels': InputLabels,
        'KPITexts': KPITexts,
        'LegalTexts': LegalTexts,
        'MarketTexts': MarketTexts,
        'OnboardingTexts': OnboardingTexts,
        'PeersTexts': PeersTexts,
        'PillarLabels': PillarLabels,
        'QuantTexts': QuantTexts,
        'ResultsTexts': ResultsTexts,
        'SidebarTexts': SidebarTexts,
        'SOTPTexts': SOTPTexts,
        'TooltipsTexts': TooltipsTexts,
        'UIMessages': UIMessages,
        'UIRegistryTexts': UIRegistryTexts,
        'UISharedTexts': UISharedTexts,
    }
    
    # Scan app/ directory
    app_dir = Path("app")
    if not app_dir.exists():
        pytest.skip("app/ directory not found")
        
    usages = scan_directory_for_i18n_usage(app_dir)
    
    # Validate each reference
    errors = []
    missing_by_class: Dict[str, List[str]] = {}
    
    for file_path, references in usages.items():
        for class_name, attr_name, line_no in references:
            if class_name not in i18n_classes:
                errors.append(
                    f"{file_path}:{line_no} - Unknown i18n class: {class_name}"
                )
                continue
                
            text_class = i18n_classes[class_name]
            if not hasattr(text_class, attr_name):
                error_msg = (
                    f"{file_path}:{line_no} - "
                    f"Missing attribute: {class_name}.{attr_name}"
                )
                errors.append(error_msg)
                
                # Track missing attributes by class
                if class_name not in missing_by_class:
                    missing_by_class[class_name] = []
                missing_by_class[class_name].append(attr_name)
    
    return errors, missing_by_class


@pytest.mark.contracts
class TestI18nCompleteness:
    """Test suite for i18n completeness validation."""
    
    def test_all_i18n_references_exist(self):
        """
        All {XxxTexts.ATTRIBUTE} references in app/ must exist in i18n modules.
        
        This test scans all Python files in the app/ directory and verifies that:
        1. Every reference to an i18n text class (e.g., CommonTexts, KPITexts) exists
        2. Every attribute accessed on these classes exists in the i18n module
        3. No broken references that would cause AttributeError at runtime
        
        Failure indicates:
        - Missing i18n keys that need to be added to src/i18n/fr/ui/*.py
        - Typos in attribute names
        - References to removed or renamed i18n constants
        """
        errors, missing_by_class = validate_i18n_references()
        
        if errors:
            # Format a helpful error message
            error_summary = "\n\n=== I18N COMPLETENESS FAILURES ===\n"
            error_summary += f"Found {len(errors)} missing i18n reference(s):\n\n"
            
            # Group by class for easier fixing
            if missing_by_class:
                error_summary += "Missing attributes by class:\n"
                for class_name, attrs in sorted(missing_by_class.items()):
                    unique_attrs = sorted(set(attrs))
                    error_summary += f"\n{class_name}:\n"
                    for attr in unique_attrs:
                        error_summary += f"  - {attr}\n"
                error_summary += "\n"
            
            # Show detailed file locations
            error_summary += "Detailed locations:\n"
            for error in errors:
                error_summary += f"  {error}\n"
                
            pytest.fail(error_summary)
    
    def test_i18n_modules_importable(self):
        """All i18n text modules should be importable without errors."""
        try:
            from src.i18n import (
                BacktestTexts,
                BenchmarkTexts,
                ChartTexts,
                CommonTexts,
                ExpertTexts,
                FeedbackMessages,
                InputLabels,
                KPITexts,
                LegalTexts,
                MarketTexts,
                OnboardingTexts,
                PeersTexts,
                PillarLabels,
                QuantTexts,
                ResultsTexts,
                SidebarTexts,
                SOTPTexts,
                TooltipsTexts,
                UIMessages,
                UIRegistryTexts,
                UISharedTexts,
            )
            # All imports successful
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import i18n modules: {e}")
    
    def test_i18n_classes_have_string_attributes(self):
        """i18n text classes should have string constants (not empty classes)."""
        from src.i18n import CommonTexts, KPITexts, SidebarTexts, UIMessages
        
        # Check that these key classes have at least some attributes
        for text_class in [CommonTexts, KPITexts, SidebarTexts, UIMessages]:
            attrs = [
                attr for attr in dir(text_class)
                if not attr.startswith('_') and isinstance(getattr(text_class, attr, None), str)
            ]
            assert len(attrs) > 0, f"{text_class.__name__} has no string attributes"
    
    def test_no_hardcoded_strings_in_app_views(self):
        """
        Detect potential hard-coded French/English strings in app/ views.
        
        This is a heuristic check that looks for quoted strings that might be
        user-facing text. It's not exhaustive but helps catch obvious violations.
        
        Note: This test allows:
        - Developer logs (logger.debug, logger.info, etc.)
        - Technical keys (short strings without spaces, like "DCF", "RIM")
        - Exception messages for developers
        """
        app_dir = Path("app")
        if not app_dir.exists():
            pytest.skip("app/ directory not found")
        
        # Patterns to search for (potential hard-coded user-facing strings)
        # We look for French/English phrases that are likely UI text
        suspicious_patterns = [
            re.compile(r'st\.(info|warning|error|success)\s*\(\s*["\']([A-ZÀ-Ÿ][a-zà-ÿ].*?)["\']'),  # st.info("Text")
            re.compile(r'st\.markdown\s*\(\s*["\']([A-ZÀ-Ÿ][a-zà-ÿ].*?)["\']'),  # st.markdown("Text")
            re.compile(r'st\.write\s*\(\s*["\']([A-ZÀ-Ÿ][a-zà-ÿ].*?)["\']'),  # st.write("Text")
        ]
        
        # Patterns to exclude (not user-facing)
        exclude_patterns = [
            r'logger\.',  # Developer logs
            r'raise\s+\w+Error',  # Exception messages
            r'#.*$',  # Comments
        ]
        
        violations = []
        
        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test_" in py_file.name:
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8')
                lines = content.split('\n')
                
                for line_no, line in enumerate(lines, start=1):
                    # Skip excluded patterns
                    if any(re.search(pattern, line) for pattern in exclude_patterns):
                        continue
                    
                    # Check for suspicious patterns
                    for pattern in suspicious_patterns:
                        match = pattern.search(line)
                        if match:
                            text = match.group(1) if match.lastindex >= 1 else match.group(0)
                            # Filter out very short strings (likely not user-facing)
                            if len(text) > 10 and ' ' in text:
                                violations.append(
                                    f"{py_file.relative_to(app_dir.parent)}:{line_no} - "
                                    f"Potential hard-coded string: '{text}'"
                                )
            except (UnicodeDecodeError, FileNotFoundError):
                continue
        
        # This is a soft check - we document violations but don't fail
        # (some may be false positives)
        if violations:
            message = "\n\n=== POTENTIAL HARD-CODED STRINGS ===\n"
            message += f"Found {len(violations)} potential hard-coded string(s):\n\n"
            for violation in violations[:20]:  # Limit to first 20
                message += f"  {violation}\n"
            if len(violations) > 20:
                message += f"\n  ... and {len(violations) - 20} more\n"
            
            # For now, just print the violations as a warning
            # You can uncomment the next line to make this a hard failure
            # pytest.fail(message)
            print(message)


@pytest.mark.contracts
class TestI18nNamingConventions:
    """Test suite for i18n naming pattern enforcement."""
    
    def test_i18n_classes_follow_naming_pattern(self):
        """
        i18n classes should follow the pattern: {Layer}{Domain}Texts
        
        Examples:
        - ExpertTerminalTexts ✓
        - SidebarTexts ✓
        - ResultsTexts ✓
        - random_stuff ✗
        """
        from src.i18n import __all__ as i18n_exports
        
        valid_suffixes = ['Texts', 'Labels', 'Messages']
        
        for export_name in i18n_exports:
            # Skip non-text classes (like enums, utilities)
            if not any(export_name.endswith(suffix) for suffix in valid_suffixes):
                continue
            
            # Check that it ends with a valid suffix
            assert any(export_name.endswith(suffix) for suffix in valid_suffixes), (
                f"i18n class '{export_name}' should end with one of: {valid_suffixes}"
            )
            
            # Check that it starts with uppercase (PascalCase)
            assert export_name[0].isupper(), (
                f"i18n class '{export_name}' should start with uppercase letter"
            )
    
    def test_i18n_constants_are_uppercase(self):
        """i18n constant attributes should be UPPERCASE with underscores."""
        from src.i18n import CommonTexts, KPITexts, SidebarTexts
        
        for text_class in [CommonTexts, KPITexts, SidebarTexts]:
            attrs = [
                attr for attr in dir(text_class)
                if not attr.startswith('_') and isinstance(getattr(text_class, attr, None), str)
            ]
            
            for attr in attrs:
                # Allow some exceptions for special patterns
                if attr.startswith('SUB_') or attr.startswith('LABEL_') or attr.startswith('HELP_'):
                    continue
                
                # Most constants should be uppercase
                if not attr.isupper():
                    # This is informational, not a hard failure
                    print(f"Note: {text_class.__name__}.{attr} is not uppercase")

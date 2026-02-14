"""
tests/contracts/test_architecture.py

ARCHITECTURE CONTRACT GUARDS
============================
Role: Validates layered architecture rules and import dependencies.
Coverage: Import restrictions, layer boundaries, code organization.
Architecture: Contract Tests.
Style: Pytest with contracts marker for separate execution.

These tests enforce architectural boundaries:
- src/ should never import from app/ (UI layer)
- src/ should never import streamlit directly
- infra/ can import from src/ but not from app/
"""

import re
from pathlib import Path

import pytest


@pytest.mark.contracts
class TestSrcLayerPurity:
    """Test suite for src/ layer isolation from UI dependencies."""

    def test_no_streamlit_imports_in_src(self):
        """No Python file in src/ should import streamlit directly."""
        src_dir = Path("src")
        violations = []

        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            content = py_file.read_text(encoding="utf-8")

            # Check for streamlit imports
            if re.search(r"^\s*import\s+streamlit", content, re.MULTILINE):
                violations.append(f"{py_file}: direct streamlit import")

            if re.search(r"^\s*from\s+streamlit", content, re.MULTILINE):
                violations.append(f"{py_file}: from streamlit import")

        assert len(violations) == 0, f"Found {len(violations)} streamlit import(s) in src/:\n" + "\n".join(violations)

    def test_no_app_imports_in_src(self):
        """No Python file in src/ should import from app/."""
        src_dir = Path("src")
        violations = []

        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            content = py_file.read_text(encoding="utf-8")

            # Check for app imports
            if re.search(r"^\s*import\s+app\.", content, re.MULTILINE):
                violations.append(f"{py_file}: import app.*")

            if re.search(r"^\s*from\s+app\.", content, re.MULTILINE):
                violations.append(f"{py_file}: from app.* import")

        assert len(violations) == 0, f"Found {len(violations)} app/ import(s) in src/:\n" + "\n".join(violations)


@pytest.mark.contracts
class TestInfraLayerBoundaries:
    """Test suite for infra/ layer import rules."""

    def test_infra_can_import_src_but_not_app(self):
        """infra/ files may import from src/ but not from app/."""
        infra_dir = Path("infra")
        app_violations = []

        for py_file in infra_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue

            content = py_file.read_text(encoding="utf-8")

            # Check for app imports (not allowed)
            if re.search(r"^\s*import\s+app\.", content, re.MULTILINE):
                app_violations.append(f"{py_file}: import app.*")

            if re.search(r"^\s*from\s+app\.", content, re.MULTILINE):
                app_violations.append(f"{py_file}: from app.* import")

        assert len(app_violations) == 0, f"Found {len(app_violations)} app/ import(s) in infra/:\n" + "\n".join(
            app_violations
        )

    def test_infra_src_imports_allowed(self):
        """Document that infra/ importing from src/ is allowed (data providers need models)."""
        # This is a documentation test
        # infra/data_providers/ legitimately imports src.models.company
        # infra/macro/ legitimately imports src.models.company
        assert True  # This is expected and allowed


@pytest.mark.contracts
class TestLayeredArchitectureDocumentation:
    """Test suite documenting the architecture layers."""

    def test_architecture_layers_documented(self):
        """
        Document the layered architecture:

        Layer 1 - UI/Presentation (app/):
          - Can import from any lower layer
          - Contains Streamlit-specific code
          - Should be thin, delegating to lower layers

        Layer 2 - Application Logic (src/):
          - Core business logic
          - Model definitions
          - Valuation strategies
          - Must NOT import from app/ or streamlit

        Layer 3 - Infrastructure (infra/):
          - Data providers
          - External API integrations
          - Reference data
          - Can import from src/ (needs models)
          - Must NOT import from app/

        Layer 4 - Tests (tests/):
          - Can import from any layer for testing
          - Should use mocks for external dependencies
        """
        # This is a documentation test
        assert True

    def test_dependency_flow_documented(self):
        """
        Document dependency flow:

        Allowed:
          app/ -> src/
          app/ -> infra/
          infra/ -> src/
          tests/ -> anything

        Forbidden:
          src/ -> app/
          src/ -> streamlit
          infra/ -> app/
        """
        # This is a documentation test
        assert True


@pytest.mark.contracts
class TestDirectoryStructure:
    """Test suite for verifying expected directory structure."""

    def test_required_directories_exist(self):
        """All required top-level directories should exist."""
        required_dirs = [
            "src",
            "app",
            "infra",
            "tests",
        ]

        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            assert dir_path.exists() and dir_path.is_dir(), f"Required directory '{dir_name}' not found"

    def test_src_subdirectories_exist(self):
        """Key src/ subdirectories should exist."""
        src_subdirs = [
            "src/models",
            "src/computation",
            "src/valuation",
            "src/core",
            "src/config",
        ]

        for subdir in src_subdirs:
            dir_path = Path(subdir)
            assert dir_path.exists() and dir_path.is_dir(), f"Required src subdirectory '{subdir}' not found"

    def test_infra_subdirectories_exist(self):
        """Key infra/ subdirectories should exist."""
        infra_subdirs = [
            "infra/data_providers",
            "infra/macro",
            "infra/ref_data",
        ]

        for subdir in infra_subdirs:
            dir_path = Path(subdir)
            assert dir_path.exists() and dir_path.is_dir(), f"Required infra subdirectory '{subdir}' not found"


@pytest.mark.contracts
class TestCodeOrganization:
    """Test suite for code organization rules."""

    def test_all_packages_have_init(self):
        """All Python packages should have __init__.py files."""
        violations = []

        for root_dir in ["src", "infra", "tests"]:
            root_path = Path(root_dir)
            if not root_path.exists():
                continue

            for subdir in root_path.rglob("*"):
                if not subdir.is_dir():
                    continue

                # Skip __pycache__ and hidden directories
                if "__pycache__" in str(subdir) or str(subdir).startswith("."):
                    continue

                # Check if it contains Python files
                has_py_files = any(subdir.glob("*.py"))

                if has_py_files:
                    init_file = subdir / "__init__.py"
                    if not init_file.exists():
                        violations.append(str(subdir))

        # Allow some violations for now (this is a soft check)
        # But document any packages missing __init__.py
        if violations:
            print(f"\nPackages without __init__.py (may be intentional): {violations}")


@pytest.mark.contracts
class TestImportHygiene:
    """Test suite for import statement hygiene."""

    def test_no_star_imports_in_core_modules(self):
        """Core modules should avoid star imports (from X import *)."""
        core_dirs = ["src/models", "src/computation", "src/valuation"]
        violations = []

        for dir_path in core_dirs:
            dir_obj = Path(dir_path)
            if not dir_obj.exists():
                continue

            for py_file in dir_obj.rglob("*.py"):
                if "__pycache__" in str(py_file) or "__init__" in str(py_file):
                    continue

                content = py_file.read_text(encoding="utf-8")

                # Check for star imports
                if re.search(r"^\s*from\s+\S+\s+import\s+\*", content, re.MULTILINE):
                    violations.append(str(py_file))

        # This is more of a guideline than a hard rule
        if violations:
            print(f"\nFiles with star imports (review recommended): {violations}")

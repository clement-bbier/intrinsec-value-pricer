"""
tests/contracts/test_architecture_contracts.py

Tests contractuels pour l'étanchéité architecturale.

Test Contrats Architecture - ST-1.1
Pattern : Contract Testing
Style : Numpy Style docstrings

Ces tests garantissent que:
1. src/ ne dépend jamais de app/ ou streamlit
2. Tous les fichiers src/ ont `from __future__ import annotations`
3. Les fichiers critiques n'utilisent pas le type Any

RISQUES FINANCIERS:
- Une violation d'étanchéité peut créer des dépendances circulaires
- Le manque de typage strict peut masquer des erreurs de contrat
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Tuple

import pytest


# ==============================================================================
# CONFIGURATION
# ==============================================================================

PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"

# Fichiers critiques où Any est interdit dans les annotations
CRITICAL_FILES = [
    "src/valuation/engines.py",
    "src/valuation/pipelines.py",
]

# Patterns d'imports interdits dans src/
FORBIDDEN_IMPORT_PATTERNS = [
    r"^\s*import\s+streamlit",
    r"^\s*from\s+streamlit\s+import",
    r"^\s*from\s+app\.",
    r"^\s*from\s+app\s+import",
    r"^\s*import\s+app\.",
]


# ==============================================================================
# HELPERS
# ==============================================================================

def get_all_python_files(directory: Path) -> List[Path]:
    """
    Récupère tous les fichiers Python d'un répertoire.
    
    Args
    ----
    directory : Path
        Répertoire à scanner.
        
    Returns
    -------
    List[Path]
        Liste des fichiers .py trouvés.
    """
    return list(directory.rglob("*.py"))


def check_file_for_forbidden_imports(filepath: Path) -> List[str]:
    """
    Vérifie si un fichier contient des imports interdits.
    
    Args
    ----
    filepath : Path
        Chemin du fichier à vérifier.
        
    Returns
    -------
    List[str]
        Liste des lignes problématiques (vide si OK).
    """
    violations = []
    try:
        content = filepath.read_text(encoding="utf-8")
        for i, line in enumerate(content.split("\n"), 1):
            # Ignorer les commentaires et docstrings
            if line.strip().startswith("#"):
                continue
            # Ignorer les lignes dans les docstrings (approximation)
            if '"""' in line or "'''" in line:
                continue
                
            for pattern in FORBIDDEN_IMPORT_PATTERNS:
                if re.match(pattern, line):
                    violations.append(f"Line {i}: {line.strip()}")
    except Exception as e:
        violations.append(f"Error reading file: {e}")
    
    return violations


def check_future_annotations(filepath: Path) -> bool:
    """
    Vérifie si un fichier contient `from __future__ import annotations`.
    
    Args
    ----
    filepath : Path
        Chemin du fichier à vérifier.
        
    Returns
    -------
    bool
        True si le fichier contient l'import, False sinon.
    """
    try:
        content = filepath.read_text(encoding="utf-8")
        return "from __future__ import annotations" in content
    except Exception:
        return False


def check_any_in_annotations(filepath: Path) -> List[str]:
    """
    Vérifie si un fichier utilise Any dans les annotations de type.
    
    Args
    ----
    filepath : Path
        Chemin du fichier à vérifier.
        
    Returns
    -------
    List[str]
        Liste des utilisations de Any trouvées (vide si OK).
        
    Notes
    -----
    On tolère Any dans les commentaires, docstrings, et certains cas Pydantic.
    """
    violations = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            # Vérifier les annotations de fonction
            if isinstance(node, ast.FunctionDef):
                # Annotations des arguments
                for arg in node.args.args:
                    if arg.annotation:
                        annotation_str = ast.unparse(arg.annotation)
                        if annotation_str == "Any":
                            violations.append(
                                f"Function '{node.name}', arg '{arg.arg}': uses Any"
                            )
                
                # Annotation de retour
                if node.returns:
                    returns_str = ast.unparse(node.returns)
                    if returns_str == "Any":
                        violations.append(
                            f"Function '{node.name}' return: uses Any"
                        )
                        
    except SyntaxError:
        pass  # Fichier avec erreur de syntaxe, sera détecté ailleurs
    except Exception as e:
        violations.append(f"Error parsing file: {e}")
    
    return violations


# ==============================================================================
# TESTS
# ==============================================================================

class TestArchitecturalBoundaries:
    """Tests pour l'étanchéité architecturale src/ <-> app/."""
    
    def test_src_does_not_import_streamlit(self) -> None:
        """
        Vérifie qu'aucun fichier src/ n'importe streamlit.
        
        Financial Impact
        ----------------
        Une violation créerait une dépendance UI dans le core financier,
        rendant impossible l'utilisation du moteur en mode headless (tests, API).
        """
        violations: List[Tuple[Path, List[str]]] = []
        
        for filepath in get_all_python_files(SRC_DIR):
            file_violations = check_file_for_forbidden_imports(filepath)
            if file_violations:
                violations.append((filepath, file_violations))
        
        if violations:
            msg = "Forbidden imports found in src/:\n"
            for filepath, issues in violations:
                rel_path = filepath.relative_to(PROJECT_ROOT)
                msg += f"\n{rel_path}:\n"
                for issue in issues:
                    msg += f"  - {issue}\n"
            pytest.fail(msg)
    
    def test_src_does_not_import_app(self) -> None:
        """
        Vérifie qu'aucun fichier src/ n'importe de modules app/.
        
        Financial Impact
        ----------------
        Une violation créerait une dépendance circulaire et violerait
        le principe d'inversion de dépendances (DIP).
        """
        # Ce test est déjà couvert par test_src_does_not_import_streamlit
        # via les patterns FORBIDDEN_IMPORT_PATTERNS
        pass


class TestTypeSafetyContracts:
    """Tests pour la conformité du typage strict."""
    
    def test_src_files_have_future_annotations(self) -> None:
        """
        Vérifie que tous les fichiers src/ non-vides ont future annotations.
        
        Financial Impact
        ----------------
        Le typage 3.10+ permet une validation statique des contrats de données
        et réduit les erreurs de runtime qui pourraient invalider les calculs.
        
        Notes
        -----
        Les fichiers suivants sont exclus de cette vérification:
        - __init__.py : Fichiers de ré-export
        - src/i18n/** : Fichiers de constantes de chaînes (pas de logique)
        """
        missing: List[Path] = []
        
        # Patterns à exclure
        exclude_patterns = [
            "__init__.py",  # Fichiers d'initialisation
        ]
        exclude_dirs = ["i18n"]  # Dossiers d'internationalisation
        
        for filepath in get_all_python_files(SRC_DIR):
            # Ignorer les fichiers exclus par pattern
            if any(pattern in filepath.name for pattern in exclude_patterns):
                continue
            
            # Ignorer les dossiers exclus
            if any(excl_dir in filepath.parts for excl_dir in exclude_dirs):
                continue
            
            # Ignorer les fichiers très courts (< 100 caractères utiles)
            content = filepath.read_text(encoding="utf-8")
            if len(content.strip()) < 100:
                continue
                
            if not check_future_annotations(filepath):
                missing.append(filepath)
        
        if missing:
            msg = "Files missing 'from __future__ import annotations':\n"
            for filepath in missing:
                rel_path = filepath.relative_to(PROJECT_ROOT)
                msg += f"  - {rel_path}\n"
            pytest.fail(msg)
    
    def test_critical_files_no_any_in_annotations(self) -> None:
        """
        Vérifie que les fichiers critiques n'utilisent pas Any dans les annotations.
        
        Financial Impact
        ----------------
        Le type Any dans les fichiers de valorisation masque les erreurs
        de contrat et peut conduire à des calculs sur des données invalides.
        """
        violations: List[Tuple[str, List[str]]] = []
        
        for critical_file in CRITICAL_FILES:
            filepath = PROJECT_ROOT / critical_file
            if not filepath.exists():
                continue
                
            file_violations = check_any_in_annotations(filepath)
            if file_violations:
                violations.append((critical_file, file_violations))
        
        if violations:
            msg = "Any type found in critical file annotations:\n"
            for filename, issues in violations:
                msg += f"\n{filename}:\n"
                for issue in issues:
                    msg += f"  - {issue}\n"
            pytest.fail(msg)


class TestImportOrderContracts:
    """Tests pour l'ordre des imports (PEP 8 + conventions projet)."""
    
    def test_future_import_comes_first(self) -> None:
        """
        Vérifie que __future__ est toujours le premier import (après docstring).
        
        Financial Impact
        ----------------
        L'import __future__ doit être en premier pour activer les fonctionnalités
        Python 3.10+ dans tout le fichier.
        """
        violations: List[str] = []
        
        for filepath in get_all_python_files(SRC_DIR):
            content = filepath.read_text(encoding="utf-8")
            
            # Ignorer les fichiers sans future import
            if "from __future__ import annotations" not in content:
                continue
            
            try:
                tree = ast.parse(content)
                imports = [
                    node for node in ast.iter_child_nodes(tree)
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                ]
                
                if not imports:
                    continue
                
                first_import = imports[0]
                if isinstance(first_import, ast.ImportFrom):
                    if first_import.module != "__future__":
                        rel_path = filepath.relative_to(PROJECT_ROOT)
                        violations.append(str(rel_path))
                        
            except SyntaxError:
                pass
        
        if violations:
            msg = "Files where __future__ is not the first import:\n"
            for filepath in violations:
                msg += f"  - {filepath}\n"
            pytest.fail(msg)

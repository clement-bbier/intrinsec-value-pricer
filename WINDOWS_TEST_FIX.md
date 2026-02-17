# Fix for Windows Test Import Errors

## Problem
On Windows, you may see import errors like:
```
ImportError: cannot import name 'ExpertTexts' from 'src.i18n.fr.ui.expert'
```

## Root Cause
This is caused by stale Python bytecode cache files (`.pyc` files in `__pycache__` directories). After PR #26, which refactored terminal texts, the import structure changed but Windows cached the old bytecode.

## Solution: Clear Python Cache

Run these commands in your terminal (from the project root):

### Option 1: Using Python
```bash
python -m pip install pyclean
pyclean .
```

### Option 2: Manual Cleanup (Windows PowerShell)
```powershell
Get-ChildItem -Recurse -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Filter "*.pyc" | Remove-Item -Force
```

### Option 3: Manual Cleanup (Windows CMD)
```cmd
for /d /r . %d in (__pycache__) do @if exist "%d" rd /s /q "%d"
del /s /q *.pyc
```

### Option 4: Using Git
```bash
git clean -fdx -e .env -e .venv
```
(This removes all untracked files including cache, but preserves your virtual environment)

## After Cleanup

1. Reinstall dependencies:
```bash
pip install -r requirements.txt
```

2. Run tests:
```bash
pytest --cov=.
```

## Verification

The imports should now work correctly. You can verify with:
```bash
python -c "from src.i18n.fr.ui.expert import ExpertTexts, UISharedTexts; print('Success!')"
```

If this prints "Success!", the issue is resolved.

## Technical Details

The file structure is correct:
- `src/i18n/fr/ui/expert.py` imports from `src/i18n/fr/ui/terminals.py`
- `ExpertTexts` class is defined in `terminals.py` (line 541)
- The backward compatibility layer in `expert.py` properly re-exports the class

The issue only occurs on Windows due to Python bytecode caching behavior differences between Windows and Unix-like systems.

"""
app/views/inputs/__init__.py
Input forms for Auto and Expert modes.
"""

from .auto_form import render_auto_form
from .expert_form import render_expert_form

__all__ = ["render_auto_form", "render_expert_form"]
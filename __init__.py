"""
EZ 3D Pivot Tool

This package exposes the addon directly from `EZ_3DPivotTool.py` content.
Historically the implementation was in a separate module; for a standard
Blender addon we keep the implementation here in `__init__` so Blender's
installer detects it immediately when the add-on folder or ZIP is selected.
"""

from .EZ_3DPivotTool import *

# Re-export bl_info, register, unregister from the implementation
__all__ = [name for name in globals().keys() if name in ("bl_info", "register", "unregister")]

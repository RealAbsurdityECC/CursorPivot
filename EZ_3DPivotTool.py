"""
Top-level wrapper for Blender to allow installing the GitHub ZIP directly.

This file delegates bl_info, register and unregister to the actual
implementation module inside `source/EZ_3DPivotTool.py`.
"""
try:
    from source import EZ_3DPivotTool as _mod
except Exception:
    # Fallback: try direct import if the user extracted differently
    import importlib
    _mod = importlib.import_module('EZ_3DPivotTool')


# Expose metadata so Blender recognizes the addon in the ZIP root
bl_info = getattr(_mod, "bl_info", {})


def register():
    _mod.register()


def unregister():
    _mod.unregister()


__all__ = ["register", "unregister", "bl_info"]

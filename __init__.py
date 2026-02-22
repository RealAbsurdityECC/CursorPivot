"""
CursorPivot — package initializer

This file provides `bl_info` at the package root and forwards register/unregister
to the implementation module `CursorPivot.py`. Having `bl_info` here helps
Blender detect the addon reliably when installing from a ZIP.
"""

import importlib

# --- Metadata (kept in sync with the implementation) ---------------------
bl_info = {
	"name": "CursorPivot",
	"author": "You & GitHub Copilot (Claude)",
	"version": (1, 0, 0),
	"blender": (4, 0, 0),
	"location": "3D Viewport > Toolbar (T)",
	"description": (
		"Turns Blender's 3D cursor into a fully interactive tool pivot, similar to "
		"the tool pivot found in Maya, 3ds Max, and other 3D applications. Provides "
		"move & rotate gizmos, automatic pivot/orientation management, and a sticky "
		"cursor mode that follows object transforms."
	),
	"category": "3D View",
}


def register():
	# Import the implementation module and forward
	mod = importlib.import_module("CursorPivot")
	if hasattr(mod, "register"):
		mod.register()


def unregister():
	mod = importlib.import_module("CursorPivot")
	if hasattr(mod, "unregister"):
		mod.unregister()


__all__ = ["bl_info", "register", "unregister"]

"""
CursorPivot — package initializer
"""

from . import CursorPivot

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
    CursorPivot.register()


def unregister():
    CursorPivot.unregister()

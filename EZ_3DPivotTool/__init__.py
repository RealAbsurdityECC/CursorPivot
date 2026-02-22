from . import EZ_3DPivotTool as _mod

# Expose bl_info from the module so Blender recognizes the package
bl_info = getattr(_mod, "bl_info", {})


def register():
    _mod.register()


def unregister():
    _mod.unregister()


__all__ = ["register", "unregister", "bl_info"]

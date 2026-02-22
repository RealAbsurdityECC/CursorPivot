import math
import bpy
import mathutils
from bpy.types import GizmoGroup, Operator, Panel, WorkSpaceTool


# ---------------------------------------------------------------------------
#   Operator – toggle the Cursor Pivot tool on / off
# ---------------------------------------------------------------------------

# Map Blender context modes to the matching tool id
_TOOL_IDS = {
    'OBJECT': "toolpivot.cursor_pivot_tool",
    'EDIT_MESH': "toolpivot.cursor_pivot_tool_edit",
}
_ALL_TOOL_IDS = set(_TOOL_IDS.values())


class TOOLPIVOT_OT_toggle(Operator):
    """Activate or deactivate the Cursor Pivot tool"""
    bl_idname = "toolpivot.toggle"
    bl_label = "Toggle Cursor Pivot"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        active_tool = context.workspace.tools.from_space_view3d_mode(
            context.mode, create=False
        )
        is_active = active_tool and active_tool.idname in _ALL_TOOL_IDS

        if is_active:
            # Deactivate – switch back to the default Select Box tool
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        else:
            # Activate the tool matching the current mode (fallback to Object)
            tool_id = _TOOL_IDS.get(context.mode, _TOOL_IDS['OBJECT'])
            bpy.ops.wm.tool_set_by_id(name=tool_id)
            # Apply pivot + orientation settings
            context.scene.tool_settings.transform_pivot_point = 'CURSOR'
            try:
                slot = context.scene.transform_orientation_slots[0]
                slot.type = 'CURSOR'
            except Exception:
                pass  # orientation type may not be available
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#   N-Panel (Sidebar) – "CursorPivot" tab
# ---------------------------------------------------------------------------

class TOOLPIVOT_OT_reset_rotation(Operator):
    """Reset the 3D cursor rotation to zero"""
    bl_idname = "toolpivot.reset_rotation"
    bl_label = "Reset Cursor Rotation"
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        context.scene.cursor.rotation_euler = (0.0, 0.0, 0.0)
        return {'FINISHED'}


class TOOLPIVOT_OT_snap_to_selected(Operator):
    """Move the 3D cursor to the active object's origin"""
    bl_idname = "toolpivot.snap_to_selected"
    bl_label = "Cursor to Selected"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None

    def execute(self, context):
        obj = context.active_object
        context.scene.cursor.location = obj.matrix_world.translation.copy()
        return {'FINISHED'}


class TOOLPIVOT_OT_snap_to_center(Operator):
    """Move the 3D cursor to the world origin"""
    bl_idname = "toolpivot.snap_to_center"
    bl_label = "Cursor to World Origin"
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        context.scene.cursor.location = (0.0, 0.0, 0.0)
        return {'FINISHED'}


# ---------------------------------------------------------------------------
#   Sticky Cursor – cursor follows object transforms
# ---------------------------------------------------------------------------

# State tracking for the depsgraph handler
_sticky_state = {
    'prev_matrix': None,   # last known matrix_world of tracked object
    'updating': False,     # re-entrancy guard
}


class TOOLPIVOT_OT_toggle_sticky(Operator):
    """Toggle sticky cursor – cursor follows object move/rotate transforms"""
    bl_idname = "toolpivot.toggle_sticky"
    bl_label = "Toggle Sticky Cursor"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        scene = context.scene
        scene.toolpivot_sticky = not scene.toolpivot_sticky
        # Snapshot current object matrix when enabling
        if scene.toolpivot_sticky and context.active_object:
            _sticky_state['prev_matrix'] = context.active_object.matrix_world.copy()
        else:
            _sticky_state['prev_matrix'] = None
        return {'FINISHED'}


def _sticky_cursor_handler(scene, depsgraph):
    """Depsgraph post-update: if sticky is on and the active object moved,
    apply the same delta to the 3D cursor."""
    if _sticky_state['updating']:
        return
    if not getattr(scene, 'toolpivot_sticky', False):
        return
    if scene.tool_settings.transform_pivot_point != 'CURSOR':
        return

    obj = bpy.context.active_object
    if obj is None:
        _sticky_state['prev_matrix'] = None
        return

    new_mat = obj.matrix_world.copy()
    prev_mat = _sticky_state.get('prev_matrix')

    if prev_mat is None:
        _sticky_state['prev_matrix'] = new_mat
        return

    # Check if the matrix actually changed (within tolerance)
    if _matrices_equal(prev_mat, new_mat):
        return

    _sticky_state['updating'] = True

    try:
        # Decompose both matrices to isolate location and rotation
        prev_loc, prev_rot, _ = prev_mat.decompose()
        new_loc, new_rot, _ = new_mat.decompose()

        cursor = scene.cursor
        cursor_loc = mathutils.Vector(cursor.location)

        # Compute rotation delta (for cursor orientation update)
        delta_rot = new_rot @ prev_rot.inverted()
        delta_rot.normalize()

        # --- Separate orbital motion from genuine translation ---
        # Use the full 3x3 matrix delta (rotation + scale combined in world
        # space) to predict exactly where the object ends up when transformed
        # purely around the cursor.  This correctly handles rotation, scale,
        # and any combination — per-axis scale decomposition fails because
        # object scale is in local space, not world space.
        try:
            delta_3x3 = new_mat.to_3x3() @ prev_mat.to_3x3().inverted()
        except Exception:
            delta_3x3 = mathutils.Matrix.Identity(3)

        obj_offset = prev_loc - cursor_loc
        expected_orbital_loc = cursor_loc + delta_3x3 @ obj_offset
        genuine_translation = new_loc - expected_orbital_loc

        # Apply rotation delta to cursor orientation
        rot_angle = delta_rot.angle
        if rot_angle > 1e-7:
            old_cursor_rot = cursor.rotation_euler.to_quaternion()
            new_cursor_rot = delta_rot @ old_cursor_rot
            cursor.rotation_euler = new_cursor_rot.to_euler()

        # Apply only the genuine translation (orbital component removed)
        if genuine_translation.length_squared > 1e-10:
            cursor.location = cursor_loc + genuine_translation
    finally:
        _sticky_state['prev_matrix'] = new_mat
        _sticky_state['updating'] = False


def _matrices_equal(a, b, epsilon=1e-6):
    """Check if two 4x4 matrices are approximately equal."""
    for i in range(4):
        for j in range(4):
            if abs(a[i][j] - b[i][j]) > epsilon:
                return False
    return True


def _quats_equal(a, b, epsilon=1e-5):
    """Check if two quaternions represent the same rotation."""
    dot = abs(a.dot(b))
    return dot > (1.0 - epsilon)


class TOOLPIVOT_PT_sidebar(Panel):
    bl_idname = "TOOLPIVOT_PT_sidebar"
    bl_label = "Cursor Pivot"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "CursorPivot"

    def draw(self, context):
        layout = self.layout

        active_tool = context.workspace.tools.from_space_view3d_mode(
            context.mode, create=False
        )
        is_active = active_tool and active_tool.idname in _ALL_TOOL_IDS

        row = layout.row()
        row.scale_y = 1.4
        row.operator(
            "toolpivot.toggle",
            text="Cursor Pivot: ON" if is_active else "Cursor Pivot: OFF",
            icon='PIVOT_CURSOR' if is_active else 'CURSOR',
            depress=is_active,
        )

        layout.separator()

        col = layout.column(align=True)
        col.operator("toolpivot.reset_rotation", text="Reset Rotation", icon='LOOP_BACK')
        col.operator("toolpivot.snap_to_selected", text="Cursor to Selected", icon='SNAP_ON')
        col.operator("toolpivot.snap_to_center", text="Cursor to World Origin", icon='WORLD')

        layout.separator()

        sticky = context.scene.toolpivot_sticky
        row2 = layout.row()
        row2.scale_y = 1.2
        row2.operator(
            "toolpivot.toggle_sticky",
            text="Sticky Cursor: ON" if sticky else "Sticky Cursor: OFF",
            icon='PINNED' if sticky else 'UNPINNED',
            depress=sticky,
        )


# ---------------------------------------------------------------------------
#   Gizmo Group – translate + rotate gizmos attached to the 3D cursor
# ---------------------------------------------------------------------------

class TOOLPIVOT_GGT_cursor_gizmos(GizmoGroup):
    bl_idname = "TOOLPIVOT_GGT_cursor_gizmos"
    bl_label = "Cursor Pivot Gizmos"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'WINDOW'
    bl_options = {'3D', 'SHOW_MODAL_ALL'}

    @classmethod
    def poll(cls, context):
        return True

    # ---- helpers -----------------------------------------------------------

    @staticmethod
    def _axis_rotations():
        """Rotation matrices that aim the gizmo's local +Z along each world axis."""
        return (
            mathutils.Matrix.Rotation(math.radians(90), 4, 'Y'),    # → +X
            mathutils.Matrix.Rotation(math.radians(-90), 4, 'X'),   # → +Y
            mathutils.Matrix.Identity(4),                             # → +Z
        )

    @staticmethod
    def _cursor_matrix(context):
        """Full 4x4 matrix from cursor location + rotation."""
        cursor = context.scene.cursor
        mat_loc = mathutils.Matrix.Translation(cursor.location)
        mat_rot = cursor.rotation_euler.to_matrix().to_4x4()
        return mat_loc @ mat_rot

    # ---- setup (runs once when tool becomes active) ------------------------

    def setup(self, context):
        mat = self._cursor_matrix(context)
        axis_rots = self._axis_rotations()

        # Axis colours: X = red, Y = green, Z = blue
        colors = (
            (1.0, 0.2, 0.2),
            (0.2, 1.0, 0.2),
            (0.2, 0.2, 1.0),
        )

        # ---- Move arrows (handler-based) ----------------------------------
        #
        # Arrow "offset" is a scalar distance along the arrow axis.
        # get() returns 0.0, set() applies delta from the cached start.
        # The cache's 'active' flag ensures start is only captured once
        # per drag.  draw_prepare resets it when no gizmo is modal.

        # World-space unit vectors for each axis
        _world_axes = (
            mathutils.Vector((1, 0, 0)),
            mathutils.Vector((0, 1, 0)),
            mathutils.Vector((0, 0, 1)),
        )

        self.move_gizmos = []
        self.move_caches = []
        for axis_idx, color in enumerate(colors):
            gz = self.gizmos.new("GIZMO_GT_arrow_3d")
            gz.draw_style = 'NORMAL'
            gz.color = color
            gz.alpha = 0.6
            gz.color_highlight = (1.0, 1.0, 1.0)
            gz.alpha_highlight = 1.0
            gz.scale_basis = 1.2
            gz.use_draw_modal = True
            gz.matrix_basis = mat @ axis_rots[axis_idx]

            cache = {'start_loc': None, 'start_dir': None, 'active': False}
            self.move_caches.append(cache)

            def _make_move_get(ax, c, world_ax):
                def fn():
                    if not c['active']:
                        cursor = bpy.context.scene.cursor
                        c['start_loc'] = mathutils.Vector(cursor.location)
                        # Arrow points along cursor's local axis in world space
                        c['start_dir'] = cursor.rotation_euler.to_matrix() @ world_ax
                        c['active'] = True
                    return 0.0
                return fn

            def _make_move_set(ax, c):
                def fn(value):
                    if c['start_loc'] is None:
                        return
                    bpy.context.scene.cursor.location = (
                        c['start_loc'] + value * c['start_dir']
                    )
                return fn

            gz.target_set_handler(
                "offset",
                get=_make_move_get(axis_idx, cache, _world_axes[axis_idx]),
                set=_make_move_set(axis_idx, cache),
            )
            self.move_gizmos.append(gz)

        # ---- Rotate dials -------------------------------------------------------
        #
        # Each dial applies rotation around the cursor's LOCAL axis using
        # quaternion math to avoid gimbal lock. At drag-start we snapshot
        # the cursor rotation as a quaternion; on each set() we compose a
        # local-axis delta rotation onto that snapshot.

        _local_axes = (
            mathutils.Vector((1, 0, 0)),  # local X
            mathutils.Vector((0, 1, 0)),  # local Y
            mathutils.Vector((0, 0, 1)),  # local Z
        )

        self.rotate_gizmos = []
        self.rotate_caches = []
        for axis_idx, color in enumerate(colors):
            gz = self.gizmos.new("GIZMO_GT_dial_3d")
            gz.color = color
            gz.alpha = 0.6
            gz.color_highlight = (1.0, 1.0, 1.0)
            gz.alpha_highlight = 1.0
            gz.scale_basis = 0.8
            gz.use_draw_modal = True
            gz.matrix_basis = mat @ axis_rots[axis_idx]

            cache = {'start_quat': None, 'active': False}
            self.rotate_caches.append(cache)

            def _make_rot_get(ax, c):
                def fn():
                    if not c['active']:
                        c['start_quat'] = bpy.context.scene.cursor.rotation_euler.to_quaternion()
                        c['active'] = True
                    return 0.0
                return fn

            def _make_rot_set(ax, c, local_axis):
                def fn(value):
                    if c['start_quat'] is None:
                        return
                    # Build a delta rotation around the cursor's local axis
                    delta = mathutils.Quaternion(local_axis, value)
                    # Apply: start_quat rotated by local delta
                    new_quat = c['start_quat'] @ delta
                    bpy.context.scene.cursor.rotation_euler = new_quat.to_euler()
                return fn

            gz.target_set_handler(
                "offset",
                get=_make_rot_get(axis_idx, cache),
                set=_make_rot_set(axis_idx, cache, _local_axes[axis_idx]),
            )
            self.rotate_gizmos.append(gz)

    # ---- per-frame matrix update ------------------------------------------

    def draw_prepare(self, context):
        any_modal = (
            any(gz.is_modal for gz in self.move_gizmos) or
            any(gz.is_modal for gz in self.rotate_gizmos)
        )

        # Reset start-caches only when no drag is active
        if not any_modal:
            for c in self.move_caches:
                c['active'] = False
            for c in self.rotate_caches:
                c['active'] = False

        # Always update gizmo matrices to follow the cursor
        mat = self._cursor_matrix(context)
        axis_rots = self._axis_rotations()

        for i, gz in enumerate(self.move_gizmos):
            gz.matrix_basis = mat @ axis_rots[i]
        for i, gz in enumerate(self.rotate_gizmos):
            gz.matrix_basis = mat @ axis_rots[i]


# ---------------------------------------------------------------------------
#   Workspace Tool – appears in the Toolbar (T panel)
# ---------------------------------------------------------------------------

class TOOLPIVOT_WT_cursor_pivot(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'OBJECT'

    bl_idname = "toolpivot.cursor_pivot_tool"
    bl_label = "Cursor Pivot"
    bl_description = (
        "Move and rotate the 3D cursor with gizmos. "
        "Automatically sets pivot to 3D Cursor and orientation to Cursor."
    )
    bl_icon = "ops.generic.cursor"       # crosshair cursor icon
    bl_widget = "TOOLPIVOT_GGT_cursor_gizmos"
    bl_keymap = ()


class TOOLPIVOT_WT_cursor_pivot_edit(WorkSpaceTool):
    bl_space_type = 'VIEW_3D'
    bl_context_mode = 'EDIT_MESH'

    bl_idname = "toolpivot.cursor_pivot_tool_edit"
    bl_label = "Cursor Pivot"
    bl_description = (
        "Move and rotate the 3D cursor with gizmos. "
        "Automatically sets pivot to 3D Cursor and orientation to Cursor."
    )
    bl_icon = "ops.generic.cursor"
    bl_widget = "TOOLPIVOT_GGT_cursor_gizmos"
    bl_keymap = ()


_tool_classes = (
    TOOLPIVOT_WT_cursor_pivot,
    TOOLPIVOT_WT_cursor_pivot_edit,
)


# ---------------------------------------------------------------------------
#   Registration
# ---------------------------------------------------------------------------

_classes = (
    TOOLPIVOT_OT_toggle,
    TOOLPIVOT_OT_reset_rotation,
    TOOLPIVOT_OT_snap_to_selected,
    TOOLPIVOT_OT_snap_to_center,
    TOOLPIVOT_OT_toggle_sticky,
    TOOLPIVOT_PT_sidebar,
    TOOLPIVOT_GGT_cursor_gizmos,
)

_addon_keymaps = []


def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.toolpivot_sticky = bpy.props.BoolProperty(
        name="Sticky Cursor",
        description="Cursor follows object transforms when pivot is set to 3D Cursor",
        default=False,
    )

    bpy.app.handlers.depsgraph_update_post.append(_sticky_cursor_handler)

    for tool_cls in _tool_classes:
        bpy.utils.register_tool(tool_cls, separator=True, group=False)

    # Register D shortcut in the 3D Viewport
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new('toolpivot.toggle', type='D', value='PRESS')
        _addon_keymaps.append((km, kmi))


def unregister():
    # Remove keymaps
    for km, kmi in _addon_keymaps:
        km.keymap_items.remove(kmi)
    _addon_keymaps.clear()

    for tool_cls in reversed(_tool_classes):
        bpy.utils.unregister_tool(tool_cls)

    if _sticky_cursor_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(_sticky_cursor_handler)

    del bpy.types.Scene.toolpivot_sticky

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()

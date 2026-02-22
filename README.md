# EZ 3D Pivot Tool for Blender

A Blender addon that turns the 3D cursor into a fully interactive **tool pivot**, similar to the tool pivot found in Maya, 3ds Max, and other 3D applications. Move and rotate gizmos let you position the pivot precisely, while automatic pivot point and transform orientation management keep everything in sync.

![Blender](https://img.shields.io/badge/Blender-4.0%2B-orange)
![License](https://img.shields.io/badge/License-GPL--3.0-blue)

## Features

- **Move & Rotate Gizmos** – 3-axis arrows (translate) and 3-axis rings (rotate) attached to the 3D cursor
- **Gimbal-free rotation** – quaternion-based rotation avoids gimbal lock
- **Auto pivot settings** – activating the tool sets Transform Pivot Point to *3D Cursor* and Transform Orientation to *Cursor*
- **Sticky Cursor** – optional mode where the cursor follows object transforms (move/rotate) in real time
- **Sidebar panel** – toggle the tool, reset rotation, snap cursor to selection or world origin
- **Keyboard shortcut** – press `D` to toggle the tool on/off
- **Multi-mode support** – works in both Object and Edit Mesh modes

## Installation

1. Download the repository ZIP from GitHub and extract it, or use GitHub's "Download ZIP" button.
2. In Blender, go to **Edit → Preferences → Add-ons**
3. Click **Install…** and navigate into the extracted folder. Select `source/EZ_3DPivotTool.py` and click **Install Add-on**.
4. Enable the checkbox next to **"EZ 3D Pivot Tool"**

## Usage

### Activating the Tool
- Press `D` in the 3D Viewport, **or**
- Open the N-panel (press `N`) → **EZ 3D Pivot Tool** tab → click **Cursor Pivot: OFF**
- The tool also appears in the left-hand Toolbar (press `T`)

### Gizmo Controls
- **Drag arrows** to move the cursor along X/Y/Z
- **Drag rings** to rotate the cursor around its local axes

### Sidebar Buttons
| Button | Action |
|--------|--------|
| **Cursor Pivot: ON/OFF** | Toggle the gizmo tool |
| **Reset Rotation** | Zero out cursor rotation |
| **Cursor to Selected** | Snap cursor to active object's origin |
| **Cursor to World Origin** | Move cursor to (0, 0, 0) |
| **Sticky Cursor: ON/OFF** | Cursor follows object transforms |

### Sticky Cursor
When enabled, moving or rotating an object will also move/rotate the 3D cursor by the same amount. This keeps the cursor "attached" to your object as a persistent custom pivot. Only active when the pivot point is set to *3D Cursor*.

## Requirements

- Blender 4.0 or newer

## Authors

- **You** – concept, design & testing
- **GitHub Copilot (Claude)** – code implementation & architecture

## License

This project is licensed under the GNU General Public License v3.0 – see the [LICENSE](LICENSE) file for details.

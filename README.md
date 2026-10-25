# Helldivers 2 on Apple Silicon

Launch fixes and tested settings for **FX Steam Launcher + Proton + FEX**. Uses the normal Steam/Easy Anti-Cheat launch.

**Tested:** M5 Pro, 24 GB RAM, macOS 26.5.1. Training and ship gameplay work. Other Macs and online missions need testing. [Results and versions](docs/tested-setup.md).

Requires Apple Command Line Tools (`xcode-select --install`).

## Setup

1. Install [FX 1.9-eac.2](https://github.com/StonkGuy/steamac/releases/tag/v1.9-eac.2), create its SteamOS disk, and sign into Steam.
2. In FX Steam, install **Helldivers 2**, **Proton Experimental (x86)**, **FEX-Emu**, and **Proton EasyAntiCheat Runtime**. Select x86 Proton Experimental for HD2. [Tool details](docs/setup.md).
3. Quit FX, then run on your **Mac**:

   ```bash
   git clone https://github.com/stmSi/helldivers2-mac-eac-fix.git
   cd helldivers2-mac-eac-fix
   ./configure-fx.command
   ```

4. Open FX again. Keep Steam open and games stopped. On your **Mac**, run:

   ```bash
   ./install.command
   ```

5. Paste this into HD2 → Properties → Launch Options:

   ```text
   env FEX_NEEDSSECCOMP=1 FEX_DISKCACHE=0 PROTON_LOG=0 WINEDEBUG=-all PROTON_USE_XALIA=0 PROTON_EAC_RUNTIME="$HOME/.local/share/Steam/steamapps/common/Proton EasyAntiCheat Runtime" %command% --use-d3d11
   ```

6. Start HD2. Use **Medium → Native render scale → Anti-aliasing Off → Motion Blur 0**. [Graphics](docs/graphics.md).

First setup builds FEX from source; allow several minutes. First launch may also compile shaders.

**Mouse:** Control+Command+G toggles capture; Control+Option releases it for menus. Optional [Control+G shortcut](docs/mouse.md).

[Troubleshooting / undo](docs/troubleshooting.md) · [Credits](docs/credits.md)

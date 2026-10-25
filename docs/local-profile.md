# FX-local HD2 profile

Leave **Steam → HD2 → Launch Options empty**.

The installer wraps FX's local `FEX-Emu/fex-compat-tool` entry point. For Steam app **553850** only, it supplies:

- FEX seccomp support and disabled disk cache.
- Proton's EAC runtime path and quiet logging.
- `--use-d3d11` for the DXMT profile.

Other games pass through unchanged. The wrapper exists only in FX's Linux VM, so it is not attached to your Steam account and is not used by your Windows laptop. Keep x86 Proton Experimental selected in FX.

## Migrate an existing installation

Stop games, keep FX open, then run on your Mac:

```bash
git pull
./install.command profile
```

This restarts the Steam client, backs up its local files, and removes the old FX launch-options wrapper from cached HD2 account settings. Unrelated game settings and ordinary Windows launch options are preserved. New Steam accounts use the same local profile automatically.

## Alternative renderer

After switching FX to Vulkan/KosmicKrisp and restarting the VM:

```bash
./install.command profile --renderer vulkan
```

This uses HD2's default D3D12 arguments. `--renderer dxmt` restores the faster tested DX11 profile.

Steam may replace the entry point during a FEX tool update. Re-run the installer afterward. `./install.command restore` restores the original entry point as well as the saved FEX runtime; it leaves Steam launch options empty.

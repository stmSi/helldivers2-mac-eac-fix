# Graphics and FPS

The faster tested path is **DXMT + DirectX 11**. FX must use DXMT; the local HD2 profile supplies `--use-d3d11` automatically. Leave Steam Launch Options empty.

Set these in HD2 and Apply:

| Setting | Starting value |
|---|---|
| Preset | Medium |
| Render scale | Native |
| Anti-aliasing | Off |
| Motion Blur | 0 |
| Frame-rate limit | 90, optional |

The final recorded Custom profile also had Bloom and Depth of Field off. Those experiments did not resolve the faint larger grid described below.

Changing individual options can make the preset show Custom. Fullscreen at the tested 1512×948 guest resolution is scaled to the Mac display; it is not native Retina resolution.

Observed ship readings were about **84–90 FPS** on an M5 Pro, 24 GB, at 1512×948. This is not a combat benchmark or a promise for other Macs.

## Known rendering limits

- TAA caused a severe fine grid in the DXMT path. Disabling anti-aliasing removed that grid in the test.
- A faint larger grid/banding can remain. Ambient-occlusion, bloom/depth-of-field and shader-math experiments did not establish a fix.
- Native scale was selected because the user found upscaling blurry. Lower scale can trade clarity for speed.

## Alternative renderer

For troublesome DXMT rendering: quit FX, select Vulkan/KosmicKrisp, restart, then run `./install.command profile --renderer vulkan` on the Mac. This returns to DirectX 12 without account-level launch options.

The tested D3D12 ship readings were roughly 44–52 FPS. DX11 through DXVK/Vulkan produced a GPU timeout in this investigation, so it is not the recommended fallback.

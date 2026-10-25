# Troubleshooting and undo

| Symptom | Check |
|---|---|
| Mac Wine says unsupported | Use Steam inside FX's Linux guest. This guide does not use Whisky. |
| EAC loads, then game stalls | Confirm patched FEX, x86 public Proton Experimental, and the local HD2 profile. Run `./install.command status`. |
| Switching Steam accounts breaks launch | Keep Launch Options empty and run `./install.command profile` once. See [local profile](local-profile.md). |
| Black screen on first start | Shader compilation took about 5–6 minutes in one tested D3D12 run. Give active compilation time. |
| EAC network-connect error | A normal retry cleared this once; the cause was not isolated. No firewall or network-spoofing change is part of this setup. |
| Fine grid / stripes | Disable anti-aliasing. See [graphics limits](graphics.md). |
| Camera stops at screen edges | Capture the mouse. See [controls](mouse.md). |
| Cursor invisible in ESC menu | Release capture. Leave HD2 auto-capture off. |
| Installer says FEXServer is running | Stop Steam games and wait for FEX to exit, then retry. |
| SSH fails | Boot FX with SSH enabled on port 2222. Use the same FX app/disk that created the VM. |
| Guest package installation fails | FX uses a specific SteamOS image. Check its configured package mirrors/keyring; the installer does not upgrade SteamOS. |

## Check or restore FEX

On your Mac, with FX open and games stopped:

```bash
./install.command status
./install.command restore
```

Restore returns the runtime saved before this install. If no backup exists, use Steam's **Verify integrity** on the FEX-Emu tool to obtain Valve's current files.

Steam can replace the custom FEX during a tool update. Re-run `./install.command` afterward. The saved backup remains the original pre-install snapshot; Steam integrity verification is the route back to the latest official version.

## Restore FX settings

Quit FX, then run from this repository:

```bash
defaults import es.fxgam.steamac .local-state/fx-preferences.before.plist
```

The restore command also removes the FX-local launch wrapper. Keep HD2's Steam Launch Options empty. To undo the optional shortcut build, restore the original app from `.local-state/shortcut/FX Steam Launcher.original.app` while FX is closed.

For bug reports, include hardware, macOS, FX/Proton/FEX versions and the failing step. Redact account IDs and credentials from logs before sharing them.

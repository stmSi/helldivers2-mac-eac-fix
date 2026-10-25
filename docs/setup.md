# Setup details

## 1. Install FX and Steam

- Use [FX 1.9-eac.2](https://github.com/StonkGuy/steamac/releases/tag/v1.9-eac.2). Newer releases are not verified here.
- Copy FX to Applications. Create its SteamOS disk and finish Steam sign-in yourself.
- Allow enough guest disk space for HD2, Proton, and several GB of compiler/source files. The tested 64 GB home partition had about 19 GB free after setup.
- Install the game through **Steam inside FX**.

## 2. Choose the correct Steam tools

HD2 → Properties → Compatibility → enable **Show all compatibility tools** → select **Proton Experimental**.

Choose the x86 tool (app **1493710**), rather than **Proton Experimental (ARM64)**. The tested public build is `experimental-11.0-20261014-x86_64`. Avoid its bleeding-edge beta for this setup.

In Steam's Library, enable Tools and install:

| Tool | Steam app ID |
|---|---:|
| FEX-Emu | 3127680 |
| Proton EasyAntiCheat Runtime | 1826330 |
| Proton Experimental, x86 | 1493710 |

Steam should fetch its required Steam Linux Runtime automatically.

## 3. Configure FX

Quit FX, then run `./configure-fx.command` on the Mac. It saves the previous preferences locally and sets:

| Setting | Value |
|---|---|
| CPUs / guest RAM | 8 / 12 GiB; 8 GiB RAM on Macs below 24 GB |
| Graphics | DXMT |
| Guest refresh / fullscreen | 120 Hz / on |
| Retina rendering | off |
| SSH | localhost port 2222 |
| HD2 mouse | manual capture |

24 GB is the tested host RAM size. Lower-memory Macs are unverified. Actual display refresh still depends on your monitor.

## 4. Install the FEX fix

Open FX again, keep Steam open, and stop games. In the cloned repository on the **Mac**:

```bash
./install.command
```

The command creates a local Python environment, connects only to your FX VM, installs missing compiler packages if needed, builds the pinned FEX sources, and replaces Steam's FEX runtime after backing it up. It installs the [FX-local HD2 profile](local-profile.md) and briefly restarts Steam. Missing compiler packages require guest sudo; the helper uses FX's existing generated guest password in memory.

The build uses four jobs. For less memory pressure:

```bash
./install.command --jobs 2
```

Game files and credentials are not changed. The profile migration clears only the old FX launch-options entry for HD2 in cached local account configs; private backups stay in the VM. Setup does not change your Steam Friends status.

## 5. Launch

Leave Steam's HD2 Launch Options empty, then play normally. The local profile supplies the settings independently of your Steam account. Keep EAC enabled. If HD2 shows the unknown/outdated graphics-driver dialog, choose Continue.

First-start shader compilation can take several minutes. Apply the [graphics settings](graphics.md) after the scene loads.

Custom FX locations are supported through `FX_APP`, `FX_DISK`, and `FX_SSH_PORT`. `FX_APP` is the `.app` directory. SSH remains restricted to localhost.

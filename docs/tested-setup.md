# Tested setup

Recorded on 25–26 October 2026.

| Component | Tested value |
|---|---|
| Mac | M5 Pro; 15 CPU cores, 16 GPU cores; 24 GB RAM |
| macOS | 26.5.1 |
| FX | StonkGuy 1.9-eac.2; commit `41c2c0eefb` |
| Guest | SteamOS image 20261022.6150929, 0.4.5; kernel 7.2.9-steamac; ARM64, 4 KiB pages |
| Guest resources | 8 vCPUs, 12 GiB RAM |
| HD2 | Steam build 26088801 |
| Proton | x86 Experimental public build 25936768; `experimental-11.0-20261014-x86_64` |
| EAC bootstrapper | 1.9.4; Linux module selected; result 301 |
| FEX base | `eac-2610.3`, commit `938eedfcd79e` |
| FEX additions | Bundled eight-commit CPU fault patch series |
| Essential local profile setting | `FEX_DISKCACHE=0` |

## Verified

- Genuine EAC initialization; training introduction and player movement.
- Ship rendering and user interaction.
- DXMT/DX11 ship readings around 84–90 FPS after disabling anti-aliasing.
- User confirmed the menu pointer reappears when mouse capture is released.
- After switching Steam accounts, the FX-local profile reached the ship on the main account with HD2 Launch Options empty for both cached accounts.
- Six focused CPU tests passed; the existing 33 regression runs produced their expected results.

## Limits

- No combat benchmark, long-session stability result, or verified online mission result.
- One EAC network-connect failure occurred; a retry worked.
- Faint larger DXMT grid/banding remained during the recorded graphics experiments.
- Other Macs, later game/Proton versions and lower-memory hosts are unverified.
- The optional Control+G source build is prepared and self-tested; live-game validation is pending.
- The packaged installer/profile has 19 automated checks. The account migration/profile was checked on the working VM; a clean-machine end-to-end install has not yet been verified.

Proton 10 reached an unimplemented `msctf` function-provider path and crashed. Newer public x86 Experimental passed that point. Cache-enabled FEX runs hit a code-invalidation wait; disabling its disk cache avoided that observed stall. The individual necessity of every bundled CPU patch has not been isolated.

These are compatibility changes. The normal game launcher and anti-cheat remain enabled; EAC initialization alone is not proof of online compatibility.

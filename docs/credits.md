# Credits and source provenance

- [FX / steamac](https://github.com/StonkGuy/steamac): StonkGuy's EAC-enabled release, based on [fxgl/steamac](https://github.com/fxgl/steamac). Apache-2.0.
- [FEX-Emu](https://github.com/FEX-Emu/FEX) and [StonkGuy's FEX fork](https://github.com/StonkGuy/FEX): ARM64 Linux emulation and Linux anti-cheat compatibility work. MIT.
- [Proton](https://github.com/ValveSoftware/Proton), SteamOS and Steam runtimes: Valve and contributors.
- [DXMT](https://github.com/3Shain/dxmt), KosmicKrisp, libkrun and the FX graphics stack: their respective contributors.

## Included FEX patches

`patches/fex-hd2.patch` preserves the original commit authors and messages. It applies to `eac-2610.3` and contains work from StonkGuy's PRs [3](https://github.com/StonkGuy/FEX/pull/3), [4](https://github.com/StonkGuy/FEX/pull/4), [6](https://github.com/StonkGuy/FEX/pull/6), [7](https://github.com/StonkGuy/FEX/pull/7), [20](https://github.com/StonkGuy/FEX/pull/20), and [21](https://github.com/StonkGuy/FEX/pull/21).

The local integration resolves overlapping unmapped-fetch and split-fetch changes, preserving both fault classification and failing-page address. That merge is part of this experimental combination, not an upstream acceptance claim. `versions.json` pins the final source-tree hash and patch checksums.

## License

Original integration scripts/documentation and the FX shortcut patch: [Apache-2.0](../LICENSE). FEX-derived patch code retains its [MIT license](../licenses/FEX-MIT.txt). Upstream software downloaded during builds retains its own licenses. No game, EAC, Steam, VM images, personal logs or compiled dependency bundles are distributed here.

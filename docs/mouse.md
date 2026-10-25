# Mouse controls

FX's capture state covers the entire game, including its ESC menu. In this DXMT setup, captured mode hides the visible menu pointer.

Keep HD2's **Capture Mouse in This Game** off in FX's Mouse menu:

| Action | Stock FX shortcut |
|---|---|
| Capture for unlimited camera rotation | Control+Command+G |
| Release for ESC/menu pointing | Control+Option |
| Toggle either way | Control+Command+G |

Capture again after closing the menu. Automatic recapture is disabled so a menu click does not hide the pointer again.

## Optional Control+G shortcut

This repository includes a small FX source patch adding **Control+G** as a toggle. The old shortcuts remain available. Holding G does not repeatedly toggle capture.

With FX installed in Applications and Apple Command Line Tools installed, quit FX and run on your Mac:

```bash
./scripts/build-fx-shortcut.sh --install
```

This builds only the launcher against FX's existing VM/GPU libraries, validates signatures, and keeps an original app backup. Initial Swift dependency downloads can be substantial. It supports the pinned FX 1.9-eac.2 build only.

Without `--install`, the command only prepares an app in `.local-state/shortcut/`. The shortcut source has built successfully and passed launcher startup/graphics self-tests; a live HD2 check of this shortcut is still pending. The stock shortcuts above have been checked with the user.

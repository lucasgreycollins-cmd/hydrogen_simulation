# Hydrogen Simulation

A fake virus prank built with Python and Pygame. It captures your desktop, overlays a realistic-looking app icon, and when you double-click it, takes over your screen with a sequence of scary visual effects — none of which actually harm your computer.

> **Safe to run.** All effects are purely visual. No files are modified, deleted, or encrypted.

---

## Effects

The simulation cycles through 11 phases, each ~7 seconds long:

| Phase | Description |
|---|---|
| Scroll | Desktop tiles and scrolls in all directions |
| Melt | Screen appears to drip downward |
| Matrix rain | Falling green characters |
| Chromatic aberration | RGB channels split apart |
| Wave | Sinusoidal distortion across the screen |
| Terminal | Fake hacking terminal with scrolling commands |
| Static | Corrupted TV signal with scanline noise |
| Tunnel | Shrinking vortex with rotation |
| Chaos | Everything at once — shake, glitches, popups, red alarm strobe |
| BSOD | Convincing Windows 10 Blue Screen of Death |
| Calm flash | Eerie pulsing light orbs |

Throughout the payload, a blinking **● REC** indicator and a **SECURE ERASE IN 04:47** countdown appear in the corners for extra effect.

---

## How to run

**1. Install dependencies**
```
pip install pygame Pillow
```

**2. Run**
```
python hydrogen.py
```

A boot terminal will type out a fake init sequence, then a small **hydrogen** app icon appears in the top-left corner of your screen. Double-click it to trigger the effects.

Press **Escape** to exit at any time.

---

## Requirements

- Python 3.9+
- `pygame`
- `Pillow`
- macOS (uses `ImageGrab` for the desktop capture)

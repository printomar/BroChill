# Bro Chill — Cortisol Guard

Local Windows desktop app. Watches for rage signals, fires absurd shitpost overlays. Distributed via GitHub clone-and-run, never installed/signed/notarized. Built primarily as Reel fuel and a star-bait repo, not a product.

## Architecture

**Detection layer (Python):** entry point `cortisolguard.py`. Detectors live in `detectors/` and each emit `RageEvent` objects via a shared callback. Stack: `pynput` (keyboard/mouse), `psutil` + `pywin32` (processes, event log).

**Overlay layer (Electron):** persistent background app in `electron/`. One hidden, transparent, fullscreen, always-on-top, frameless `BrowserWindow`. Renders bits from `electron/renderer/<bit_id>.html`. No frameworks, no build step — vanilla HTML/CSS/JS for fast iteration.

**IPC:** persistent Electron with an HTTP server on `localhost:<config.overlay.port>`. Python POSTs `{bit_id}` to `/trigger`. Electron loads the bit, shows the window. Click-anywhere → renderer sends `dismiss` IPC → main process hides window. Window stays hidden between triggers — never killed, never respawned.

**Lifecycle:** `cortisolguard.py` spawns Electron as a subprocess on startup, polls the port until reachable, then arms detectors. Ctrl+C in Python terminates Electron too.

**Bits:** `bits/bits.json` is the registry. Each bit = `{id, tier (1-3), weight, type, assets}`. Bit `id` maps 1:1 to `electron/renderer/<id>.html`. Selection is weighted random with no immediate repeats (logic lives in Electron).

## Detector contract

All detectors follow the keyboard detector pattern:
- Class instantiated with `(config, callback)`
- Emit `RageEvent(signal: str, intensity: float 0-1, trigger_key: str | None, timestamp: float)`
- Per-sub-detector cooldown to prevent event spam
- Thresholds and cooldowns live in `config.json`, never hardcoded
- `start()` / `stop()` / `join()` lifecycle

## Hard constraints

- Windows-only v1.
- No installer, signing, telemetry, accounts, or network calls beyond `localhost`.
- Runs as `python cortisolguard.py`. That's the install.
- Defender may flag global keystroke hook; document the exclusion in README, don't fight it.
- No stats, no reports, no settings UI beyond `config.json`. This is a shitpost.
- No frameworks in Electron renderer (no React, no Vue, no Tailwind). Vanilla. Bits should be readable as a single HTML file.
- Total codebase target: ~500 lines Python + ~200 lines Electron main + ~50-150 lines per bit. If a step blows past this, push back.

## Voice

Pure absurdist meme. Fake-corporate seriousness layered on stupid premises. "Production incident detected: you." "git blame yourself." "Your therapist is typing…" Voice should land harder in the bits than in the code or README — the README itself can be drier and let the screenshots carry the joke.

## Build order

1. ✅ Project skeleton + config loader + bit pool JSON schema
2. ✅ Keystroke velocity detection (sustained + same-key burst)
3. ✅ Electron overlay + persistent HTTP server + cortisol_spike hero bit (BSOD archived for Step 6 pool)
4. ❌ Tray icon (skipped) with cortisol meter (decaying float, separate persistent Electron window)
5. Remaining detectors: undo storm, mouse slam, crash detection, `cg run` wrapper for failed builds
6. Bit pool expansion (target: 12 bits at v1; mix of visual overlays, fake notifications, ironic breathing exercise, sound effects)
7. Sound effects layer (Web Audio in renderer, no external libs)
8. README with hero GIF, bit gallery, Defender exclusion docs, ironic disclaimers

Stop at each step. Demo. Iterate. Don't let the agent jump ahead or add scope.

## Known quirks (don't "fix" these)

- The keyboard detector catches the user mashing Ctrl+C to quit the script. This is a feature.
- Electron transparent fullscreen windows occasionally flicker on first show. Acceptable for v1.
- Defender may quarantine on first run. README handles it.
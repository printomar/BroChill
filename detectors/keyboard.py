from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass

from pynput import keyboard


@dataclass
class RageEvent:
    signal: str
    intensity: float   # 0.0 – 1.0
    trigger_key: str | None
    timestamp: float


class KeyboardDetector:
    def __init__(self, config: dict, on_rage):
        kb = config.get("keyboard", {})
        self._velocity_threshold: float = kb.get("velocity_threshold", 9)
        self._velocity_window: float    = kb.get("velocity_window", 3)
        self._burst_threshold: int      = kb.get("burst_threshold", 5)
        self._burst_window: float       = kb.get("burst_window", 1)
        self._cooldown: float           = kb.get("cooldown_seconds", 10)
        self._on_rage = on_rage

        self._timestamps: deque[float] = deque()
        self._key_times: defaultdict[str, deque[float]] = defaultdict(deque)

        self._last_velocity_fire: float = 0.0
        self._last_burst_fire: float    = 0.0

        self._listener = keyboard.Listener(on_press=self._on_press)
        self._listener.daemon = True

    # ------------------------------------------------------------------ #
    # pynput callback — runs on the listener thread                        #
    # ------------------------------------------------------------------ #

    def _on_press(self, key):
        now = time.monotonic()
        key_str = _key_name(key)
        self._check_velocity(now, key_str)
        self._check_burst(now, key_str)

    # ------------------------------------------------------------------ #
    # Sub-detectors                                                        #
    # ------------------------------------------------------------------ #

    def _check_velocity(self, now: float, key_str: str) -> None:
        q = self._timestamps
        q.append(now)
        cutoff = now - self._velocity_window
        while q and q[0] < cutoff:
            q.popleft()

        rate = len(q) / self._velocity_window
        if rate <= self._velocity_threshold:
            return
        if now - self._last_velocity_fire < self._cooldown:
            return

        self._last_velocity_fire = now
        # intensity: how far past the threshold, capped at 1
        intensity = min((rate - self._velocity_threshold) / self._velocity_threshold, 1.0)
        self._on_rage(RageEvent(
            signal="keystroke_velocity",
            intensity=round(intensity, 3),
            trigger_key=key_str,
            timestamp=time.time(),
        ))

    def _check_burst(self, now: float, key_str: str) -> None:
        q = self._key_times[key_str]
        q.append(now)
        cutoff = now - self._burst_window
        while q and q[0] < cutoff:
            q.popleft()

        count = len(q)
        if count < self._burst_threshold:
            return
        if now - self._last_burst_fire < self._cooldown:
            return

        self._last_burst_fire = now
        # intensity: 0.5 baseline + proportional overage, capped at 1
        intensity = min(0.5 + (count - self._burst_threshold) / self._burst_threshold * 0.5, 1.0)
        self._on_rage(RageEvent(
            signal="same_key_burst",
            intensity=round(intensity, 3),
            trigger_key=key_str,
            timestamp=time.time(),
        ))

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def start(self) -> None:
        self._listener.start()

    def join(self) -> None:
        self._listener.join()

    def stop(self) -> None:
        self._listener.stop()
        self._listener.join(timeout=1)


def _key_name(key) -> str:
    try:
        return key.char or repr(key)
    except AttributeError:
        return str(key)

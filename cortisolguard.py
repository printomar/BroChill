import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request

from detectors.keyboard import KeyboardDetector, RageEvent


def load_config(path: str = "config.json") -> dict:
    with open(path) as f:
        return json.load(f)


def find_electron_bin() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    candidate = os.path.join(here, "electron", "node_modules", ".bin", "electron.cmd")
    if not os.path.exists(candidate):
        sys.exit(
            "Electron not installed.\n"
            "Fix: cd electron && npm install"
        )
    return candidate


def spawn_electron() -> subprocess.Popen:
    bin_path = find_electron_bin()
    electron_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "electron")
    return subprocess.Popen(
        [bin_path, "."],
        cwd=electron_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def wait_for_overlay(port: int, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.3)
    return False


def trigger_overlay(port: int, bit_id: str) -> None:
    body = json.dumps({"bit_id": bit_id}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/trigger",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=2)
    except Exception:
        pass  # overlay may not be ready; skip silently


def main() -> None:
    config = load_config()
    overlay_cfg = config.get("overlay", {})
    port: int = overlay_cfg.get("port", 8765)
    overlay_enabled: bool = overlay_cfg.get("enabled", True)

    overlay_proc = None
    if overlay_enabled:
        overlay_proc = spawn_electron()
        print(f"Waiting for overlay on port {port}…")
        if wait_for_overlay(port):
            print(f"Overlay armed on port {port}.")
        else:
            print("Warning: overlay did not come up in time, continuing without it.")

    def on_rage(event: RageEvent) -> None:
        print(
            f"[RAGE] {event.signal}"
            f" | intensity={event.intensity:.2f}"
            f" | key={event.trigger_key!r}"
        )
        if overlay_enabled:
            trigger_overlay(port, "bsod")

    detector = KeyboardDetector(config, on_rage)

    def shutdown(sig, frame):
        print("\nCortisolGuard disarmed.")
        detector.stop()
        if overlay_proc:
            overlay_proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)

    print("CortisolGuard armed.")
    detector.start()
    detector.join()


if __name__ == "__main__":
    main()

import signal
import subprocess
import sys
import threading
from pathlib import Path

from watchfiles import Change, watch

ROOT = Path(__file__).resolve().parent.parent
WATCH_DIRS = [ROOT / "src", ROOT / "resources"]
COMMAND = [sys.executable, "-m", "evolix_ai"]


def start() -> subprocess.Popen:
    return subprocess.Popen(COMMAND, cwd=ROOT)


def stop(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def log_changes(changes: set[tuple[Change, str]]) -> None:
    paths = "\n  ".join(str(Path(path).relative_to(ROOT)) for _, path in changes)
    print(f"\nchanged:\n  {paths}\nrestarting ...", flush=True)


def main() -> int:
    stop_event = threading.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stop_event.set())

    process = start()
    print(f"watching {', '.join(str(d) for d in WATCH_DIRS)} ...", flush=True)

    try:
        for changes in watch(*WATCH_DIRS, stop_event=stop_event):
            log_changes(changes)
            stop(process)
            process = start()
    finally:
        stop(process)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

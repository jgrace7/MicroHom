import time


def say(msg=""):
    """Single place for all console output: '[HH:MM:SS] message'."""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def fmt_time(seconds):
    """12.3 s / 4 min 07 s / 1 h 05 min"""
    if seconds < 60:
        return f"{seconds:.1f} s"
    minutes, secs = divmod(seconds, 60)
    if minutes < 60:
        return f"{int(minutes)} min {int(round(secs)):02d} s"
    hours, minutes = divmod(minutes, 60)
    return f"{int(hours)} h {int(minutes):02d} min"


def tail(path, n=8):
    """Last n non-empty lines of a text file (used to show why a MOOSE run failed)."""
    try:
        with open(path, errors="replace") as f:
            return [ln.rstrip() for ln in f.read().splitlines() if ln.strip()][-n:]
    except OSError:
        return []

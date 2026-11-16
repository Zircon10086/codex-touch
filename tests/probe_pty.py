"""Exercise the diagnostic's terminal I/O on a synthetic PTY, without Android."""

import os
from pathlib import Path
import pty
import select
import signal
import subprocess
import termios
import time


PROBE = Path(__file__).resolve().parents[1] / "scripts" / "probe-termux-ime.sh"
ON = b"\x1b[?1000h\x1b[?1006h"
OFF = b"\x1b[?1006l\x1b[?1000l"


def exercise(window):
    master, slave = pty.openpty()
    saved = termios.tcgetattr(slave)
    args = ["bash", str(PROBE)] + (["--ime-window"] if window else [])
    proc = subprocess.Popen(args, stdin=slave, stdout=slave, stderr=slave)
    pending = bytearray()

    def through(marker):
        deadline = time.monotonic() + 4
        while marker not in pending:
            ready, _, _ = select.select([master], [], [], max(0, deadline - time.monotonic()))
            if not ready:
                raise AssertionError(f"probe did not emit {marker!r}")
            pending.extend(os.read(master, 4096))
        end = pending.index(marker) + len(marker)
        result = bytes(pending[:end])
        del pending[:end]
        return result

    try:
        assert ON in through(b"auto-exit: 45s)")
        # A slide out of the field and a wheel event must not open an IME window.
        os.write(master, b"\x1b[<0;2;2M\x1b[<0;8;3m")
        assert OFF not in through(b"tap 1: outside")
        os.write(master, b"\x1b[<64;2;2M\x1b[<0;2;2M\x1b[<0;2;2m")
        field = through(b"tap 2: field")
        if window:
            assert OFF + ON in field
        else:
            assert OFF not in field
        if window:
            proc.send_signal(signal.SIGTERM)
        else:
            os.write(master, b"q")
        assert OFF in through(b"\x1b[?1049l")
        assert proc.wait(timeout=3) == (143 if window else 0)
        assert termios.tcgetattr(slave) == saved, "probe left tty attributes changed"
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        os.close(master)
        os.close(slave)


if __name__ == "__main__":
    exercise(False)
    exercise(True)
    print("PASS: probe PTY (hit, miss, reporting window, quit, signal, terminal restoration).")

# ai-generated: 90% - Claude Code drafted, reviewed by me
"""Test runner for the compose `tests` profile (Lab 2 Stretch 3).

Waits for svcdesk's /health, runs the pytest suite, and prints `ITSMLAB-TESTS: passed=<n> failed=<m>` as the
last line of stdout. Exits 0 only when every test passed.
"""

import os
import sys
import time
import urllib.request

import pytest

URL = os.environ.get("SVCDESK_URL", "http://localhost:8080")


class Tally:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def pytest_runtest_logreport(self, report) -> None:
        if report.failed:
            self.failed += 1
        elif report.passed and report.when == "call":
            self.passed += 1


def wait_for_health(seconds: int = 60) -> None:
    deadline = time.monotonic() + seconds
    while True:
        try:
            with urllib.request.urlopen(f"{URL}/health", timeout=3) as response:
                if response.status == 200:
                    return
        except OSError:
            pass
        if time.monotonic() > deadline:
            return  # let the tests fail with a clear error instead of hanging
        time.sleep(1)


def main() -> None:
    wait_for_health()
    tally = Tally()
    code = pytest.main(["-q", "-p", "no:cacheprovider", os.path.dirname(os.path.abspath(__file__))],
                       plugins=[tally])
    sys.stdout.flush()
    print(f"ITSMLAB-TESTS: passed={tally.passed} failed={tally.failed}", flush=True)
    sys.exit(0 if code == 0 and tally.failed == 0 else 1)


if __name__ == "__main__":
    main()

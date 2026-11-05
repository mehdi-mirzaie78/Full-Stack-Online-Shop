"""Repeatable local/CI test runs, independent of root .env and development services."""

import argparse
import contextlib
import fcntl
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "server"
PYTHON = (
    str(SERVER / ".venv/bin/python") if (SERVER / ".venv/bin/python").exists() else sys.executable
)
COMPOSE = [
    "docker",
    "compose",
    "--env-file",
    os.devnull,
    "--project-name",
    "shop-tests",
    "--file",
    str(ROOT / "infra/compose.test.yml"),
]


def test_environment() -> dict[str, str]:
    # Keep tool discovery, but never pass inherited provider credentials or service URLs.
    allowed = ("PATH", "HOME", "USER", "TMPDIR", "CI", "E2E_BROWSER_CHANNEL")
    return {key: os.environ[key] for key in allowed if key in os.environ} | {
        "DJANGO_SETTINGS_MODULE": "config.test_settings",
        "SHOP_TEST_MODE": "1",
        "NEXT_TELEMETRY_DISABLED": "1",
        "OTEL_ENABLED": "false",
        "NEXT_PUBLIC_API_URL": "http://127.0.0.1:8100/api/v1",
        "NEXT_PUBLIC_MEDIA_URL": "http://127.0.0.1:59000/shop-test-media",
        "E2E_API_URL": "http://127.0.0.1:8100",
        "AWS_EC2_METADATA_DISABLED": "true",
        "NO_PROXY": "localhost,127.0.0.1,::1",
    }


def run(command: list[str], *, cwd: Path = ROOT, timeout: int = 300) -> None:
    subprocess.run(command, cwd=cwd, env=test_environment(), check=True, timeout=timeout)


def compose(*arguments: str) -> None:
    run([*COMPOSE, *arguments], timeout=600)


@contextlib.contextmanager
def test_services() -> Iterator[None]:
    compose("down", "--volumes", "--remove-orphans")
    try:
        compose("up", "--detach", "--wait", "--wait-timeout", "90")
        yield
    finally:
        compose("down", "--volumes", "--remove-orphans")


def backend_tests(integration_only: bool = False) -> None:
    run([PYTHON, "manage.py", "check"], cwd=SERVER)
    run([PYTHON, "manage.py", "makemigrations", "--check", "--dry-run"], cwd=SERVER)
    selection = (
        ["-m", "integration"]
        if integration_only
        else [
            "--cov=apps",
            "--cov-report=term-missing",
            "--cov-report=xml:coverage.xml",
            "--cov-fail-under=85",
        ]
    )
    run([PYTHON, "-m", "pytest", *selection, "--junitxml=server.junit.xml"], cwd=SERVER)


def wait_for_backend(process: subprocess.Popen) -> None:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("Test API exited; see test-results/api.log")
        try:
            with opener.open("http://127.0.0.1:8100/api/health/", timeout=1) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError):
            time.sleep(0.2)
    raise RuntimeError("Test API did not become healthy; see test-results/api.log")


def browser_tests() -> None:
    # Refuse to probe a server owned by another run or a developer.
    with socket.socket() as check:
        check.bind(("127.0.0.1", 8100))
    run([PYTHON, "manage.py", "migrate", "--noinput"], cwd=SERVER)
    run(["npm", "--prefix", "client", "run", "build"])
    reports = ROOT / "test-results"
    reports.mkdir(exist_ok=True)
    with (reports / "api.log").open("w") as log:
        process = subprocess.Popen(
            [PYTHON, "manage.py", "runserver", "127.0.0.1:8100", "--noreload"],
            cwd=SERVER,
            env=test_environment(),
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        try:
            wait_for_backend(process)
            run(["npm", "--prefix", "client", "run", "test:e2e"])
        finally:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "layer", choices=("unit", "integration", "backend", "e2e", "all", "up", "down")
    )
    arguments = parser.parse_args()
    # Fixed ports/project are deliberate; reject concurrent runs instead of sharing test data.
    with (Path(tempfile.gettempdir()) / "shop-tests.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.error("Another shop test run owns the test services.")
        if arguments.layer == "up":
            compose("up", "-d", "--wait", "--wait-timeout", "90")
            return
        if arguments.layer == "down":
            compose("down", "--volumes", "--remove-orphans")
            return
        if arguments.layer in ("unit", "all"):
            run(
                [
                    PYTHON,
                    "-m",
                    "unittest",
                    "discover",
                    "-s",
                    "scripts",
                    "-p",
                    "test_*.py",
                ]
            )
            run(["npm", "--prefix", "client", "run", "test:unit"])
        if arguments.layer == "unit":
            run([PYTHON, "-m", "pytest", "-m", "not integration"], cwd=SERVER)
            return
        with test_services():
            if arguments.layer in ("integration", "backend", "all"):
                backend_tests(integration_only=arguments.layer == "integration")
            if arguments.layer in ("e2e", "all"):
                browser_tests()


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(f"Test run failed: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)

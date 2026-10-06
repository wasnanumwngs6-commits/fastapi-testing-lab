"""Start the API, run the Postman collections with Newman, and stop the API."""

import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
COLLECTION = "postman/API-Testing-Lab.postman_collection.json"
ENVIRONMENT = "postman/local.postman_environment.json"


def wait_for_server(url: str, timeout: float = 30) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return True
        except OSError:
            time.sleep(0.5)
    return False


def run_newman(*args: str) -> int:
    command = ["newman", "run", COLLECTION, "-e", ENVIRONMENT, *args]
    return subprocess.run(command, shell=sys.platform == "win32", check=False).returncode


def stop_server(server: subprocess.Popen) -> None:
    if server.poll() is not None:
        return

    server.terminate()
    try:
        server.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait()


def main() -> int:
    Path("reports").mkdir(exist_ok=True)
    server = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ]
    )
    try:
        if not wait_for_server(f"{BASE_URL}/health"):
            print("FastAPI server did not start within 30 seconds.", file=sys.stderr)
            return 1
        if server.poll() is not None:
            return server.returncode or 1

        exit_code = run_newman(
            "--folder",
            "01-Unit-API-Tests",
            "--folder",
            "02-Integration-Flow",
            "-r",
            "cli,htmlextra",
            "--reporter-htmlextra-export",
            "reports/postman-report.html",
        )
        if exit_code != 0:
            return exit_code

        return run_newman(
            "--folder",
            "03-Data-Driven",
            "-d",
            "postman/data/products.csv",
            "-r",
            "cli",
        )
    finally:
        stop_server(server)


if __name__ == "__main__":
    sys.exit(main())

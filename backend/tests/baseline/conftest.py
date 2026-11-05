"""Independent process and database for v1 wire baselines; no app imports here."""
import json
import os
import select
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def worker(tmp_path_factory):
    root = tmp_path_factory.mktemp("v1-baseline")
    config = root / "config.yaml"
    config.write_text(f"cloud:\n  provider: local\nlocal:\n  data_dir: {root}\n  db_path: {root}/baseline.db\n")
    env = dict(os.environ, ENVIRONMENT="test", CONFIG_PATH=str(config),
               GOOGLE_CLIENT_ID="synthetic", GOOGLE_CLIENT_SECRET="synthetic",
               SECRET_KEY="synthetic-baseline-only-key", JWT_SECRET_KEY="synthetic-baseline-only-key",
               ALLOW_DEV_SEED="false", PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("worker.py"))],
                               env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True)

    def receive():
        assert select.select([process.stdout], [], [], 30)[0], "Baseline worker timed out"
        line = process.stdout.readline()
        assert line, "Baseline worker exited; inspect sanitized worker failure"
        return json.loads(line)

    assert receive() == {"ready": True}

    def call(command):
        process.stdin.write(json.dumps(command) + "\n")
        process.stdin.flush()
        return receive()

    try:
        yield call
    finally:
        process.stdin.close()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
        process.stdout.close()
        process.stderr.close()


@pytest.fixture
def api(worker):
    assert worker({"reset": True}) == {"reset": True}

    def request(method, path, actor="A", body=None):
        return worker({"method": method, "path": path, "actor": actor, "body": body})
    return request

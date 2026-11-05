"""Run complete application lifecycle in a fresh process/configuration/database."""
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path


def test_v1_offline_smoke(tmp_path):
    config = tmp_path / "config.yaml"
    config.write_text(f"cloud:\n  provider: local\nlocal:\n  data_dir: {tmp_path}\n  db_path: {tmp_path}/smoke.db\n")
    environment = dict(os.environ, ENVIRONMENT="test", CONFIG_PATH=str(config),
                       GOOGLE_CLIENT_ID="synthetic", GOOGLE_CLIENT_SECRET="synthetic",
                       SECRET_KEY=secrets.token_hex(32), JWT_SECRET_KEY=secrets.token_hex(32),
                       PYTHONPATH=str(Path(__file__).resolve().parents[2]))
    result = subprocess.run([sys.executable, str(Path(__file__).with_name("readiness_smoke_worker.py"))],
                            env=environment, capture_output=True, text=True, timeout=60)
    # Do not echo worker bodies/credentials if a future smoke assertion fails.
    assert result.returncode == 0, "Offline API smoke failed; inspect sanitized worker assertion name"
    report = json.loads(result.stdout)
    assert report["status"] == "passed" and report["checks"] >= 40
    assert not report["cloud_validated"]

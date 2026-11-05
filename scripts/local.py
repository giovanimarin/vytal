#!/usr/bin/env python3
"""Local-only Vytal launcher. No cloud, production credentials or Docker needed."""
import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def local_environment(root=ROOT):
    if os.environ.get("K_SERVICE") or os.environ.get("ENVIRONMENT", "local").lower() not in {"local", "dev", "development"}:
        raise ValueError("Local launcher refuses managed/production/unknown environments")
    directory = root / ".local-vytal"
    directory.mkdir(mode=0o700, exist_ok=True)
    keys = directory / "keys.json"
    try:
        descriptor = os.open(keys, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            json.dump({name: secrets.token_urlsafe(48) for name in ("SECRET_KEY", "JWT_SECRET_KEY")}, stream)
    except FileExistsError:
        pass
    # Two terminals may start together; only the exclusive creator writes keys.
    for attempt in range(20):
        try:
            stored = json.loads(keys.read_text())
            if set(stored) != {"SECRET_KEY", "JWT_SECRET_KEY"} or not all(isinstance(v, str) and v for v in stored.values()):
                raise ValueError("Invalid private local key file")
            break
        except json.JSONDecodeError:
            if attempt == 19:
                raise ValueError("Invalid private local key file") from None
            time.sleep(0.01)
    config = directory / "config.json"
    # JSON is valid YAML; avoids a launcher dependency before backend setup.
    config.write_text(json.dumps({"cloud": {"provider": "local"}, "local": {
        "data_dir": str(directory / "data"), "db_path": str(directory / "data/vytal.db")}}))
    return dict(os.environ, **stored, ENVIRONMENT="local", CONFIG_PATH=str(config),
                GOOGLE_CLIENT_ID="local-simulation-only", GOOGLE_CLIENT_SECRET="local-simulation-only",
                GOOGLE_REDIRECT_URI="http://localhost:8000/api/v1/connect/google_fit/callback",
                ALLOW_DEV_SEED="false", CORS_ORIGINS='["http://localhost:3000"]')


def python_path(root=ROOT):
    return root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["setup", "backend", "web", "android", "demo"])
    parser.add_argument("--email", help="Existing local account to receive synthetic demo data")
    parser.add_argument("--api-url", default="http://10.0.2.2:8000/api/v1", help="Android emulator/LAN API URL")
    parser.add_argument("--lan", action="store_true", help="Bind backend to LAN for a trusted physical device")
    args = parser.parse_args()
    try:
        env = local_environment()
    except (ValueError, OSError):
        raise SystemExit("Unable to initialize local configuration; never use this launcher in production") from None
    python = python_path()
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if args.command == "setup":
        if not python.exists():
            subprocess.run([sys.executable, "-m", "venv", str(ROOT / ".venv")], check=True)
        subprocess.run([str(python), "-m", "pip", "install", "-r", "requirements-prod.txt"], cwd=ROOT / "backend", check=True)
        if not npm:
            raise SystemExit("Install Node 22 and npm first")
        for folder, options in [("web", []), ("mobile/vytal-app", ["--legacy-peer-deps"])]:
            subprocess.run([npm, "ci", *options], cwd=ROOT / folder, check=True)
        print("Dependencies ready. Start backend and web in separate terminals.")
        return
    if not python.exists():
        raise SystemExit("Run python scripts/local.py setup first")
    if args.command == "backend":
        command = [str(python), "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0" if args.lan else "127.0.0.1", "--port", "8000"]
        folder = ROOT / "backend"
    elif args.command == "demo":
        if not args.email:
            parser.error("demo requires --email of an existing local account")
        command = [str(python), "scripts/seed_local_account.py", "--email", args.email]
        folder = ROOT / "backend"
    else:
        if not npm:
            raise SystemExit("Install Node 22 and npm first")
        if args.command == "web":
            env.update(NODE_ENV="development", VYTAL_BACKEND_URL="http://127.0.0.1:8000", NEXT_TELEMETRY_DISABLED="1")
            command, folder = [npm, "run", "dev"], ROOT / "web"
        else:
            env.update(NODE_ENV="development", EXPO_PUBLIC_API_URL=args.api_url, EXPO_NO_TELEMETRY="1", EXPO_OFFLINE="1")
            command, folder = [npm, "start", "--", "--go", "--lan" if args.lan else "--localhost"], ROOT / "mobile/vytal-app"
    try:
        subprocess.run(command, cwd=folder, env=env, check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as error:
        raise SystemExit(error.returncode) from None


if __name__ == "__main__":
    main()

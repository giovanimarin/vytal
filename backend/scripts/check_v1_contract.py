"""Compare public v1 OpenAPI against a Git base without using a developer database."""
import argparse
import json
import os
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def contract(backend: Path, config: Path) -> dict:
    env = dict(os.environ, CONFIG_PATH=str(config), ENVIRONMENT="local",
               GOOGLE_CLIENT_ID="synthetic-contract", GOOGLE_CLIENT_SECRET="synthetic-contract")
    raw = subprocess.check_output(
        [sys.executable, "-c", "import json; from app.main import app; print(json.dumps(app.openapi()))"],
        cwd=backend, env=env,
    )
    document = json.loads(raw)
    for path in document["paths"].values():
        for operation in path.values():
            if not isinstance(operation, dict):
                continue
            # Editorial docstring punctuation does not change the wire contract.
            operation.pop("description", None)
            if "parameters" not in operation:
                continue
            operation["parameters"].sort(key=lambda p: (p["in"], p["name"]))
            for parameter in operation["parameters"]:
                # Explicit Optional fixes describe existing None defaults; never relax
                # required identifiers, request bodies, security or response schemas.
                schema = parameter["schema"]
                if parameter["in"] == "query" and not parameter.get("required", False):
                    branches = schema.get("anyOf", [])
                    if branches == [{"type": "string"}, {"type": "null"}]:
                        del schema["anyOf"]
                        schema["type"] = "string"
    return document


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/master")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="vytal-contract-") as temp:
        work = Path(temp)
        archive = work / "base.tar"
        with archive.open("wb") as stream:
            subprocess.run(["git", "archive", args.base, "backend"], cwd=root, stdout=stream, check=True)
        with tarfile.open(archive) as source:
            source.extractall(work, filter="data")
        config = work / "config.yaml"
        config.write_text(f"cloud:\n  provider: local\nlocal:\n  data_dir: {work}\n  db_path: {work}/test.db\n")
        before, after = contract(work / "backend", config), contract(root / "backend", config)
        if before != after:
            raise SystemExit("Public OpenAPI contract differs beyond optional query nullability/order")
    print("Public OpenAPI compatible: paths, inputs, security and responses preserved")


if __name__ == "__main__":
    main()

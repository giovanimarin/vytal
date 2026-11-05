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
    env = dict(os.environ, CONFIG_PATH=str(config), ENVIRONMENT="test",
               GOOGLE_CLIENT_ID="synthetic-contract", GOOGLE_CLIENT_SECRET="synthetic-contract")
    raw = subprocess.check_output(
        [sys.executable, "-c", "import json; from app.main import app; print(json.dumps(app.openapi()))"],
        cwd=backend, env=env,
    )
    return normalize_contract(json.loads(raw))


def normalize_contract(document: dict) -> dict:
    """Ignore editorial descriptions only; preserve required/null/security/types.

    Strict equality is intentionally conservative, including additive changes:
    an intentional API change needs explicit baseline review, never auto-update.
    """
    import copy

    result = copy.deepcopy(document)

    maps = {"properties", "schemas", "paths", "content", "responses", "securitySchemes", "headers", "$defs"}
    literals = {"default", "enum", "const", "example", "examples"}

    def normalize(value, context=None):
        if isinstance(value, dict):
            if context not in maps:
                value.pop("description", None)
            for name, child in value.items():
                if name not in literals:
                    normalize(child, name)
            if isinstance(value.get("parameters"), list):
                value["parameters"].sort(key=lambda p: (p.get("in", ""), p.get("name", "")))
        elif isinstance(value, list):
            for child in value:
                normalize(child)

    normalize(result)
    return result


def assert_compatible(before: dict, after: dict, *, allow_additions: bool = False) -> None:
    if allow_additions:
        import copy
        after = copy.deepcopy(after)
        # Only additional endpoints/methods and component definitions are allowed.
        # Existing schemas/requirements/responses/security remain exact contracts.
        after['paths'] = {path: {key: after.get('paths', {}).get(path, {}).get(key)
                                for key in value} for path, value in before.get('paths', {}).items()}
        after['components'] = {section: {name: after.get('components', {}).get(section, {}).get(name)
                                        for name in definitions}
                               for section, definitions in before.get('components', {}).items()}
    if json.dumps(normalize_contract(before), sort_keys=True) != json.dumps(normalize_contract(after), sort_keys=True):
        raise ValueError("Public OpenAPI contract differs: review paths, inputs, security and responses")


def assert_wire_equal(before: dict, after: dict) -> None:
    """Exact observed JSON contract, including nulls and bool/int/float types."""
    if json.dumps(before, sort_keys=True) != json.dumps(after, sort_keys=True):
        raise ValueError("Observed v1 response contract differs")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/master")
    parser.add_argument("--snapshot", type=Path, help="Also compare with a versioned baseline (read only)")
    parser.add_argument("--allow-additions", action="store_true", help="Permit new operations/models, never modifications to existing contracts")
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
        try:
            assert_compatible(before, after, allow_additions=args.allow_additions)
            if args.snapshot:
                assert_compatible(json.loads(args.snapshot.read_text()), after, allow_additions=args.allow_additions)
        except ValueError as error:
            raise SystemExit(str(error)) from None
    print("Public OpenAPI compatible: paths, inputs, security and responses preserved")


if __name__ == "__main__":
    main()

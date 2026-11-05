"""Offline evidence, not a GCP validator. Never reads env, credentials or state.

Only parses committed HCL/schema/source files and runs DDL in in-memory SQLite.
--check is deliberately nonzero while known deployment blockers remain.
"""
import argparse
import ast
import json
import re
import sqlite3
from pathlib import Path

import hcl2

REFRESH_TYPES = {
    "token_id": "STRING", "user_id": "STRING", "token_hash": "STRING",
    "expires_at": "TIMESTAMP", "created_at": "TIMESTAMP", "revoked": "INT64",
}


def validate_refresh_schema(schema: list[dict]) -> list[str]:
    """Candidate contract only: does not infer constraints/engine guarantees."""
    errors = []
    names = [column["name"] for column in schema]
    if len(set(names)) != len(names) or set(names) != set(REFRESH_TYPES):
        errors.append("refresh-field-set")
    for column in schema:
        if column.get("type") != REFRESH_TYPES.get(column["name"]) or column.get("mode") != "REQUIRED":
            errors.append("refresh-column-contract")
    return sorted(set(errors))


def local_columns(source: str) -> dict[str, set[str]]:
    tree = ast.parse(source)
    ddl = next(ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "_SCHEMA_SQL" for t in node.targets))
    with sqlite3.connect(":memory:") as db:
        db.executescript(ddl)
        tables = [row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        return {table: {row[1] for row in db.execute('PRAGMA table_info("' + table + '")')} for table in tables}


def declared_schemas(module: Path) -> dict[str, list[dict]]:
    with (module / "main.tf").open() as file:
        hcl = hcl2.load(file)
    tables = next(block["tables"] for block in hcl["locals"] if "tables" in block)
    schemas = {}
    for table, definition in tables.items():
        # Read literal schema references only; do not evaluate HCL or providers.
        match = re.search(r'schemas/([a-z_]+\.json)', definition["schema"])
        if not match:
            raise ValueError("Unsupported schema reference; manual review required")
        schemas[table] = json.loads((module / "schemas" / match[1]).read_text())
    return schemas


def compare_tables(local: dict[str, set[str]], declared: dict[str, list[dict]]) -> list[dict]:
    findings = []
    for table, columns in sorted(local.items()):
        if table not in declared:
            findings.append({"id": "missing-table", "table": table, "severity": "blocking"})
            continue
        schema = declared[table]
        missing = columns - {column["name"] for column in schema}
        required = {column["name"] for column in schema if column.get("mode") == "REQUIRED"} - columns
        if missing or required:
            findings.append({"id": "column-mismatch", "table": table, "severity": "blocking",
                             "missing_columns": sorted(missing), "extra_required_columns": sorted(required)})
    return findings


def audit(root: Path) -> dict:
    module = root / "infrastructure/terraform/modules/gcp/bigquery"
    local = local_columns((root / "backend/app/adapters/cloud/local.py").read_text())
    declared = declared_schemas(module)
    candidate = json.loads((module / "schemas/proposed/refresh_tokens.json").read_text())
    findings = compare_tables(local, declared)
    findings.extend({"id": error, "severity": "blocking"} for error in validate_refresh_schema(candidate))
    # Explicit unresolved review items: a parse or schema test cannot clear them.
    findings.extend([
        {"id": "refresh-concurrency-unverified", "severity": "blocking"},
        {"id": "runtime-iam-config-image-unverified", "severity": "blocking"},
    ])
    provider = ast.parse((root / "backend/app/adapters/cloud/gcp.py").read_text())
    if any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
           and n.func.attr == "insert_rows_json" for n in ast.walk(provider)):
        findings.append({"id": "legacy-streaming-before-dml", "severity": "blocking"})
    return {"scope": "offline-static-only", "gcp_validated": False, "ready_for_deploy": False,
            "local_tables": sorted(local), "declared_bigquery_tables": sorted(declared), "findings": findings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if unresolved deployment blockers exist")
    args = parser.parse_args()
    result = audit(Path(__file__).resolve().parents[2])
    print(json.dumps(result, indent=2))
    return int(args.check and bool(result["findings"]))


if __name__ == "__main__":
    raise SystemExit(main())

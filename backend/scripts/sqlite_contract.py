"""Inspect literal SQLite DDL in memory, without importing app/settings/providers."""
import ast
import json
import sqlite3
from pathlib import Path


def sqlite_contract() -> dict:
    source = Path(__file__).resolve().parents[1] / "app/adapters/cloud/local.py"
    tree = ast.parse(source.read_text())
    ddl = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == "_SCHEMA_SQL" for t in node.targets))
    with sqlite3.connect(":memory:") as db:
        db.executescript(ddl)
        tables = {}
        for name, sql in db.execute("SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
            columns = [dict(zip(("cid", "name", "type", "notnull", "default", "pk"), row, strict=True))
                       for row in db.execute(f'PRAGMA table_info("{name}")')]
            indexes = []
            for _, index, unique, origin, partial in db.execute(f'PRAGMA index_list("{name}")').fetchall():
                indexes.append({"name": index, "unique": unique, "origin": origin, "partial": partial,
                                "columns": [r[2] for r in db.execute(f'PRAGMA index_info("{index}")')]})
            tables[name] = {"columns": columns, "indexes": sorted(indexes, key=lambda i: i["name"]),
                            "foreign_keys": [list(r) for r in db.execute(f'PRAGMA foreign_key_list("{name}")')],
                            "sql": " ".join(sql.split())}
        return {"tables": tables, "foreign_keys_enabled_by_default": db.execute("PRAGMA foreign_keys").fetchone()[0]}


if __name__ == "__main__":
    print(json.dumps(sqlite_contract(), sort_keys=True, indent=2))

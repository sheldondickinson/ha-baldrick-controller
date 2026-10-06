"""Private, bounded custom-xModel geometry imports and SQLite revisions."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import uuid
from pathlib import Path

from defusedxml import ElementTree

MAX_NODES = 12750
MAX_UPLOAD = 2 * 1024 * 1024
PALETTE = [
    [0, 255, 255],
    [255, 0, 255],
    [255, 255, 0],
    [0, 0, 255],
    [255, 80, 0],
    [0, 255, 0],
    [255, 0, 0],
]


def import_model(raw: bytes) -> dict:
    if len(raw) > MAX_UPLOAD:
        raise ValueError("Model exceeds 2 MiB")
    try:
        root = ElementTree.fromstring(
            raw, forbid_dtd=True, forbid_entities=True, forbid_external=True
        )
    except Exception as exc:
        raise ValueError("Unsafe or malformed model XML") from exc
    a = root.attrib
    if (
        root.tag != "custommodel"
        or a.get("DisplayAs", "Custom") != "Custom"
        or "CustomModel" not in a
    ):
        raise ValueError("Only custommodel geometry is supported")
    if a.get("StringType", "RGB Nodes") not in ("RGB Nodes", "3 Channel RGB"):
        raise ValueError("Only individually numbered RGB nodes are supported")
    nodes = {}
    rows = a["CustomModel"].split(";")
    if len(rows) > 2000 or len(a["CustomModel"]) > 1000000:
        raise ValueError("Geometry too large")
    for y, row in enumerate(rows):
        if len(row.split(",")) > 2000:
            raise ValueError("Geometry too wide")
        for x, token in enumerate(row.split(",")):
            if not token.strip() or token.strip() == "0":
                continue
            n = int(token)
            if n < 1 or n > MAX_NODES or n in nodes:
                raise ValueError("Duplicate or invalid node number")
            nodes[n] = [x, y]
    if not nodes or set(nodes) != set(range(1, len(nodes) + 1)):
        raise ValueError("Node numbering must be contiguous from 1")
    strings = {
        k: v
        for k, v in a.items()
        if k == "CustomStrings" or k.startswith("String") and k[6:].isdigit()
    }
    submodels = [dict(e.attrib) for e in root.findall("subModel")]
    return {
        "id": uuid.uuid4().hex,
        "title": a.get("name", "Uploaded model")[:120],
        "count": len(nodes),
        "coords": [nodes[n] for n in range(1, len(nodes) + 1)],
        "displayXScale": 1,
        "sourceSHA256": hashlib.sha256(raw).hexdigest(),
        "sourceStrings": strings,
        "submodels": submodels,
        "checkpoints": [
            {
                "id": "C01",
                "node": 1,
                "end": len(nodes),
                "kind": "start",
                "label": "Start — edit checkpoints",
                "colour": 0,
                "confirmed": False,
            }
        ],
        "provenance": "User upload; geometry only. String starts are suggestions, not physical turns.",
    }


def validate_checkpoints(points, count):
    if not points or len(points) > 1000 or points[0].get("node") != 1:
        raise ValueError("First checkpoint must start at node 1")
    prev = 0
    for i, p in enumerate(points):
        n = p.get("node")
        if (
            type(n) is not int
            or not prev < n <= count
            or type(p.get("colour")) is not int
            or not 0 <= p["colour"] < len(PALETTE)
        ):
            raise ValueError("Invalid checkpoint order or colour")
        p.update(
            id=f"C{i + 1:02}",
            end=points[i + 1]["node"] - 1 if i + 1 < len(points) else count,
            label=str(p.get("label", ""))[:160],
            confirmed=p.get("confirmed") is True,
        )
        prev = n
    return points


class Library:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute("PRAGMA journal_mode=WAL")
        # Identical, versioned migrations in development, test and production.
        for migration in sorted((Path(__file__).parent / "migrations").glob("*.sql")):
            self.db.executescript(migration.read_text())
        self.db.commit()

    def list(self, kind):
        if kind not in ("models", "instances"):
            raise ValueError("Invalid collection")
        return [
            json.loads(r[0])
            for r in self.db.execute(f"SELECT data FROM {kind} ORDER BY rowid")
        ]

    def get(self, kind, key):
        if kind not in ("models", "instances", "settings"):
            raise ValueError("Invalid collection")
        column = "key" if kind == "settings" else "id"
        r = self.db.execute(
            f"SELECT data FROM {kind} WHERE {column}=?", (key,)
        ).fetchone()
        if not r:
            raise ValueError("Saved item not found")
        return json.loads(r[0])

    def save(self, kind, data, source=None):
        if kind not in ("models", "instances"):
            raise ValueError("Invalid collection")
        key = data.setdefault("id", uuid.uuid4().hex)
        raw = json.dumps(data)
        active = self.db.execute(f"SELECT 1 FROM {kind} WHERE id=?", (key,)).fetchone()
        historical = self.db.execute(
            "SELECT 1 FROM revisions WHERE resource=? LIMIT 1", (key,)
        ).fetchone()
        if not active and historical:
            raise ValueError("A retired permanent identifier cannot be reused")
        with self.db:
            self.db.execute(
                "INSERT INTO revisions(kind,resource,data) VALUES(?,?,?)",
                (kind, key, raw),
            )
            if kind == "models":
                self.db.execute(
                    "INSERT INTO models(id,data,source) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                    (key, raw, source),
                )
            else:
                self.db.execute(
                    "INSERT INTO instances(id,data) VALUES(?,?) ON CONFLICT(id) DO UPDATE SET data=excluded.data",
                    (key, raw),
                )
        return data

    def remove(self, kind, key):
        if kind not in ("models", "instances"):
            raise ValueError("Invalid collection")
        if kind == "models" and any(
            i["model_id"] == key for i in self.list("instances")
        ):
            raise ValueError("Remove associated instances first")
        self.get(kind, key)
        with self.db:
            self.db.execute(
                "INSERT INTO revisions(kind,resource,data) VALUES(?,?,?)",
                (kind, key, json.dumps({"deleted": True})),
            )
            self.db.execute(f"DELETE FROM {kind} WHERE id=?", (key,))

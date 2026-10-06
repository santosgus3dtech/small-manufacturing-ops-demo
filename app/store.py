from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY,
    reference TEXT NOT NULL UNIQUE,
    customer TEXT NOT NULL,
    product TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    status TEXT NOT NULL,
    due_date TEXT NOT NULL,
    revenue_cents INTEGER NOT NULL,
    cost_cents INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY,
    actor_role TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    details TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

SEED_ORDERS = (
    ("MO-1048", "Atlas Studio", "Custom enclosure", 12, "In production", "2026-10-09", 184800, 106900),
    ("MO-1047", "Cedar Labs", "Sensor bracket", 30, "Quality check", "2026-10-08", 127500, 68400),
    ("MO-1046", "Northstar Design", "Display stand", 8, "Queued", "2026-10-14", 93600, 45100),
    ("MO-1045", "Lumen Robotics", "Cable guide set", 45, "Ready", "2026-10-07", 211500, 123200),
    ("MO-1044", "Harbor Workshop", "Prototype housing", 4, "Delivered", "2026-10-03", 116000, 57200),
    ("MO-1043", "Orbit Research", "Calibration jig", 6, "Delivered", "2026-10-01", 162000, 79800),
)


def connect(database_path: str | Path) -> sqlite3.Connection:
    path = str(database_path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(SCHEMA)
    if connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
        connection.executemany(
            """INSERT INTO orders
            (reference, customer, product, quantity, status, due_date, revenue_cents, cost_cents)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            SEED_ORDERS,
        )
        connection.execute(
            "INSERT INTO audit_log (actor_role, action, entity_type, details) VALUES ('system', 'seed', 'database', 'Synthetic portfolio fixtures created')"
        )
        connection.commit()
    return connection


def dashboard(connection: sqlite3.Connection) -> dict:
    summary = connection.execute(
        """SELECT COUNT(*) AS total_orders,
        SUM(CASE WHEN status NOT IN ('Delivered', 'Cancelled') THEN 1 ELSE 0 END) AS active_orders,
        SUM(revenue_cents) AS revenue_cents,
        SUM(revenue_cents - cost_cents) AS gross_profit_cents
        FROM orders"""
    ).fetchone()
    statuses = connection.execute(
        "SELECT status, COUNT(*) AS count FROM orders GROUP BY status ORDER BY count DESC, status"
    ).fetchall()
    return {
        **dict(summary),
        "gross_margin_percent": round(
            (summary["gross_profit_cents"] / summary["revenue_cents"] * 100) if summary["revenue_cents"] else 0,
            1,
        ),
        "status_counts": [dict(row) for row in statuses],
    }

from contextlib import contextmanager
import sqlite3
from pathlib import Path
from typing import Any, Iterator

DATABASE_PATH = Path(__file__).with_name("app.db")


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def create_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS shipments (
                tracking_id INTEGER PRIMARY KEY,
                sender TEXT NOT NULL,
                recipient TEXT NOT NULL,
                origin TEXT NOT NULL,
                destination TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                estimated_delivery TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        existing_columns = {
            row[1]
            for row in connection.execute("PRAGMA table_info(shipments)").fetchall()
        }
        columns_to_add = {
            "sender": "TEXT NOT NULL DEFAULT ''",
            "recipient": "TEXT NOT NULL DEFAULT ''",
            "origin": "TEXT NOT NULL DEFAULT ''",
            "destination": "TEXT NOT NULL DEFAULT ''",
            "estimated_delivery": "TEXT",
            "created_at": "TEXT NOT NULL DEFAULT ''",
        }
        for column, definition in columns_to_add.items():
            if column not in existing_columns:
                connection.execute(
                    f"ALTER TABLE shipments ADD COLUMN {column} {definition}"
                )
        connection.execute(
            "UPDATE shipments SET created_at = CURRENT_TIMESTAMP "
            "WHERE created_at IS NULL OR created_at = ''"
        )


def create_shipment(shipment: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO shipments
                (tracking_id, sender, recipient, origin, destination, status,
                 estimated_delivery, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
            (
                shipment["tracking_id"],
                shipment["sender"],
                shipment["recipient"],
                shipment["origin"],
                shipment["destination"],
                shipment["status"],
                shipment["estimated_delivery"],
            ),
        )
        row = connection.execute(
            "SELECT * FROM shipments WHERE tracking_id = ?",
            (shipment["tracking_id"],),
        ).fetchone()
    return dict(row)


def get_shipments() -> list[dict[str, Any]]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM shipments ORDER BY created_at DESC, tracking_id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_shipment(tracking_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM shipments WHERE tracking_id = ?", (tracking_id,)
        ).fetchone()
    return dict(row) if row else None


def update_shipment(
    tracking_id: int, updates: dict[str, Any]
) -> dict[str, Any] | None:
    if not updates:
        return get_shipment(tracking_id)

    updates = {
        key: value.isoformat() if hasattr(value, "isoformat") else value
        for key, value in updates.items()
    }
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = [*updates.values(), tracking_id]

    with get_connection() as connection:
        cursor = connection.execute(
            f"UPDATE shipments SET {assignments} WHERE tracking_id = ?", values
        )
        if cursor.rowcount == 0:
            return None
        row = connection.execute(
            "SELECT * FROM shipments WHERE tracking_id = ?", (tracking_id,)
        ).fetchone()
    return dict(row)


def delete_shipment(tracking_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM shipments WHERE tracking_id = ?", (tracking_id,)
        )
    return cursor.rowcount > 0

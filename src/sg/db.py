"""SQLite persistence layer for Sg."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA_VERSION = 19

# Tables that belonged to the removed story pipeline; dropped when migrating.
_LEGACY_TABLES = ("chapters", "scenes", "locations", "assets", "jobs", "site_adapters")


@dataclass(slots=True)
class Project:
    id: int | None
    name: str
    description: str
    created_at: str
    updated_at: str


@dataclass(slots=True)
class Provider:
    id: int | None
    name: str
    kind: str
    base_url: str
    api_key: str
    default_model: str
    created_at: str
    updated_at: str


class Database:
    """Thin wrapper around a SQLite connection holding the app's data."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = str(path)
        self._conn = sqlite3.connect(self.path)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._migrate()

    def _migrate(self) -> None:
        with self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS providers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    kind TEXT NOT NULL DEFAULT 'custom',
                    base_url TEXT NOT NULL DEFAULT '',
                    api_key TEXT NOT NULL DEFAULT '',
                    default_model TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
                )
                """
            )
            for table in _LEGACY_TABLES:
                self._conn.execute(f"DROP TABLE IF EXISTS {table}")
            self._conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    # ------------------------------------------------------------- projects
    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> Project:
        return Project(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_projects(self) -> list[Project]:
        rows = self._conn.execute(
            "SELECT * FROM projects ORDER BY updated_at DESC, id DESC"
        ).fetchall()
        return [self._row_to_project(row) for row in rows]

    def get_project(self, project_id: int) -> Project | None:
        row = self._conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return self._row_to_project(row) if row else None

    def create_project(self, name: str, description: str = "") -> Project:
        with self._conn:
            cursor = self._conn.execute(
                "INSERT INTO projects (name, description) VALUES (?, ?)",
                (name, description),
            )
        project = self.get_project(int(cursor.lastrowid))
        assert project is not None
        return project

    def update_project(
        self,
        project_id: int,
        name: str,
        description: str = "",
    ) -> Project | None:
        with self._conn:
            self._conn.execute(
                """
                UPDATE projects
                SET name = ?, description = ?,
                    updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
                WHERE id = ?
                """,
                (name, description, project_id),
            )
        return self.get_project(project_id)

    def delete_project(self, project_id: int) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))

    # ------------------------------------------------------------ providers
    @staticmethod
    def _row_to_provider(row: sqlite3.Row) -> Provider:
        return Provider(
            id=row["id"],
            name=row["name"],
            kind=row["kind"],
            base_url=row["base_url"],
            api_key=row["api_key"],
            default_model=row["default_model"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def list_providers(self) -> list[Provider]:
        rows = self._conn.execute("SELECT * FROM providers ORDER BY id ASC").fetchall()
        return [self._row_to_provider(row) for row in rows]

    def get_provider(self, provider_id: int) -> Provider | None:
        row = self._conn.execute("SELECT * FROM providers WHERE id = ?", (provider_id,)).fetchone()
        return self._row_to_provider(row) if row else None

    def create_provider(
        self,
        name: str,
        kind: str,
        base_url: str,
        api_key: str = "",
        default_model: str = "",
    ) -> Provider:
        with self._conn:
            cursor = self._conn.execute(
                """
                INSERT INTO providers (name, kind, base_url, api_key, default_model)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, kind, base_url, api_key, default_model),
            )
        provider = self.get_provider(int(cursor.lastrowid))
        assert provider is not None
        return provider

    def update_provider(
        self,
        provider_id: int,
        name: str,
        kind: str,
        base_url: str,
        api_key: str = "",
        default_model: str = "",
    ) -> Provider | None:
        with self._conn:
            self._conn.execute(
                """
                UPDATE providers
                SET name = ?, kind = ?, base_url = ?, api_key = ?, default_model = ?,
                    updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
                WHERE id = ?
                """,
                (name, kind, base_url, api_key, default_model, provider_id),
            )
        return self.get_provider(provider_id)

    def delete_provider(self, provider_id: int) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM providers WHERE id = ?", (provider_id,))

    # -------------------------------------------------------------- settings
    def get_setting(self, key: str, default: str | None = None) -> str | None:
        row = self._conn.execute("SELECT value FROM app_settings WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def get_settings(self, prefix: str = "") -> dict[str, str]:
        """Return settings whose key starts with ``prefix``, as a mapping."""
        rows = self._conn.execute(
            "SELECT key, value FROM app_settings WHERE key LIKE ? || '%'", (prefix,)
        ).fetchall()
        return {row["key"]: row["value"] for row in rows}

    def set_setting(self, key: str, value: str) -> None:
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO app_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
                """,
                (key, value),
            )

    def set_settings(self, values: dict[str, str]) -> None:
        """Upsert several settings in one transaction."""
        with self._conn:
            self._conn.executemany(
                """
                INSERT INTO app_settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    updated_at = strftime('%Y-%m-%d %H:%M:%f', 'now')
                """,
                list(values.items()),
            )

    def delete_setting(self, key: str) -> None:
        with self._conn:
            self._conn.execute("DELETE FROM app_settings WHERE key = ?", (key,))

    def close(self) -> None:
        self._conn.close()

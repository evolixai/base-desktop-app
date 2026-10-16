import sqlite3
from pathlib import Path

from evolix_ai.db import Database


def test_create_and_list() -> None:
    db = Database()
    assert db.list_projects() == []

    project = db.create_project("Alpha", "first")
    assert project.id is not None
    assert project.name == "Alpha"
    assert project.description == "first"

    projects = db.list_projects()
    assert [p.id for p in projects] == [project.id]


def test_get_missing_returns_none() -> None:
    db = Database()
    assert db.get_project(999) is None


def test_migrates_legacy_projects_table(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%d %H:%M:%f', 'now'))
        )
        """
    )
    conn.execute("INSERT INTO projects (name, description) VALUES ('Legacy', 'old')")
    conn.commit()
    conn.close()

    db = Database(path)
    project = db.list_projects()[0]
    assert project.name == "Legacy"
    assert project.description == "old"


def test_drops_legacy_story_tables(tmp_path: Path) -> None:
    path = tmp_path / "legacy.sqlite3"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE chapters (id INTEGER PRIMARY KEY, project_id INTEGER, source_url TEXT)"
    )
    conn.commit()
    conn.close()

    db = Database(path)

    names = {
        row["name"]
        for row in db._conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    }
    assert "chapters" not in names


def test_update_project() -> None:
    db = Database()
    project = db.create_project("Alpha")

    updated = db.update_project(project.id, "Beta", "changed")
    assert updated is not None
    assert updated.name == "Beta"
    assert updated.description == "changed"
    assert db.get_project(project.id).name == "Beta"


def test_update_missing_returns_none() -> None:
    db = Database()
    assert db.update_project(999, "Ghost") is None


def test_delete_project() -> None:
    db = Database()
    project = db.create_project("Alpha")
    db.delete_project(project.id)
    assert db.list_projects() == []


def test_listing_orders_most_recently_updated_first() -> None:
    db = Database()
    older = db.create_project("Older")
    newer = db.create_project("Newer")

    with db._conn:
        db._conn.execute(
            "UPDATE projects SET updated_at = '2000-01-01 00:00:00.000' WHERE id = ?",
            (older.id,),
        )

    assert [p.id for p in db.list_projects()] == [newer.id, older.id]


def test_create_and_list_providers() -> None:
    db = Database()
    assert db.list_providers() == []

    provider = db.create_provider("Zen", "zen", "https://opencode.ai/zen/v1", "sk-1", "gpt-5.2")
    assert provider.id is not None
    assert provider.kind == "zen"
    assert provider.api_key == "sk-1"
    assert provider.default_model == "gpt-5.2"

    assert [p.id for p in db.list_providers()] == [provider.id]


def test_get_missing_provider_returns_none() -> None:
    db = Database()
    assert db.get_provider(999) is None


def test_update_provider() -> None:
    db = Database()
    provider = db.create_provider("Custom", "custom", "https://example.com/v1")

    updated = db.update_provider(
        provider.id, "Local", "custom", "https://localhost:1234/v1", "key", "llama"
    )
    assert updated is not None
    assert updated.name == "Local"
    assert updated.base_url == "https://localhost:1234/v1"
    assert db.get_provider(provider.id).api_key == "key"


def test_delete_provider() -> None:
    db = Database()
    provider = db.create_provider("Go", "go", "https://opencode.ai/zen/go/v1")
    db.delete_provider(provider.id)
    assert db.list_providers() == []


def test_settings_roundtrip() -> None:
    db = Database()
    assert db.get_setting("chat.provider") is None
    assert db.get_setting("chat.provider", "fallback") == "fallback"

    db.set_setting("chat.provider", "1")
    db.set_setting("other.key", "x")
    assert db.get_setting("chat.provider") == "1"

    db.set_setting("chat.provider", "2")
    assert db.get_setting("chat.provider") == "2"

    assert db.get_settings("chat.") == {"chat.provider": "2"}

    db.delete_setting("chat.provider")
    assert db.get_setting("chat.provider") is None


def test_set_settings_bulk() -> None:
    db = Database()
    db.set_settings({"chat.provider": "1", "chat.model": "m"})

    assert db.get_settings("chat.") == {"chat.provider": "1", "chat.model": "m"}

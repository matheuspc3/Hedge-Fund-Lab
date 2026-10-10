import sqlite3

import pytest

from scripts.repair_sqlite_database import repair_database


def test_repair_database_deduplicates_and_creates_backup(tmp_path):
    database = tmp_path / "test.db"
    with sqlite3.connect(database) as connection:
        for table in ("cotacoes_diarias", "indicadores_tecnicos"):
            connection.execute(
                f"CREATE TABLE {table} (id INTEGER PRIMARY KEY, ativo_id INTEGER, data TEXT)"
            )
            connection.executemany(
                f"INSERT INTO {table} (ativo_id, data) VALUES (?, ?)",
                [(1, "2025-01-02"), (1, "2025-01-02")],
            )

    backup = repair_database(database)
    assert backup.is_file()
    with sqlite3.connect(database) as connection:
        assert (
            connection.execute("SELECT COUNT(*) FROM cotacoes_diarias").fetchone()[0] == 1
        )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                "INSERT INTO cotacoes_diarias (ativo_id, data) VALUES (1, '2025-01-02')"
            )


def test_repair_database_refuses_to_overwrite_backup(tmp_path):
    database = tmp_path / "test.db"
    database.touch()
    database.with_suffix(".db.bak").touch()
    with pytest.raises(FileExistsError):
        repair_database(database)

"""Remove duplicatas antigas do SQLite e cria índices únicos.

O script sempre cria um backup antes de alterar o banco:
    python scripts/repair_sqlite_database.py hedgefundlab.db
"""

import argparse
import shutil
import sqlite3
from pathlib import Path


def repair_database(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    backup = path.with_suffix(path.suffix + ".bak")
    if backup.exists():
        raise FileExistsError(f"backup already exists: {backup}")
    shutil.copy2(path, backup)

    with sqlite3.connect(path) as connection:
        for table in ("cotacoes_diarias", "indicadores_tecnicos"):
            connection.execute(
                f"""DELETE FROM {table}
                WHERE id NOT IN (
                    SELECT MAX(id) FROM {table} GROUP BY ativo_id, data
                )"""
            )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_cotacao_ativo_data "
            "ON cotacoes_diarias (ativo_id, data)"
        )
        connection.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_indicador_ativo_data "
            "ON indicadores_tecnicos (ativo_id, data)"
        )
    return backup


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("database", type=Path)
    args = parser.parse_args()
    backup = repair_database(args.database)
    print(f"Banco reparado. Backup: {backup}")


if __name__ == "__main__":
    main()

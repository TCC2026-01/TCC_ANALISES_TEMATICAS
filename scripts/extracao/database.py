# -*- coding: utf-8 -*-
"""
Camada de persistência da extração.

Compatibilidades:
- adiciona init_db() para funcionar com main.py
- suporta banco antigo com coluna id em professores
- tabela projetos inclui data_inicio e data_fim
"""

import sqlite3
from contextlib import closing


def clean_value(value):
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


class DatabaseManager:
    def __init__(self, db_name="integra.db"):
        self.db_name = db_name
        self._create_tables()

    def init_db(self):
        self._create_tables()

    def _connect(self):
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 5000")
        return conn

    def _column_exists(self, table_name, column_name):
        with closing(self._connect()) as conn:
            cur = conn.execute(f"PRAGMA table_info({table_name})")
            cols = [row[1] for row in cur.fetchall()]
            return column_name in cols

    def _ensure_column(self, table_name, column_name, column_type="TEXT"):
        if not self._column_exists(table_name, column_name):
            with closing(self._connect()) as conn, conn:
                conn.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                )

    def _create_tables(self):
        with closing(self._connect()) as conn, conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS professores (
                    professor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sigla TEXT NOT NULL,
                    nome TEXT,
                    campus TEXT,
                    cargo TEXT,
                    slug TEXT NOT NULL,
                    url_final TEXT,
                    UNIQUE(sigla, slug)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS tccs (
                    tcc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    slug_professor TEXT,
                    nome_professor TEXT,
                    sigla TEXT,
                    instituicao TEXT,
                    uf TEXT,
                    campus TEXT,
                    ano TEXT,
                    curso TEXT,
                    autores TEXT,
                    titulo TEXT,
                    resumo TEXT,
                    palavras_chaves TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS artigos (
                    artigo_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    slug_professor TEXT,
                    nome_professor TEXT,
                    sigla TEXT,
                    ano TEXT,
                    titulo TEXT,
                    journal TEXT,
                    doi TEXT,
                    palavras_chaves TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS projetos (
                    projeto_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    professor_id INTEGER NOT NULL,
                    slug_professor TEXT,
                    nome_professor TEXT,
                    sigla TEXT,
                    titulo TEXT,
                    descricao TEXT,
                    natureza TEXT,
                    equipe TEXT,
                    financiadores TEXT,
                    data_inicio TEXT,
                    data_fim TEXT
                )
            """)

            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_professores_sigla_slug ON professores(sigla, slug)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tccs_professor ON tccs(professor_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_artigos_professor ON artigos(professor_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_projetos_professor ON projetos(professor_id)"
            )

        # garante colunas novas em bancos já existentes
        self._ensure_column("projetos", "data_inicio", "TEXT")
        self._ensure_column("projetos", "data_fim", "TEXT")

    def save_professores(self, sigla, professores):
        if not professores:
            return

        rows = [
            (
                clean_value(sigla),
                clean_value(p.get("nome")),
                clean_value(p.get("campus")),
                clean_value(p.get("cargo")),
                clean_value(p.get("slug")),
                clean_value(p.get("url_final")),
            )
            for p in professores
            if p.get("slug")
        ]

        with closing(self._connect()) as conn, conn:
            conn.executemany("""
                INSERT OR IGNORE INTO professores
                (sigla, nome, campus, cargo, slug, url_final)
                VALUES (?, ?, ?, ?, ?, ?)
            """, rows)

    def get_professor_id(self, sigla, slug):
        sigla = clean_value(sigla)
        slug = clean_value(slug)

        with closing(self._connect()) as conn:
            cur = conn.execute("PRAGMA table_info(professores)")
            cols = [row[1] for row in cur.fetchall()]

            id_col = "professor_id" if "professor_id" in cols else "id"

            cur = conn.execute(
                f"""
                SELECT {id_col}
                FROM professores
                WHERE sigla = ? AND slug = ?
                """,
                (sigla, slug),
            )
            row = cur.fetchone()
            return row[0] if row else None

    def _insert_many(self, sql, rows):
        if not rows:
            return
        with closing(self._connect()) as conn, conn:
            conn.executemany(sql, rows)

    def save_tccs(self, rows):
        self._insert_many("""
            INSERT INTO tccs (
                professor_id, slug_professor, nome_professor, sigla,
                instituicao, uf, campus, ano, curso, autores,
                titulo, resumo, palavras_chaves
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

    def save_artigos(self, rows):
        self._insert_many("""
            INSERT INTO artigos (
                professor_id, slug_professor, nome_professor, sigla,
                ano, titulo, journal, doi, palavras_chaves
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

    def save_projetos(self, rows):
        self._insert_many("""
            INSERT INTO projetos (
                professor_id, slug_professor, nome_professor, sigla,
                titulo, descricao, natureza, equipe, financiadores,
                data_inicio, data_fim
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

    def get_status_summary(self):
        resumo = {}

        with closing(self._connect()) as conn:
            cur = conn.execute("SELECT DISTINCT sigla FROM professores ORDER BY sigla")
            siglas = [row[0] for row in cur.fetchall()]

            for sigla in siglas:
                total_prof = conn.execute(
                    "SELECT COUNT(*) FROM professores WHERE sigla = ?",
                    (sigla,)
                ).fetchone()[0]

                total_tcc = conn.execute("""
                    SELECT COUNT(*)
                    FROM tccs
                    WHERE professor_id IN (
                        SELECT professor_id FROM professores WHERE sigla = ?
                    )
                """, (sigla,)).fetchone()[0] if self._column_exists("professores", "professor_id") else conn.execute("""
                    SELECT COUNT(*)
                    FROM tccs
                    WHERE professor_id IN (
                        SELECT id FROM professores WHERE sigla = ?
                    )
                """, (sigla,)).fetchone()[0]

                total_art = conn.execute("""
                    SELECT COUNT(*)
                    FROM artigos
                    WHERE professor_id IN (
                        SELECT professor_id FROM professores WHERE sigla = ?
                    )
                """, (sigla,)).fetchone()[0] if self._column_exists("professores", "professor_id") else conn.execute("""
                    SELECT COUNT(*)
                    FROM artigos
                    WHERE professor_id IN (
                        SELECT id FROM professores WHERE sigla = ?
                    )
                """, (sigla,)).fetchone()[0]

                total_proj = conn.execute("""
                    SELECT COUNT(*)
                    FROM projetos
                    WHERE professor_id IN (
                        SELECT professor_id FROM professores WHERE sigla = ?
                    )
                """, (sigla,)).fetchone()[0] if self._column_exists("professores", "professor_id") else conn.execute("""
                    SELECT COUNT(*)
                    FROM projetos
                    WHERE professor_id IN (
                        SELECT id FROM professores WHERE sigla = ?
                    )
                """, (sigla,)).fetchone()[0]

                resumo[sigla] = {
                    "professores": total_prof,
                    "tccs": total_tcc,
                    "artigos": total_art,
                    "projetos": total_proj,
                }

        return resumo
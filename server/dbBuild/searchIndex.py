import os
import sqlite3
import time


FTS_SQL = """
CREATE VIRTUAL TABLE IF NOT EXISTS textMapFts USING fts5(
    hash UNINDEXED,
    lang UNINDEXED,
    content,
    content='textMap',
    content_rowid='id',
    tokenize='trigram'
)
"""

EXTRA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS dialogue_talkId_coopQuestId_index ON dialogue(talkId, coopQuestId)",
    "CREATE INDEX IF NOT EXISTS questTalk_questId_index ON questTalk(questId)",
]


def supports_trigram_fts(conn):
    try:
        conn.execute("CREATE VIRTUAL TABLE temp._fts_trigram_test USING fts5(content, tokenize='trigram')")
        conn.execute("DROP TABLE temp._fts_trigram_test")
        return True
    except sqlite3.Error:
        return False


def rebuild_search_index(conn):
    started = time.time()
    for sql in EXTRA_INDEXES:
        conn.execute(sql)

    if supports_trigram_fts(conn):
        conn.execute(FTS_SQL)
        conn.execute("INSERT INTO textMapFts(textMapFts) VALUES('rebuild')")
        backend = "fts_trigram"
    else:
        backend = "like"
        print("SQLite FTS5 trigram is unavailable, keyword search will fallback to LIKE.")

    conn.execute("ANALYZE")
    conn.commit()
    return backend, (time.time() - started) * 1000


def rebuild_database(db_path):
    conn = sqlite3.connect(db_path)
    try:
        backend, elapsed_ms = rebuild_search_index(conn)
        text_count = conn.execute("SELECT COUNT(*) FROM textMap").fetchone()[0]
        fts_count = None
        if backend == "fts_trigram":
            fts_count = conn.execute("SELECT COUNT(*) FROM textMapFts").fetchone()[0]
        print(f"{db_path}: backend={backend} textMap={text_count} textMapFts={fts_count} elapsed={elapsed_ms:.2f}ms")
    finally:
        conn.close()


def main():
    server_dir = os.path.dirname(os.path.dirname(__file__))
    for file_name in ["data.db", "starrail-data.db"]:
        db_path = os.path.join(server_dir, file_name)
        if os.path.exists(db_path):
            rebuild_database(db_path)
        else:
            print(f"skip missing database: {db_path}")


if __name__ == "__main__":
    main()

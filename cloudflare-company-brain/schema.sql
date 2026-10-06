CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  doc TEXT NOT NULL,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  text TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_chunks_type ON chunks(type);

CREATE TABLE IF NOT EXISTS query_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL DEFAULT (datetime('now')),
  question TEXT NOT NULL,
  answered INTEGER NOT NULL,
  top_score REAL,
  reason TEXT
);

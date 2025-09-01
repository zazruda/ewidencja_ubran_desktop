import sqlite3
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path.home() / "EwidencjaUbran" / "ewidencja.db"

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT,
    position TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    email TEXT,
    phone TEXT
);

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT,
    size TEXT,
    color TEXT,
    inv_number TEXT UNIQUE,
    min_stock INTEGER NOT NULL DEFAULT 0,
    stock INTEGER NOT NULL DEFAULT 0,
    location TEXT,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue_date TEXT NOT NULL,
    employee_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'Wydane',
    expected_return TEXT,
    FOREIGN KEY(employee_id) REFERENCES employees(id),
    FOREIGN KEY(item_id) REFERENCES items(id)
);

CREATE TABLE IF NOT EXISTS returns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    return_date TEXT NOT NULL,
    issue_id INTEGER NOT NULL,
    qty INTEGER NOT NULL DEFAULT 1,
    state_after TEXT,
    FOREIGN KEY(issue_id) REFERENCES issues(id)
);

CREATE TABLE IF NOT EXISTS movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    move_date TEXT NOT NULL,
    move_type TEXT NOT NULL, -- Przyjęcie, Wydanie, Zwrot, Korekta+
    item_id INTEGER NOT NULL,
    employee_id INTEGER,
    qty INTEGER NOT NULL,
    note TEXT,
    FOREIGN KEY(item_id) REFERENCES items(id),
    FOREIGN KEY(employee_id) REFERENCES employees(id)
);

-- Indexes to speed up common queries
CREATE INDEX IF NOT EXISTS idx_items_stock_min ON items(stock, min_stock);
CREATE INDEX IF NOT EXISTS idx_items_inv ON items(inv_number);
CREATE INDEX IF NOT EXISTS idx_employees_active ON employees(active);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_employee ON issues(employee_id);
CREATE INDEX IF NOT EXISTS idx_movements_item_date ON movements(item_id, move_date);
"""

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.commit()

def query(sql, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
    return rows

def execute(sql, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid

@contextmanager
def transaction():
    """Context manager for a single-connection transaction.
    Usage:
        with transaction() as conn:
            conn.execute("INSERT ...")
            conn.execute("UPDATE ...")
    """
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

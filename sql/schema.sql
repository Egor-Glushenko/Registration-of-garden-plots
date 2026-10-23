-- Garden Plot Registry: SQLite schema (PR7 coursework deliverable)
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS owners (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    phone TEXT NOT NULL,
    email TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS plots (
    id INTEGER PRIMARY KEY,
    plot_number TEXT NOT NULL UNIQUE,
    area_sqm REAL NOT NULL CHECK (area_sqm > 0),
    status TEXT NOT NULL CHECK (status IN ('free', 'occupied', 'leased', 'disputed')),
    owner_id INTEGER REFERENCES owners(id) ON DELETE SET NULL,
    debt REAL NOT NULL DEFAULT 0 CHECK (debt >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY,
    owner_id INTEGER NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
    amount REAL NOT NULL CHECK (amount > 0),
    payment_date TEXT NOT NULL,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_plots_owner_id ON plots(owner_id);
CREATE INDEX IF NOT EXISTS idx_payments_owner_date ON payments(owner_id, payment_date);

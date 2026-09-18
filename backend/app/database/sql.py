user_table_query = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_key_hash VARCHAR(64) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

user_api_key_column_query = """
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key_hash VARCHAR(64) UNIQUE;
"""

link_table_query = """
CREATE TABLE IF NOT EXISTS links (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    original_url TEXT NOT NULL,
    short_code VARCHAR(20) UNIQUE NOT NULL,
    click_count INTEGER NOT NULL DEFAULT 0,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""

link_click_count_index_query = """
CREATE INDEX IF NOT EXISTS idx_links_click_count ON links (click_count DESC);
"""

ALL_QUERY = [user_table_query, user_api_key_column_query, link_table_query, link_click_count_index_query]

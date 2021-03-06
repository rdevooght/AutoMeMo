CREATE TABLE IF NOT EXISTS snapshots (
    snapshot_id INTEGER PRIMARY KEY,
    website_name TEXT,
    queried_url TEXT,
    scraped_url TEXT,
    snapshot_date DATETIME,
    path_to_source TEXT,
    path_to_screenshot TEXT,
    path_to_archive TEXT,
    failed INTEGER DEFAULT 0
    metadata TEXT
);
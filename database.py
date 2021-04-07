import sqlite3
import configparser
import json

def read_config(section='DEFAULT'):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']

CONFIG = read_config()

def save_snapshot(metadata) -> str:
    '''
    Saves the metadata in a more structured way in a sqlite db
    returns the id of the snapshot
    '''

    path_to_source = metadata['folder_path']+metadata['source']['filename'] if metadata['source']['saved'] else None
    path_to_screenshot = metadata['folder_path']+metadata['screenshot']['filename'] if metadata['screenshot']['saved'] else None
    path_to_archive = metadata['folder_path']+metadata['mhtml_archive']['filename'] if metadata['mhtml_archive']['saved'] else None
    
    values = (
        metadata['name'], metadata['queried_url'], metadata['scraped_url'],
        path_to_source, path_to_screenshot, path_to_archive, metadata['scrape_time'],
        json.dumps(metadata)
    )
    
    con = sqlite3.connect(CONFIG['path_to_db'])
    cursor = con.cursor()
    query = '''INSERT INTO snapshots(
        website_name, queried_url, scraped_url, path_to_source, path_to_screenshot, path_to_archive,
        snapshot_date, metadata
    ) VALUES (?,?,?,?,?,?,?,?)
    '''
    cursor.execute(query, values)

    snapshot_id = cursor.lastrowid

    # Commit and close connection to db
    con.commit()
    con.close()

    return snapshot_id

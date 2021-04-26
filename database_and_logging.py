import sqlite3
import configparser
import json
import logging
import pandas as pd

def read_config(section='DEFAULT'):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']

CONFIG = read_config()
logging.basicConfig(filename=CONFIG['logs_folder']+'logs.log')

def save_snapshot(metadata) -> str:
    '''
    Saves the metadata in a more structured way in a sqlite db
    returns the id of the snapshot
    '''

    path_to_source = metadata['folder_path']+metadata['source']['filename'] if metadata['source']['saved'] else None
    path_to_screenshot = metadata['folder_path']+metadata['screenshot']['filename'] if metadata['screenshot']['saved'] else None
    path_to_archive = metadata['folder_path']+metadata['mhtml_archive']['filename'] if metadata['mhtml_archive']['saved'] else None
    
    # Check in the logs if something failed
    # We want to reccord that in a distinct field in the DB to spot it more easily
    failed = False
    if 'logs' in metadata:
        for l in metadata['logs']:
            if isinstance(l, dict) and 'Exception' in l:
                failed = True
                break

    values = (
        metadata['name'], metadata['queried_url'], metadata['scraped_url'],
        path_to_source, path_to_screenshot, path_to_archive, metadata['scrape_time'], failed,
        json.dumps(metadata)
    )
    
    con = sqlite3.connect(CONFIG['path_to_db'])
    cursor = con.cursor()
    query = '''INSERT INTO snapshots(
        website_name, queried_url, scraped_url, path_to_source, path_to_screenshot, path_to_archive,
        snapshot_date, failed, metadata
    ) VALUES (?,?,?,?,?,?,?,?,?)
    '''
    cursor.execute(query, values)

    snapshot_id = cursor.lastrowid

    # Commit and close connection to db
    con.commit()
    con.close()

    return snapshot_id

def save_failure(website, exception):
    '''
    Takes in a website object and an exception, and saves a log of the failed scraping with the traceback
    '''

    logging.error('Failed scraping of %s at %s', website.name, website.scrape_time)
    logging.exception(exception)

def make_report():
    '''
    Returns a list containing, for each website, a series of statistics:
    - nbr of times the source/screenshot/archive was saved
    - success ratio
    - nbr of failures for loading the page/saving the source/saving a screenshot/saving an archive
    '''
    con = sqlite3.connect(CONFIG['path_to_db'])

    query = '''
    SELECT queried_url, 1 as count, path_to_source NOTNULL as sources, 
    path_to_screenshot NOTNULL as screenshots, path_to_archive NOTNULL as archives, 
    metadata, failed
    FROM snapshots
    '''

    snapshots = pd.read_sql(query, con)
    con.close()

    def has_failed(metadata, when):
        try:
            if metadata == metadata:
                metadata = json.loads(metadata)
                if 'logs' in metadata:
                    for l in metadata['logs']:
                        if isinstance(l, dict) and 'When' in l:
                            if l['When'] == when:
                                return True
            return False
        except:
            print(metadata)
    
    snapshots['failed_loading'] = snapshots.metadata.apply(lambda x: has_failed(x, 'page_load'))
    snapshots['failed_source'] = snapshots.metadata.apply(lambda x: has_failed(x, 'save_source'))
    snapshots['failed_screenshot'] = snapshots.metadata.apply(lambda x: has_failed(x, 'take_screenshot'))
    snapshots['failed_archive'] = snapshots.metadata.apply(lambda x: has_failed(x, 'save_mhtml_archive'))

    stats = snapshots[[
        'queried_url', 'sources', 'screenshots', 'archives', 'failed', 
        'failed_loading', 'failed_source', 'failed_screenshot', 'failed_archive', 'count'
        ]].groupby('queried_url').agg('sum').reset_index()
    
    stats['success_ratio'] = 1 - (stats['failed'] / stats['count'])

    return stats

    
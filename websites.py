from urllib.parse import urlparse
from selenium.webdriver.common.by import By
import configparser
import datetime
import os
import json
from database import save_snapshot

def read_config(section='DEFAULT'):
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['DEFAULT']

CONFIG = read_config()

def get_default_aliases(url):
    netloc = urlparse(url).netloc
    aliases = [
        url, # ex: https://www.website.be/info/
        netloc, # ex: www.website.be
        netloc.split('.')[-2], # ex: website
        '.'.join(netloc.split('.')[-2:]) # ex: website.be
    ]
    return aliases


def get_website_object(url):
    '''
    Returns the best website object, based on the recieved url
    '''

    # Check if the requested url matches one of the known websites
    # For those, writing just a part of the url is enough
    matched_urls = []
    for k in KNOWN_WEBSITES.keys():
        if url in get_default_aliases(k):
            matched_urls.append(k)
    
    if len(matched_urls) > 1:
        raise Exception('The url "'+url+'" is ambiguous')
    elif len(matched_urls) == 1:
        # If the website is one of the known website
        # returns the specialized object if it exists
        full_url = matched_urls[0]
        if KNOWN_WEBSITES[full_url] is not None:
            return KNOWN_WEBSITES[full_url](full_url)
        else:
            return Website(full_url)
    else:
        # If the url doesn't match a knwon website, use the default object
        # Make sure that the url starts with http(s)
        if not url.startswith('https://') and not url.startswith('http://'):
            url = 'https://' + url
        
        return Website(url)


    

class Website(object):

    def __init__(self, url):
        self.url = url
        self.name = self.get_website_name()

        self.scrape_time = datetime.datetime.now()

        # Create the folder where the snapshot will be saved
        # If the folder already exists and isn't empty, fail
        self.data_folder = self.get_folder_path()
        if os.path.isdir(self.data_folder) and os.listdir(self.data_folder):
            raise Exception('Try to save snapshot to '+self.data_folder+' but location is already taken')
        else:
            os.makedirs(self.data_folder, exist_ok=True)

        self.state = 'ini'
        self.logs = []
    
    def set_driver(self, driver):
        self.driver = driver

    def get_website_name(self) -> str:
        '''
        Returns a name for the website, based on the url, to be used in messages and in storage path.
        The name is the domain name of the website, without the "www." and the ".be". 
        '''

        name = urlparse(self.url).netloc
        if name.startswith('www.'):
            name = name[4:]
        if name.endswith('.be'):
            name = name[:-3]
        
        return name

    def _GDPR_popup(self):
        '''
        This function handles some common GDPR popup
        '''
        elements = self.driver.find_elements_by_id('didomi-notice-agree-button')
        if len(elements) == 1:
            self.logs.append("Didomi-style GDPR popup")
            elements[0].click()
        

    def load_page(self):
        self.driver.get(self.url)
        self._GDPR_popup()
        self.true_url = self.driver.current_url
        self.state = 'page_loaded'
    
    def reach_state(self, desired_state):
        if desired_state == 'page_loaded' and self.state == 'ini':
            self.load_page()

    def save_source(self):
        self.reach_state('page_loaded')
        self.source_code_filename = CONFIG['source_code_filename']
        with open(self.data_folder + self.source_code_filename, 'w') as f:
            f.write(self.driver.page_source)
        self.source_code_saved = True

    def take_screenshot(self):
        self.reach_state('page_loaded')
        self.screenshot_filename = CONFIG['screenshot_filename']
        self.driver.save_screenshot(self.data_folder + self.screenshot_filename)
        self.screenshot_taken = True
    
    def save_mhtml_archive(self):
        res = self.driver.execute_cdp_cmd('Page.captureSnapshot', {'format': 'mhtml'})
        self.mhtml_filename = CONFIG['mhtml_archive_filename']
        with open(self.data_folder+self.mhtml_filename, 'w') as f:
            f.write(res['data'])
        self.mhtml_archive_saved = True
    
    @property
    def metadata(self):
        metadata = {
            'name': self.name,
            'queried_url': self.url,
            'scraped_url': getattr(self, 'true_url', None),
            'scrape_time': self.scrape_time.strftime(CONFIG['datetime_folder_format']),
            'logs': self.logs,
            'folder_path': self.data_folder
        }

        if getattr(self, 'source_code_saved', False):
            metadata['source'] = {'saved': True, 'filename': self.source_code_filename}
        else:
            metadata['source'] = {'saved': False, 'filename': None}
        
        if getattr(self, 'screenshot_taken', False):
            metadata['screenshot'] = {'saved': True, 'filename': self.screenshot_filename}
        else:
            metadata['screenshot'] = {'saved': False, 'filename': None}
        
        if getattr(self, 'mhtml_archived_saved', False):
            metadata['mhtml_archive'] = {'saved': True, 'filename': self.mhtml_filename}
        else:
            metadata['mhtml_archive'] = {'saved': False, 'filename': None}

        return metadata
    
    def save_metadata(self):
        with open(self.data_folder + CONFIG['metadata_filename'], 'w') as f:
            json.dump(self.metadata, f)
    
    def save_to_db(self):
        save_snapshot(self.metadata)


    def get_folder_path(self) -> str:
        '''
        Returns the path to the folder where the snapshot should be saved
        '''
        return CONFIG['data_folder'] + self.name + '/' + self.scrape_time.strftime(CONFIG['datetime_folder_format']) + '/'

class VRT(Website):
    '''
    vrt.be needs a specialized class for its GDPR popup
    '''

    def _GDPR_popup(self):
        elements = self.driver.find_elements_by_id('widget-vrt-cookiebalk3__button')
        if len(elements) == 1:
            # Use javascript to interact instead of selenium "click" because selenium throws the following exception:
            # selenium.common.exceptions.ElementNotInteractableException: Message: element not interactable
            self.driver.execute_script("document.getElementById('widget-vrt-cookiebalk3__button').click()")
            self.logs.append("Clicked VRT GDPR popup")
        elif len(elements) == 0:
            self.logs.append("No VRT GDPR popup")

class RTBF(Website):
    '''
    rtbf.be needs a specialized class for its GDPR popup
    '''

    def _GDPR_popup(self):
        elements = self.driver.find_elements_by_class_name('button__acceptAll')
        if len(elements) == 1:
            self.logs.append("Clicked RTBF GDPR popup")
            elements[0].click()
        elif len(elements) == 0:
            self.logs.append("No RTBF GDPR popup")
        else:
            self.logs.append("Multiple matches for RTBF GDPR popup")



KNOWN_WEBSITES = {
    'https://www.lesoir.be': None,
    'https://www.lalibre.be': None,
    'https://www.rtbf.be/info/': RTBF,
    'https://www.dhnet.be': None,
    'https://www.rtl.be/info/': None,
    'https://www.lecho.be': None,
    'https://www.vrt.be': VRT,
    'https://www.standaard.be': None,
    'https://www.tijd.be': None,
    #'https://www.hln.be': None, # Needs a way to handle DPGmedia popup
    #'https://www.demorgen.be/': None, # Needs a way to handle DPGmedia popup
    'https://www.nieuwsblad.be': None
}
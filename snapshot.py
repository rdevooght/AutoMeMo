from selenium import webdriver
import argparse
import configparser
import websites as websites

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--screenshot', dest='take_screenshot', default=False, action='store_true', help='Take a screenshot of the page')
    parser.add_argument('-a', '--archive', dest='save_archive', default=False, action='store_true', help='Save a full archive of the page')
    parser.add_argument('--defaults', dest='default_websites', default=False, action='store_true', help='Add all default websites to the list of urls')
    parser.add_argument('urls', nargs='*', help='List of urls to scrape')
    return parser.parse_args()

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    args = get_arguments()

    if args.default_websites:
        args.urls += websites.KNOWN_WEBSITES.keys()

    options = webdriver.chrome.options.Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(config['DEFAULT']['windows_width'], config['DEFAULT']['windows_height'])

    for i, url in enumerate(args.urls):
        print("Scrape "+ url+" ("+str(i+1)+"/"+str(len(args.urls))+")")
        website = websites.get_website_object(url)
        website.set_driver(driver)
        website.load_page()
        website.save_source()
        if args.take_screenshot:
            website.take_screenshot()
        
        if args.save_archive:
            website.save_mhtml_archive()
        
        website.save_metadata()
        website.save_to_db()

    driver.quit()
    

if __name__ == '__main__':
    main()
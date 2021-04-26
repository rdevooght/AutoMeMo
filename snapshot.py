from selenium import webdriver
import argparse
import configparser
import datetime
import websites as websites
from database_and_logging import save_failure, make_report

def get_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', nargs='?', default=False, const=True, help='Save a report in a CSV file. Can specify filename (default is reports/YYYY_MM_DD.csv in the logs folder). (no scraping is done, other options are ignored)')
    parser.add_argument('-s', '--screenshot', dest='take_screenshot', default=False, action='store_true', help='Take a screenshot of the page')
    parser.add_argument('-a', '--archive', dest='save_archive', default=False, action='store_true', help='Save a full archive of the page')
    parser.add_argument('--defaults', dest='default_websites', default=False, action='store_true', help='Add all default websites to the list of urls')
    parser.add_argument('urls', nargs='*', help='List of urls to scrape')
    return parser.parse_args()

def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    args = get_arguments()

    if args.report:
        report = make_report()
        if args.report == True:
            today = datetime.date.today()
            filename = config['DEFAULT']['logs_folder']+'reports/'+datetime.date.today().strftime("%Y-%m-%d")+'.csv'
        else:
            filename = args.report
        
        report.to_csv(filename, index=False)
        return 0

    if args.default_websites:
        args.urls += websites.KNOWN_WEBSITES.keys()

    options = webdriver.chrome.options.Options()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(config['DEFAULT']['windows_width'], config['DEFAULT']['windows_height'])

    for i, url in enumerate(args.urls):
        print("Scrape "+ url+" ("+str(i+1)+"/"+str(len(args.urls))+")")
        website = websites.get_website_object(url)
        try:
            website.set_driver(driver)
            website.run(save_source=True, save_screenshot=args.take_screenshot, save_archive=args.save_archive)
        except Exception as e:
            save_failure(website, e)

    driver.quit()
    

if __name__ == '__main__':
    main()
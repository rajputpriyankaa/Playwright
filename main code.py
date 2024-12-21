from blinkit import blinkit
from zepto import zepto
from swiggy_instamart import swiggy_instamart


sites = ['blinkit', 'zepto', 'swiggy_instamart']
scrape_site = input(f'select site to be scraped from {sites}: ').lower()
print(scrape_site)
if scrape_site in sites:
    if scrape_site == 'blinkit':
        blinkit()
    elif scrape_site == 'zepto':
        zepto()
    elif scrape_site == 'swiggy_instamart':
        swiggy_instamart()

else:
    print('Scraper is not present for the site entered')
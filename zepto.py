import time

from playwright.sync_api import sync_playwright
import pyautogui
import re
import json
import csv
import os

# timeouts #
macro_timeout = 50000
mini_timeout = 20000

# extraction function
def zepto_extraction(sc_list):
    # sc_list is the content of the list page
    sc = json.loads(sc_list)
    chunk_data = sc['storeProducts']
    # looping through the chunks
    for i in chunk_data:
        title = i['product']['name']
        product_id = i['product']['id']
        brand = i['product']['brand']
        selling_price = i['discountedSellingPrice'] / 100
        mrp = i['mrp'] / 100
        discountAmount = i['discountAmount'] / 100
        discountPercent = str(i['discountPercent']) + '% Off'
        primaryCategoryName = i['primaryCategoryName']
        primarySubcategoryName = i['primarySubcategoryName']
        formattedPacksize = i['productVariant']['formattedPacksize']
        image_url = 'https://cdn.zeptonow.com/' + str(i['productVariant']['images'][0]['path']) if i['productVariant']['images'] else ''
        maxAllowedQuantity = i['productVariant']['maxAllowedQuantity']
        storeId = i['storeId']

        headers = ['Title', 'Product_id', 'Brand', 'Selling_price', 'Mrp', 'DiscountAmount', 'DiscountPercent',
                   'PrimaryCategoryName', 'PrimarySubcategoryName', 'FormattedPacksize', 'Image_url',
                   'MaxAllowedQuantity', 'StoreId']

        sc_data = [title, product_id, brand, selling_price, mrp, discountAmount, discountPercent, primaryCategoryName,
                   primarySubcategoryName,
                   formattedPacksize, image_url, maxAllowedQuantity, storeId]
        # check if the file exists or not
        file_exists = os.path.exists('zepto_output.csv')
        # writing data to csv
        with open('zepto_output.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists or os.stat('zepto_output.csv').st_size == 0:
                writer.writerow(headers)

            writer.writerow(sc_data)

def location(page):
    type_manually_path = '(//p[text()="Type manually"])[1]'
    page.evaluate(f"document.evaluate('{type_manually_path}',document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();")
    page.type('//input[@placeholder="Search a new address"]', 'gurgaon', delay=200)
    page.click('(//div[@data-testid="address-search-item"])[1]')
    page.wait_for_timeout(mini_timeout)
    page.click('//div[text()="Confirm & Continue"]')

def zepto():
    retry = 1
    max_try = 3
    location_popup = '//p[text()="To deliver as quickly as possible, we would like your current location"]'
    content = False
    # loop to retry if the crawling process fails
    while retry < max_try and not content:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                # Get screen resolution
                screen_width, screen_height = pyautogui.size()

                # Set the viewport size to the screen resolution
                page.set_viewport_size({"width": screen_width, "height": screen_height})
                page.goto('https://www.zeptonow.com/')

                # to get the required request of the content from the backened requests
                def page_on_response(request):
                    if re.search('inventory/catalogue/store-products', str(request.url)) is not None and request.method == 'GET':
                        print(f"printing response url {request.url}")
                        sc_list = request.response().text()
                        time.sleep(5)
                        zepto_extraction(sc_list)
                        # print(sc_list)

                page.on("requestfinished", lambda requestfinished: page_on_response(requestfinished))
                # page.wait_for_timeout(macro_timeout)

                if page.is_visible(location_popup):
                    location(page)

                skincare_path = '(//img[@alt="Skincare"])[1]'
                page.evaluate(
                    f"document.evaluate('{skincare_path}',document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click();")
                if page.is_visible(location_popup):
                    location(page)
                page.wait_for_timeout(macro_timeout)

                max_scrolls = 20
                scroll_count = 0
                last_height = page.evaluate("document.body.scrollHeight")
                # pagination
                while scroll_count < max_scrolls:
                    page.mouse.wheel(0, 2000)
                    page.wait_for_timeout(10000)

                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        print("No new content loaded, stopping.")
                        break

                    last_height = new_height
                    scroll_count += 1
                    print(f"Scroll attempt {scroll_count}")

                content = True
                page.wait_for_timeout(mini_timeout)

        except Exception as e:
            retry = retry + 1
            print(retry, max_try)
            if retry == max_try:
                print('Error in crawling')


if __name__ == '__main__':
	zepto()
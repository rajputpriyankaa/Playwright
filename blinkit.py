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
def blinkit_extraction(sc_list):

    # sc_list is the content of the list page

    sc = json.loads(sc_list)
    all_keys = sc.keys()

    # checking keys for different content format
    if 'objects' in all_keys:
        chunk_data = sc['objects']

    else:
        data = sc['prefetch']['with_data']
        key = list(sc['prefetch']['with_data'])[0]
        chunk_data = data[key]['objects']

    # looping through the chunks
    for i in chunk_data:
        if 'header_config' not in i:
            title = i['tracking']['widget_meta']['title']
            product_id = i['tracking']['widget_meta']['id']
            subcategory_id = i['tracking']['widget_meta']['custom_data']['subcategory_id']
            selling_price = i['tracking']['widget_meta']['custom_data']['price']
            mrp = i['tracking']['widget_meta']['custom_data']['mrp']
            city_id = i['data']['merchant']['city_id']
            image_url = i['data']['product']['image_url']
            unit = i['data']['product']['unit']
            product_type = i['data']['product']['type']
            brand = i['data']['product']['brand']
            offer = i['data']['product']['offer']
            discount = i['data']['product']['discount']

            headers = ['Title', 'Product_id', 'Subcategory_id', 'Selling_price', 'Mrp', 'City_id', 'Image_url', 'Unit',
                       'Product_type', 'Brand', 'Offer', 'Discount']
            sc_data = [title, product_id, subcategory_id, selling_price, mrp, city_id, image_url, unit, product_type,
                       brand, offer, discount]

            # check if the file exists or not
            file_exists = os.path.exists('blinkit_output.csv')

            # writing data to csv
            with open('blinkit_output.csv', 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                if not file_exists or os.stat('blinkit_output.csv').st_size == 0:
                    writer.writerow(headers)

                writer.writerow(sc_data)

def blinkit():
    retry = 1
    max_try = 3
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
                page.goto('https://blinkit.com/', timeout=90000)
                if page.is_visible('//div[text()="Please provide your delivery location to see products at nearby store"]'):
                    page.type('//input[@placeholder="search delivery location"]', 'gurgaon', delay=200)
                    page.click('(//div[@class="LocationSearchList__LocationListContainer-sc-93rfr7-0 lcVvPT"])[1]')

                # to get the required request of the content from the backened requests
                def page_on_response(request):
                    # print(f"printing response url {request.url}")
                    if (re.search('https://blinkit.com/v2/listing', str(request.url)) is not None
                            or re.search('https://blinkit.com/v1/listing/widgets', str(request.url)) is not None) \
                            and request.method == 'GET':
                        # print(f"printing response url {request.url}")
                        sc_list = request.response().text()
                        blinkit_extraction(sc_list)
                        # print(sc_list)

                page.on("requestfinished", lambda requestfinished: page_on_response(requestfinished))

                page.click('//img[@alt="19 - Personal Care"]')
                page.wait_for_timeout(macro_timeout)

                max_scrolls = 20
                scroll_count = 0
                last_height = page.evaluate("document.body.scrollHeight")
                # pagination
                while scroll_count < max_scrolls:
                    page.mouse.wheel(0, 1000)
                    page.wait_for_timeout(5000)
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
	blinkit()
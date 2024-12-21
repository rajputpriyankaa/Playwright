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
def swiggy_instamart_extraction(sc_list):
    # sc_list is the content of the list page

    sc = json.loads(sc_list)
    all_keys = sc['data'].keys()
    # checking keys for different content format

    if 'categories' in all_keys:
        chunk_data = sc['data']['widgets'][1]['data']
    else:
        chunk_data = sc['data']['widgets'][0]['data']

    # looping through the chunks
    for i in chunk_data:
        title = i['display_name']
        brand = i['brand']
        brand_id = i['brand_id']
        avl = i['is_avail']
        product_id = i['product_id']
        mrp = i['variations'][0]['price']['mrp']
        selling_price = i['variations'][0]['price']['offer_price']
        discount_value = i['variations'][0]['price']['discount_value']
        offer = i['variations'][0]['price']['offer_applied']['product_description']
        quantity = i['variations'][0]['sku_quantity_with_combo']
        max_allowed_quantity = i['variations'][0]['max_allowed_quantity']
        sub_category_type = i['variations'][0]['sub_category_type']
        category = i['variations'][0]['category']
        store_id = i['variations'][0]['store_id']

        headers = ['Title', 'Brand', 'Brand_Id', 'Avl', 'Product_Id', 'Mrp', 'Selling_Price', 'Discount_Value', 'Offer',
                   'Quantity', 'Max_Allowed_Quantity', 'Sub_Category_Type', 'Category', 'Store_Id']

        sc_data = [title, brand, brand_id, avl, product_id, mrp, selling_price, discount_value, offer, quantity,
                   max_allowed_quantity, sub_category_type, category, store_id]

        # check if the file exists or not
        file_exists = os.path.exists('swiggy_output.csv')

        # writing data to csv
        with open('swiggy_output.csv', 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists or os.stat('swiggy_output.csv').st_size == 0:
                writer.writerow(headers)

            writer.writerow(sc_data)

def swiggy_instamart():
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
                page.goto('https://www.swiggy.com/instamart', timeout=90000)
                page.wait_for_timeout(mini_timeout)
                # page.pause()
                if page.is_visible('//div[@class="_3VnBa"]'):
                    page.click('//div[@class="_3VnBa"]')

                # to get the required request of the content from the backened requests
                def page_on_response(request):
                    if re.search('instamart/category-listing', str(request.url)) is not None \
                            or re.search('instamart/category-listing', str(request.url)) is not None:
                            # and request.method == 'GET':
                        print(f"printing response url {request.url}")
                        sc_list = request.response().text()
                        swiggy_instamart_extraction(sc_list)
                        # print(sc_list)

                page.on("requestfinished", lambda requestfinished: page_on_response(requestfinished))

                page.click('//div[text()="Beauty and Grooming"]')
                page.wait_for_timeout(mini_timeout)

                max_scrolls = 20
                scroll_count = 0

                # using locator to access the count of increasing elements as the height of page remains same
                last_height = page.locator('//div[@data-testid="ItemWidgetContainer"]').count()

                # pagination
                while scroll_count < max_scrolls:
                    page.mouse.wheel(0, 5000)
                    page.wait_for_timeout(5000)

                    new_height = page.locator('//div[@data-testid="ItemWidgetContainer"]').count()
                    # print('new_height', new_height)
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


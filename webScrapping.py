from playwright.sync_api import sync_playwright


def fetchDetails():

    details = {}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, slow_mo=50)
        page = browser.new_page()
        page.goto('https://rtovehicleinfo.onlineseva.xyz/rtovehicle.php')
        page.locator('#card_details').wait_for(timeout=0)

        details['reg_no'] = page.query_selector(
            '//html/body/div/div/div[1]/div[2]/p').inner_text()
        details['name'] = page.query_selector(
            '//html/body/div/div/div[2]/div[2]/p').inner_text()
        details['fuel_type'] = page.query_selector(
            '//html/body/div/div/div[7]/div[2]/p').inner_text()
        details['insaurance_exp'] = page.query_selector(
            '//html/body/div/div/div[12]/div[2]/p').inner_text()

    return details

import bs4
import sys
import time
import apprise
import threading
import os
import subprocess
#from twilio.rest import Client
#from twilio.base.exceptions import TwilioRestException
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException, \
    WebDriverException, ElementClickInterceptedException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

# ---------------------------------------------Please Read--------------------------------------------------------------

# Updated: 4/12/2021

# Hello everyone! Welcome to my Best Buy script.
# Let's go over the checklist for the script to run properly.
#   1. Product URL
#   2. Firefox Profile
#   3. Credit Card CVV Number
#   4. Twilio Account

# This Script only accepts Product URL's that look like this. I hope you see the difference between page examples.

# Example 1 - Nvidia RTX 3080:
# https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440
# Example 2 - PS5:
# https://www.bestbuy.com/site/sony-playstation-5-console/6426149.p?skuId=6426149
# Example 3 - Ryzen 5600x:
# https://www.bestbuy.com/site/amd-ryzen-5-5600x-4th-gen-6-core-12-threads-unlocked-desktop-processor-with-wraith-stealth-cooler/6438943.p?skuId=6438943

# This Script does not accept Product URL's that look like this.
# https://www.bestbuy.com/site/searchpage.jsp?st=rtx+3080&_dyncharset=UTF-8&_dynSessConf=&id=pcat17071&type=page&sc=Global&cp=1&nrp=&sp=&qp=&list=n&af=true&iht=y&usc=All+Categories&ks=960&keys=keys

# Highly Recommend To set up Twilio Account to receive text messages. So if bot doesn't work you'll at least get a phone
# text message with the url link. You can click the link and try manually purchasing on your phone.

# Twilio is free. Get it Here.
# www.twilio.com/referral/BgLBXx

# -----------------------------------------------Steps To Complete------------------------------------------------------

# Test Link 1 - Ryzen 5800x seems to be available quite often. It is the best URL to try out preorder script.
# To actually avoid buying CPU, you can comment out Line 220. Uncomment the line when you are done testing.
# https://www.bestbuy.com/site/amd-ryzen-7-5800x-4th-gen-8-core-16-threads-unlocked-desktop-processor-without-cooler/6439000.p?skuId=6439000

# Test Link 2 (cheap HDMI cable) - https://www.bestbuy.com/site/dynex-6-hdmi-cable-black/6405508.p?skuId=6405508
# *Warning* - Script will try to checkout the HDMI cable twice since this is how the Bestbuy preorder script works
# Best buy makes us click the add to cart button twice to enter Queue System. 
# Don't worry about script buying two graphics cards though. The script will only buy one.
# As well, Best buy won't let you check out more than 1 item.
# To actually avoid buying HDMI cable, you can comment out Line 220. Uncomment the line when you are done testing.

# 1. Product URL
#url = 'https://www.bestbuy.com/site/evga-geforce-rtx-3080-xc3-ultra-gaming-10gb-gddr6-pci-express-4-0-graphics-card/6432400.p?skuId=6432400'
# Search URL
search_url = 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DCPUs%20%2F%20Processors~abcat0507010&sc=Global&st=ryzen%205000&type=page&usc=All%20Categories'

# 2. Firefox Profile
def create_driver():
    """Creating firefox driver to control webpage. Please add your firefox profile here."""
    options = Options()
    options.headless = False  # Change To False if you want to see Firefox Browser Again.
    profile = webdriver.FirefoxProfile(
        r'C:\Users\Andrew\AppData\Roaming\Mozilla\Firefox\Profiles\tncguumw.default-release')
    web_driver = webdriver.Firefox(profile, options=options, executable_path=GeckoDriverManager().install())
    #print('new driver created id is:' + web_driver.session_id)
    return web_driver


# 3. credit card CVV Number
CVV = '215'  # You can enter your CVV number here in quotes.

# 4. Twilio Account
#toNumber = 'your_phonenumber'
#fromNumber = 'twilio_phonenumber'
#accountSid = 'ssid'
#authToken = 'authtoken'
#client = Client(accountSid, authToken)

# 4.a Telegram using apprise
# Create an Apprise instance
apobj = apprise.Apprise()

# Add all of the notification services by their server url.
# A sample telegram notification:
apobj.add('tgram://1693695277:AAF2Ikr3vaYepodeBvR0dX8VG4m-Uz_mXDw/1719249203/')
# notify all of the services loaded into our Apprise object.
# apobj.notify(
#    body='what a great notification service!',
#   title='my notification title',
# )
# ----------------------------------------------------------------------------------------------------------------------

# Create variables
global sentsku
global senttime
global pausetime

sentsku = []  # these are sku's of cards sent in the last X minutes. to not overload your inbox
senttime = []  # Time stamp of the sku's of sent cards.
pausetime = 1800  # notification pause time to not overload inbox


def time_sleep(x, driver):
    """Sleep timer for page refresh."""
    for i in range(x, -1, -1):
        sys.stdout.write('\r')
        sys.stdout.write('{:2d} seconds'.format(i))
        sys.stdout.flush()
        time.sleep(1)
    driver.execute_script('window.localStorage.clear();')
    driver.refresh()


def extract_page():
    html = driver.page_source
    soup = bs4.BeautifulSoup(html, 'html.parser')
    return soup


def driver_click(driver, find_type, selector):
    """Driver Wait and Click Settings."""
    while True:
        if find_type == 'css':
            try:
                driver.find_element_by_css_selector(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)
        elif find_type == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)
        elif find_type == 'xpath':
            try:
                driver.find_element_by_xpath(f"//*[@class='{selector}']").click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(1)

def searching_for_card(driver):
    """Scanning all cards."""
    driver.get(search_url)
    while True:
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        wait = WebDriverWait(driver, 15)
        wait2 = WebDriverWait(driver, 2)
        try:
            #findAllCards = soup.find_all('button', {'class': 'btn btn-primary btn-sm btn-block btn-leading-ficon add-to-cart-button'})
            findAllCards = soup.find_all('a', {'class': 'btn btn-secondary btn-sm btn-block add-to-cart-button'})
            if len(findAllCards) != 0:
                i = 0
                newIDlist = []
                newtimelist = []                
                while i < len(findAllCards):
                    buttonData = findAllCards[i]
                    skuID = buttonData['data-sku-id']                    
                    if skuID in sentsku:
                        x = sentsku.index(skuID)
                        if time.time() - senttime[sentsku.index(skuID)] > pausetime:
                            sentsku.pop(x)
                            senttime.pop(x)
                        else:
                            print('found ', skuID, ' in sent list and time remaining is: ', pausetime - (time.time() - senttime[x]))
                        del x
                    if skuID not in sentsku:
                        newIDlist.append(skuID)
                        newtimelist.append(time.time())
                        skudata = soup.find("li", {'data-sku-id': skuID})
                        price = skudata.select_one('div.priceView-customer-price > span:first-child').get_text()
                        Title = skudata.select_one('div.sku-title > h4:nth-child(1) > a:nth-child(1)').get_text()
                        CardURL = driver.find_element_by_css_selector("a[href*='" + skuID + "']").get_attribute("href")
                        print('In stock: ' + price + ' ' + Title)
                        apobj.notify(
                            body='In stock: ' + price + '  ' + CardURL,
                            title=Title,
                        )   
                        #os.system("BestBuy_BuyaCard.py " + CardURL)
                        subprocess.Popen('BestBuy_BuyaCard.py', shell=True)
                        del price, Title, skudata, CardURL
                    del buttonData, skuID
                    i = i + 1
                sentsku.extend(newIDlist)
                senttime.extend(newtimelist)
                pass
            else: 
                sys.stdout.write('\r')
                sys.stdout.write('nothing new in stock')
                sys.stdout.flush()
                #print('nothing new in stock')

        except NoSuchElementException:
            pass
        time_sleep(10, driver)

#def card_found_setup(url):
#    driver = create_driver()
#    #x = threading.Thread(target=)
#    FoundCard(driver, url)

def FoundCard(driver, url):
    """Found a card in stock now try to buy it"""
    driver.get(url)
    while True:
        html = driver.page_source
        soup = bs4.BeautifulSoup(html, 'html.parser')
        wait = WebDriverWait(driver, 15)
        wait2 = WebDriverWait(driver, 5)
        Title = soup.find("div", class_="sku-title")
        Title = Title.text

        try:
            add_to_cart_button = soup.find('button', {
                'class': 'btn btn-primary btn-lg btn-block btn-leading-ficon add-to-cart-button'})

            if add_to_cart_button:
                print(f'Add To Cart Button Found!')

                # Queue System Logic.
                try:
                    # Entering Queue: Clicking "add to cart" 2nd time to enter queue.
                    wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".add-to-cart-button")))
                    driver_click(driver, 'css', '.add-to-cart-button')
                    print("Clicked Add to Cart Button. Now sending message to your phone.")
                    print("You are now added to Best Buy's Queue System. Page will be refreshing. Please be patient.")

                    # Sleep timer is here to give Please Wait Button to appear. Please don't edit this.
                    time.sleep(5)
                    driver.refresh()
                    time.sleep(5)
                except (NoSuchElementException, TimeoutException) as error:
                    print(f'Queue System Error: ${error}')

                # Sending Text Message To let you know you are in the queue system.
                try:
                    apobj.notify(
                    body='Your In Queue System on Bestbuy!',
                    title=Title,
                    )
                    #client.messages.create(to=toNumber, from_=fromNumber,
                    #                      body=f'Your In Queue System on Bestbuy! {url}')
                except (NameError, TwilioRestException):
                    pass

                # In queue, just waiting for "add to cart" button to turn clickable again.
                # page refresh every 15 seconds until Add to Cart button reappears.
                while True:
                    try:
                        add_to_cart = driver.find_element_by_css_selector(".add-to-cart-button")
                        please_wait_enabled = add_to_cart.get_attribute('aria-describedby')

                        if please_wait_enabled:
                            driver.refresh()
                            time.sleep(15)
                            del please_wait_enabled, add_to_cart
                        else:  # When Add to Cart appears. This will click button.
                            print("Add To Cart Button Clicked A Second Time.")
                            wait2.until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, ".add-to-cart-button")))
                            time.sleep(2)
                            driver_click(driver, 'css', '.add-to-cart-button')
                            time.sleep(2)
                            break
                    except(NoSuchElementException, TimeoutException) as error:
                        print(f'Queue System Refresh Error: ${error}')

                # Going To Cart Process.
                driver.get('https://www.bestbuy.com/cart')

                # Checking if item is still in cart.
                try:
                    wait.until(
                        EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary']")))
                    time.sleep(1)
                    driver_click(driver, 'xpath', 'btn btn-lg btn-block btn-primary')
                    print("Item Is Still In Cart.")
                except (NoSuchElementException, TimeoutException):
                    print("Item is not in cart anymore. Retrying..")
                    time_sleep(3, driver)
                    FoundCard(driver)

                # Logging Into Account.
                print("Attempting to Login. Firefox should remember your login info to auto login.")

                # Click Shipping Option. (if available)
                try:
                    wait2.until(EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary button__fast-track']")))
                    time.sleep(2)
                    shipping_class = driver.find_element_by_xpath("//*[@class='ispu-card__switch']")
                    shipping_class.click()
                    print("Clicking Shipping Option.")
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException, ElementClickInterceptedException) as error:
                    print(f'shipping error: {error}')

                # Trying CVV
                try:
                    print("\nTrying CVV Number.\n")
                    wait2.until(EC.presence_of_element_located((By.ID, "credit-card-cvv")))
                    time.sleep(1)
                    security_code = driver.find_element_by_id("credit-card-cvv")
                    time.sleep(1)
                    security_code.send_keys(CVV)
                except (NoSuchElementException, TimeoutException):
                    pass

                # Final Checkout.
                try:
                    wait2.until(EC.presence_of_element_located((By.XPATH, "//*[@class='btn btn-lg btn-block btn-primary button__fast-track']")))
                    print("clicked checkout")
                    # comment the line down below to avoid buying when testing bot. vv
                    #driver_click(driver, 'xpath', 'btn btn-lg btn-block btn-primary button__fast-track')  
                except (NoSuchElementException, TimeoutException, ElementNotInteractableException):
                    print("Could Not Complete Checkout.")

                # Completed Checkout.
                print('Order Placed!')
                apobj.notify(
                    body='Order Placed! For' + Title,
                    title=Title,
                    )
                time.sleep(1800)
                driver.quit()

        except (NoSuchElementException, TimeoutException) as error:
            print(f'error is: {error}')

        time_sleep(5, driver)


if __name__ == '__main__':
    driver = create_driver()
    searching_for_card(driver)

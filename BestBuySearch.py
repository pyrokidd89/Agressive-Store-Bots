import bs4
import sys
import time
import apprise
#from twilio.rest import Client
#from twilio.base.exceptions import TwilioRestException
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, ElementNotInteractableException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

# Create an Apprise instance
apobj = apprise.Apprise()

# Add all of the notification services by their server url.
# A sample telegram notification:
apobj.add('tgram://1693695277:AAF2Ikr3vaYepodeBvR0dX8VG4m-Uz_mXDw/1719249203/')

# Then notify these services any time you desire. The below would
# notify all of the services loaded into our Apprise object.
# apobj.notify(
#    body='what a great notification service!',
#   title='my notification title',
# )


# Product Page (By default, This URL will scan all RTX 3080's at one time.)
# url = 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DGPUs%20%2F%20Video%20Graphics%20Cards~abcat0507002&sc=Global&st=rtx%203080&type=page&usc=All%20Categories'
#url = 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=currentprice_facet%3DPrice~Less%20than%20%2425&sc=Global&st=hdmi&type=page&usc=All%20Categories'
#url = 'https://www.bestbuy.com/site/computer-cards-components/video-graphics-cards/abcat0507002.c?id=abcat0507002&qp=gpusv_facet%3DGraphics%20Processing%20Unit%20(GPU)~NVIDIA%20GeForce%20RTX%203080&sp=%2Bcurrentprice%20skuidsaas'
url = 'https://www.bestbuy.com/site/searchpage.jsp?_dyncharset=UTF-8&id=pcat17071&iht=y&keys=keys&ks=960&list=n&qp=category_facet%3DCPUs%20%2F%20Processors~abcat0507010&sc=Global&st=ryzen%205000&type=page&usc=All%20Categories'
# Please do not use URL of a Specific Product like the example URL below.
# https://www.bestbuy.com/site/nvidia-geforce-rtx-3080-10gb-gddr6x-pci-express-4-0-graphics-card-titanium-and-black/6429440.p?skuId=6429440
# If you are only interested in a specific graphics card. Use a URL link like this instead.
# You'll see how I used bestbuy filters on website to only show a specific card on the URL below.
# https://www.bestbuy.com/site/searchpage.jsp?id=pcat17071&qp=brand_facet%3DBrand~NVIDIA&st=rtx%203080

# Create variables
sentsku = []  # these are sku's of cards sent in the last X minutes. to not overload your inbox
senttime = []  # Time stamp of the sku's of sent cards.
pausetime = 300  # notification pause time to not overload inbox
def timeSleep(x, driver):
    #for i in range(x, -1, -1):
        #sys.stdout.write('\r')
        #sys.stdout.write('{:2d} seconds'.format(i))
        #sys.stdout.flush()
        #time.sleep(1)
    driver.refresh()
    sys.stdout.write('\r')
    sys.stdout.write('Page refreshed\n')
    sys.stdout.flush()


def createDriver():
    """Creating driver."""
    options = Options()
    options.headless = False   # Change To False if you want to see Firefox Browser Again.
    profile = webdriver.FirefoxProfile(r'C:\Users\Andrew\AppData\Roaming\Mozilla\Firefox\Profiles\tncguumw.default-release')
    driver = webdriver.Firefox(profile, options=options, executable_path=GeckoDriverManager().install())
    return driver


def driverWait(driver, findType, selector):
    """Driver Wait Settings."""
    while True:
        if findType == 'css':
            try:
                driver.find_element_by_css_selector(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)
        elif findType == 'name':
            try:
                driver.find_element_by_name(selector).click()
                break
            except NoSuchElementException:
                driver.implicitly_wait(0.2)


def findingCards(driver):
    """Scanning all cards."""
    driver.get(url)
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
                    #print(i)
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
                        del price, Title, skudata, CardURL
                    del buttonData, skuID
                    i = i + 1
                sentsku.extend(newIDlist)
                senttime.extend(newtimelist)
                pass
            else 
                print('nothing new in stock')

        except NoSuchElementException:
            pass
        timeSleep(5, driver)

if __name__ == '__main__':
    driver = createDriver()
    findingCards(driver)
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo

client=pymongo.MongoClient(MONGO_URL)
db=client[MONGO_DB]


chrome_options=Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
browser=webdriver.Chrome(options=chrome_options)
wait=WebDriverWait(browser, 10)

browser.set_window_size(1400,900)

def search():
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_TSearchForm > div.search-button > button')))
        input.send_keys('美食')
        submit.click()
        button = wait.until(EC.element_to_be_clickable((By.XPATH,'//*[@id="J_Quick2Static"]')))
        button.click()
        wb = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,'#J_OtherLogin > a.weibo-login')))
        wb.click()
        username = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '#pl_login_logged > div > div:nth-child(2) > div > input')))
        password = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '#pl_login_logged > div > div:nth-child(3) > div > input')))
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#pl_login_logged > div > div:nth-child(7) > div:nth-child(1) > a > span')))
        username[0].send_keys('your username')
        password[0].send_keys('your password')
        submit.click()
        time.sleep(5)
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#pl_login_logged > div > div:nth-child(7) > div:nth-child(1) > a > span')))
        submit.click()
        get_products()
    except ElementNotInteractableException:
        return search()
    except TimeoutException:
        return search()

def get_products():
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR,'#mainsrp-itemlist .items .item')))
    html=browser.page_source
    doc=pq(html)
    items=doc('#mainsrp-itemlist .items .item').items()
    for item in items:
        product={
            'image':item.find('.pic .img').attr('src'),
            'price':item.find('.price').text(),
            'deal':item.find('.deal-cnt').text()[:-3],
            'title':item.find('.title').text(),
            'shop':item.find('.shop').text(),
            'location':item.find('.location').text()
        }
        print(product)
        save_to_mongo(product)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功',result)
    except Exception:
        print('存储到MONGODB失败', result)


def main():
    total=search()
    print(total)
    browser.close()


if __name__=='__main__':
    main()
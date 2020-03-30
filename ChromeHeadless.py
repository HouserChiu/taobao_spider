import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pyquery import PyQuery as pq
from config import *
import pymongo
from lxml import etree

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
browser = webdriver.Chrome(options=chrome_options)
wait = WebDriverWait(browser, 10)

browser.set_window_size(1400, 900)


def search():
    print('正在搜索')
    try:
        browser.get('https://www.taobao.com')
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#q'))
        )
        submit = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_TSearchForm > div.search-button > button')))
        input.send_keys('美食')
        submit.click()
        button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="J_Quick2Static"]')))
        button.click()
        wb = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, '#J_OtherLogin > a.weibo-login')))
        wb.click()
        username = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '#pl_login_logged > div > div:nth-child(2) > div > input')))
        password = wait.until(EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, '#pl_login_logged > div > div:nth-child(3) > div > input')))
        login = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#pl_login_logged > div > div:nth-child(7) > div:nth-child(1) > a > span')))
        username[0].send_keys('your username')
        password[0].send_keys('your password')
        login.click()
        time.sleep(5)
        total = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.total')))
        get_products()
        return total.text
    except ElementNotInteractableException:
        return search()
    except TimeoutException:
        return search()

def next_page(page_number):
    try:
        input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > input'))
        )
        submit = wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > div.form > span.btn.J_Submit')))
        input.clear()
        input.send_keys(page_number)
        submit.click()
        wait.until(EC.text_to_be_present_in_element(
            (By.CSS_SELECTOR, '#mainsrp-pager > div > div > div > ul > li.item.active > span'), str(page_number)))
        get_products()
    except TimeoutException:
        next_page(page_number)

def get_products():
    #等待信息加载出来
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '#mainsrp-itemlist .items .item')))
    html = etree.HTML(browser.page_source)
    pros = html.xpath("//div[@class='grid g-clearfix']/div/div")
    infos = []
    for pro in pros:
        price = pro.xpath(".//div[contains(@class,'price')]/strong/text()")
        titles = pro.xpath(".//div[contains(@class,'title')]/a/text()")
        name = ''.join(titles)
        title = re.sub(r'\s', '', name)
        shop= pro.xpath(".//a[contains(@class,'shopname')]/span[2]/text()")

        info = {
            'price':price,
            'title':title,
            'shop':shop
        }

        infos.append(info)
    print(infos)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert(result):
            print('存储到MONGODB成功', result)
    except Exception:
        print('存储到MONGODB失败', result)


if __name__ == '__main__':
    total_text = search()
    total_num = int(re.search('\d+', total_text).group(0))
    for i in range(2, total_num + 1):
        next_page(i)
    browser.close()
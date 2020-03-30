import re
import time
from selenium import webdriver
from selenium.common.exceptions import ElementNotInteractableException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from config import *
import pymongo
from lxml import etree

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

browser = webdriver.Chrome()
wait = WebDriverWait(browser, 10)


def login():
    try:
        browser.get('https://www.taobao.com/')
        time.sleep(1)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="J_SiteNavLogin"]/div[1]/div[1]/a[1]'))).click()
        time.sleep(2)
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="J_OtherLogin"]/a[1]'))).click()
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pl_login_logged"]/div/div[2]/div/input'))).send_keys(
            '微博账号')
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="pl_login_logged"]/div/div[3]/div/input'))).send_keys(
            '微博密码')
        wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="pl_login_logged"]/div/div[7]/div[1]/a/span'))).click()
        time.sleep(2)
        wait.until(
            EC.presence_of_element_located((By.XPATH, '//*[@id="q"]'))
        ).send_keys('美食')
        wait.until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="J_TSearchForm"]/div[1]/button'))).click()
        time.sleep(1)
        total = wait.until(EC.presence_of_element_located((By.XPATH,'//*[@id="mainsrp-pager"]/div/div/div/div[1]')))
        parse_detail()
        return total.text

    except TimeoutException:
        return login()


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
        parse_detail()
    except TimeoutException:
        next_page(page_number)


def parse_detail():
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

    save_to_mongo(infos)


def save_to_mongo(result):
    try:
        if db[MONGO_TABLE].insert_many(result):
            print('存储到MONGODB成功', result)
    except Exception:
        print('存储到MONGODB失败', result)

if __name__ == '__main__':
    total_text = login()
    total_num = int(re.search('\d+', total_text).group(0))
    for i in range(2, total_num + 1):
        next_page(i)
    browser.close()

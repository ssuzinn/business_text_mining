from datetime import datetime
from abc import *
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from business_text_mining.settings import driverPath


class BaseDriver(metaclass=ABCMeta):
    baseurl = ''
    def __init__(self):
        options = webdriver.ChromeOptions()
        #options.add_argument('headless')  # 창 안띄우고 크롤링
        options.add_argument('window-size=1920x1080')
        #options.add_argument("disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-setuid-sandbox")

        self.driver = webdriver.Chrome(driverPath, chrome_options=options)
        self.driver.get(self.baseurl)
        self.driver.implicitly_wait(3)

    def q(self):
        self.driver.quit()


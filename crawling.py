# Settings
import os
import re
import time
import pyperclip
import pandas as pd

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from business_text_mining.base import BaseDriver

'''
//*[@id="menuLink60"]' Q&A
//*[@id="menuLink65"]' FREE 자유게시판
//*[@id="menuLink78"]' 와인 추천하기&받기
'''


class NaverCafeCrawl(BaseDriver):
    baseurl = 'https://nid.naver.com/nidlogin.login'

    def __init__(self):
        super().__init__()
        self.target_url = 'https://cafe.naver.com/winerack24'
        self.clubid = 20564405
        self.menu = 65
        self.file_name = 'WINE_FREE'

    def Naver_login(self, my_id='sujinha927', my_pw='gkrksp0922'):
        self.driver.execute_script("document.getElementsByName('id')[0].value =\'" + my_id + "\'")
        self.driver.execute_script("document.getElementsByName('pw')[0].value =\'" + my_pw + "\'")
        time.sleep(1)
        self.driver.find_element_by_id("log.login").click()
        time.sleep(1)

        # self.clipboard_input('//*[@id="id"]', my_id)
        # self.clipboard_input('//*[@id="pw"]', my_pw)
        # self.driver.find_element_by_xpath('//*[@id="log.login"]').click()
        # time.sleep(1)

    def clipboard_input(self, user_xpath, user_input):
        temp_user_input = pyperclip.paste()

        pyperclip.copy(user_input)
        self.driver.find_element_by_xpath(user_xpath).click()
        ActionChains(self.driver).key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()

        pyperclip.copy(temp_user_input)
        time.sleep(1)

    def NAVER_CAFE(self):
        self.Naver_login()
        self.driver.get(self.target_url)
        time.sleep(1)
        #self.driver.switch_to.frame('cafe_main')
        #self.driver.find_element_by_css_selector(self.menu).click()
        #time.sleep(1)

    def body_crawling(self):
        try:
            body = self.driver.find_element_by_css_selector('div.se-module.se-module-text').text
        except:
            try:
                body = self.driver.find_element_by_css_selector('div.ContentRenderer').text
            except:
                body = ''
        return body

    def comments_crawling(self, page_soup):
        try:
            iscomment = page_soup.find_all('div', class_='comm_cont')
            if len(iscomment) == 0:
                box = []
            else:
                WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'comm_cont')))
                iscomment = page_soup.find_all('div', class_='comm_cont')
                box = []
                for i in iscomment:
                    box.append(i.find('span', class_='comm_body').text.strip())
            return box
        except:
            soup = bs(self.driver.page_source, 'lxml')
            iscomment = soup.find_all('span', class_='text_comment')
            if len(iscomment) == 0:
                box = []
            else:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_all_elements_located((By.CLASS_NAME, 'text_comment')))
                soup = bs(self.driver.page_source, 'lxml')
                iscomment = soup.find_all('span', class_='text_comment')
                box = []
                for i in iscomment:
                    box.append(i.get_text())
            return box

    def Crawling(self):
        self.driver.implicitly_wait(10)
        self.driver.switch_to.frame('cafe_main')
        page_soup = bs(self.driver.page_source, 'html.parser')
        content = page_soup.find('div', class_='inbox')
        title = content.find('div', class_='tit-box').text.strip()
        user = content.find('td', class_='p-nick').find('a', class_="m-tcol-c b").text.strip()
        body = content.find("div", class_="se-main-container").text.strip()
        date = content.find('td', class_='m-tcol-c date').text.strip()
        count = content.findAll('span', class_='b m-tcol-c reply')[1].text.strip()
        comment_count = content.find("td", class_="reply").find("a",
                                                                class_="reply_btn b m-tcol-c m-tcol-p _totalCnt").text
        if content.find("div", class_="like_empty"):
            score = 0
        else:
            score = content.find("div", class_="like_article").find("em", class_="u_cnt _count").text
        comment = self.comments_crawling(page_soup)
        print(title)
        # except:
        #     title = self.driver.find_element_by_css_selector('div.h3.title_text').text  # 제목
        #     user = self.driver.find_element_by_css_selector('div.nick_box').text
        #     date = self.driver.find_element_by_css_selector('span.date').text  # 날짜
        #     count = self.driver.find_element_by_css_selector('span.count').text  # 조회수
        #     comment_count = self.driver.find_element_by_css_selector('strong.num').text  # 댓글수
        #     score = self.driver.find_element_by_css_selector('em.u_cnt._count').text  # 좋아요
        #     body = self.body_crawling()  # 본문
        #     comment = self.comments_crawling(page_soup)

        return date, count, comment_count, score, title, user, body, comment

    def save_json(self, crawled):
        crawled_texts = pd.DataFrame(crawled,
                                     columns=['날짜', '조회수', '댓글개수', '좋아요', '제목', '닉네임', '본문', '댓글'])
        crawled_texts.to_json(f'business_text_mining/crawl_result/{self.file_name}.json', orient='table')

    def save_links(self, pages):
        # &search.menuid = : 게시판 번호
        # &search.page = : 데이터 수집 할 페이지 번호
        # &userDisplay = 50 : 한 페이지에 보여질 게시글 수
        links = []
        for pageNum in range(1, pages + 1):
            menuid = self.menu
            userDisplay = 50
            self.driver.get(
                self.target_url + '/ArticleList.nhn?search.clubid=' + str(self.clubid) + '&search.menuid=' + str(
                    menuid) + '&search.page=' + str(pageNum) + '&userDisplay=' + str(userDisplay))
            self.driver.switch_to.frame('cafe_main')  # iframe으로 접근
            soup = bs(self.driver.page_source, 'html.parser')
            soup = soup.find_all(class_='article-board m-tcol-c')[1]  # 네이버 카페 구조 확인후 게시글 내용만 가저오기
            datas = soup.find_all(class_='td_article')
            for data in datas:
                article_title = data.find(class_='article')
                link = article_title.get('href')
                # article_title = article_title.get_text().strip()
                links.append(link + '\n')
                # print(article_title)
                # print(self.target_url + link)
        with open(f'business_text_mining/links/{self.file_name}_links.txt', 'w') as file:
            for l in links:
                file.write(f'{l}')
        print(f'--------SAVE  {self.file_name} LINKS -----')

    def get_links(self):
        if os.path.isfile(f'business_text_mining/links/{self.file_name}_links.txt'):
            with open(os.path.join('business_text_mining/links', f'{self.file_name}_links.txt'), 'r') as read_file:
                lines = read_file.readlines()
            return lines
        else:
            return ''

    def run(self, endpage=1000, check=0):
        crawled = []
        E=[]
        if os.path.isfile(f'business_text_mining/links/{self.file_name}_links.txt') != True:
            print('get links!')
            self.NAVER_CAFE()
            self.save_links(pages=endpage)
            self.driver.quit()
        links = [l for l in self.get_links() if l != '\n']
        for link in links:
            try:
                try:
                    self.NAVER_CAFE()
                    self.driver.get(''.join([self.target_url, link.strip()]))
                except:
                    self.driver.get(''.join([self.target_url, link.strip()]))

                crawled.append(self.Crawling())
                check += 1
                if check % 100 == 0:
                    print('현재 %d개의 크롤링을 완료하였습니다.' % check)
                    self.save_json(crawled)
                    print(f'save! {self.file_name}_{check}')
                elif check == 1:
                    print('첫 번째 크롤링이 성공적이었습니다.')
                else:
                    continue
            except:
                E.append(link)
                check += 1
                if check % 100 == 0:
                    print('현재 %d개의 크롤링을 완료하였습니다.' % check)
                    self.save_json(crawled)
        self.save_json(crawled)
        self.driver.quit()
        with open(f'business_text_mining/Error_links.txt', 'w') as file:
            for e in E:
                file.write(f'{e}')

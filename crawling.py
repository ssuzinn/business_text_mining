# Settings
import os
import re
import time
import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup as bs
from selenium.webdriver.support import expected_conditions as EC
from business_text_mining.base import BaseDriver


class NaverCafeCrawl(BaseDriver):
    baseurl = 'https://nid.naver.com/nidlogin.login'

    def __init__(self):
        super().__init__()
        self.target_url = 'https://cafe.naver.com/winerack24'
        self.clubid = 20564405
        self.menu = '//*[@id="menuLink60"]'
        self.file_name = 'WINE_Q&A'

    def Naver_login(self, my_id='sujinha927', my_pw='gkrksp0922'):
        self.driver.execute_script("document.getElementsByName('id')[0].value =\'" + my_id + "\'")
        self.driver.execute_script("document.getElementsByName('pw')[0].value =\'" + my_pw + "\'")
        time.sleep(1)
        # login button click
        self.driver.find_element_by_id("log.login").click()
        time.sleep(1)

    def NAVER_CAFE(self):
        self.Naver_login()
        self.driver.get(self.target_url)
        time.sleep(1)
        self.driver.find_element_by_xpath(self.menu).click()
        time.sleep(1)
        self.driver.switch_to.frame('cafe_main')

    def body_crawling(self):
        try:
            body = self.driver.find_element_by_css_selector('div.se-module.se-module-text').text
        except:
            try:
                body = self.driver.find_element_by_css_selector('div.ContentRenderer').text
            except:
                body = ''
        return body

    def comments_crawling(self):
        soup = bs(self.driver.page_source, 'lxml')
        iscomment = soup.find_all('span', class_='text_comment')

        if len(iscomment) == 0:
            box = []
        else:
            WebDriverWait(self.driver, 15).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'text_comment')))
            soup = bs(self.driver.page_source, 'lxml')
            iscomment = soup.find_all('span', class_='text_comment')
            box = []
            for i in iscomment:
                box.append(i.get_text())
        return box

    def Crawling(self):
        self.driver.implicitly_wait(10)

        title = self.driver.find_element_by_css_selector('h3.title_text').text  # 제목
        user = self.driver.find_element_by_css_selector('div.nick_box').text
        date = self.driver.find_element_by_css_selector('span.date').text  # 날짜
        count = self.driver.find_element_by_css_selector('span.count').text  # 조회수
        comment_count = self.driver.find_element_by_css_selector('strong.num').text  # 댓글수
        likescore = self.driver.find_element_by_css_selector('em.u_cnt._count').text  # 좋아요
        body = self.body_crawling()  # 본문
        comment = self.comments_crawling()  # 댓글
        return title, user, date, count, comment_count, likescore, body, comment

    def save_json(self, name, Title, body, comments, User, Date, Count, likeScore, Comment_count):
        C = []
        contents = dict()
        for t, c, com, us, d, count, like, com_count in zip(Title, body, comments, User, Date, Count, likeScore,
                                                            Comment_count):
            contents["title"] = t
            contents["content"] = c
            contents["comments"] = com
            contents["date"] = d
            contents["count"] = count
            contents["likescore"] = like
            contents["comments_count"] = com_count
            C.append(contents)
            contents = dict()
        with open(f'./crawl_result/{name}.json', 'w', encoding='utf8') as cf:
            json.dump(C, cf, indent="\t", ensure_ascii=False)

    def save_links(self, pages):
        # &search.menuid = : 게시판 번호
        # &search.page = : 데이터 수집 할 페이지 번호
        # &userDisplay = 50 : 한 페이지에 보여질 게시글 수
        links = []
        for pageNum in range(1, pages + 1):
            menuid = re.findall('\d+', self.menu)
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
                print(self.target_url + link)
        with open(f'business_text_mining/links/{self.file_name}_links.txt', 'w') as file:
            for l in links:
                file.write(f'{l}')

    def get_links(self):
        if os.path.isfile(f'business_text_mining/links/{self.file_name}_links.txt'):
            with open(os.path.join('business_text_mining/links', f'{self.file_name}_links.txt'), 'r') as read_file:
                lines = read_file.readlines()
            return lines
        else:
            return ''

    def run(self, endpage=1000, check=0, menu='', name=''):
        Title = []
        body = []
        User = []
        Date = []
        Count = []
        likeScore = []
        comments = []
        Comment_count = []

        self.NAVER_CAFE()
        # if os.path.isfile(f'business_text_mining/links/{self.file_name}_links.txt.txt') != True:
        # self.save_links(pages=endpage)

        self.driver.quit()
        links = [l for l in self.get_links() if l != '\n']

        for link in links:
            self.NAVER_CAFE()
            print(self.target_url+link.strip())
            self.driver.get(self.target_url + '/' + link.strip())
            title, user, date, count, comment_count, likescore, content, comment = self.Crawling()

            Title.append(title)
            User.append(user)
            Date.append(date)
            Count.append(count)
            Comment_count.append(comment_count)
            likeScore.append(likescore)
            body.append(content)
            comments.append(comment)

            self.driver.q()

            check += 1
            if check % 100 == 0:
                print('현재 %d개의 크롤링을 완료하였습니다.' % check)
                self.save_json(name=f'{self.file_name}_{check}',
                               Title=Title, body=body, comments=comments, User=User, Date=Date, Count=Count,
                               likeScore=likeScore,
                               Comment_count=Comment_count)
                print(f'save! {self.file_name}_{check}')
                Title = []
                body = []
                User = []
                Date = []
                Count = []
                likeScore = []
                comments = []
                Comment_count = []
            elif check == 1:
                print('첫 번째 크롤링이 성공적이었습니다.')
            else:
                continue

# NaverCafeCrawl(target_url='https://cafe.naver.com/winerack24', clubid=20564405,menu='//*[@id="menuLink60"]',
#                file_name='WINE_Q&A').run()

import json
import re
import pandas as pd
from collections import Counter
from datetime import datetime
from tqdm import tqdm,tqdm_pandas
from kiwipiepy import Kiwi
from soynlp.utils import DoublespaceLineCorpus
from soynlp.word import WordExtractor
from soynlp.tokenizer import MaxScoreTokenizer

import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
from wordcloud import WordCloud
# import chart_studio.plotly.plotly as py
# import cufflinks as cf
# cf.go_offline(connected=True)

class Pre_Process:
    def __init__(self,data_name=''):
        self.data_name=data_name
        self.data=pd.DataFrame

    def data_load(self):
        with open(self.data_name, 'r', encoding='utf-8')as f:
            self.data = json.load(f)
        self.data=pd.DataFrame(self.data['data'])
        return self.data

    @staticmethod
    def clean_text(text):
        emoji_pattern = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   "]+", flags=re.UNICODE)
        text = emoji_pattern.sub(r'', text)
        re_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),|]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        text = re.sub(re_pattern, 'url', text)
        text = re.sub('\([^)]*\)', ',', text)
        text = re.sub('\[[^)]*\]', ',', text)
        text = re.sub('[^ㄱ-ㅎ ㅏ-ㅣ가-힣A-Za-z0-9!?]+', ' ', text)
        text = re.sub('[\\s+ *]', ' ', text)
        return text

    def clean_data(self):
        self.data=self.data_load()
        self.data['clean_content'] = self.data.본문.apply(lambda x: self.clean_text(x))
        self.data['clean_title'] = self.data.제목.apply(lambda x: self.clean_text(x))
        self.data['contents'] = self.data.clean_title + self.data.clean_content
        return self.data

    @staticmethod
    def Check_date(data):
        data['date'] = data.날짜.apply(lambda x: datetime.strptime(''.join(x.split('.')[:3]), '%Y%m%d'))
        Date_count = data.groupby('date').count().loc[:, '본문']
        date_count=Date_count.sort_values(ascending=False)
        return date_count

    def Check_spell(self,data):
        # ! pip install git+https://github.com/ssut/py-hanspell.git
        from hanspell import spell_checker
        tqdm.pandas()
        if 'contents' not in data.columns:
            data= self.clean_text()
        data['spell_check_contents'] = data.contents.progress_apply(lambda x: spell_checker.check(x).checked
        if spell_checker.check(x).checked != '' else x) # spell check시 데이터가 아예 날아가는 경우가 있음
        return data

    @staticmethod
    def show_contents_length(DF):
        font_name = font_manager.FontProperties(fname='/System/Library/Fonts/Supplemental/Arial Narrow Bold Italic.ttf'
                                                ).get_name()
        rc('font', family=font_name, size=15)
        plt.figure(figsize=(10, 8))
        print('컨텐츠의 최대 길이 :', max(len(l) for l in DF.contents))
        print('컨텐츠의 평균 길이 :', sum(map(len, DF.contents)) / len(DF.contents))
        plt.hist([len(s) for s in DF.contents], bins=50, color='#d62728')
        plt.xlabel('length of contents')
        plt.ylabel('number of contents')
        plt.show()

    @staticmethod
    def soytokenizer(DF):
        S = DF.contents
        corpus = DoublespaceLineCorpus(S, iter_sent=True)
        word_extractor = WordExtractor(min_frequency=2,
                                       min_cohesion_forward=0.5,
                                       min_right_branching_entropy=0.0
                                       )
        word_extractor.train(S)
        words = word_extractor.extract()
        cohesion_score = {word: score.cohesion_forward for word, score in words.items() if
                          1.0 > score.cohesion_forward >= 0.8}
        Wtokenizer = MaxScoreTokenizer(scores=cohesion_score)
        return Wtokenizer

    @staticmethod
    def Kiwi_nouns(DF):
        kiwi = Kiwi(num_workers=16)
        kiwi.prepare()
        a = []
        Total = []
        for result in kiwi.analyze(DF.contents, top_n=1):
            R = result[0]
            for i in range(len(R[0])):
                if R[0][i][1] in ['NNG', 'NNP']:
                    a.append(R[0][i][0])
                if R[0][i][1] in ['VV', 'VA']:
                    a.append(R[0][i][0] + '다')
            Total.append(a)
            a = []
        target_title = [[each_word for each_word in each_doc if each_word] for each_doc in Total]
        return target_title

    def Get_unique_nouns(self,DF):
        DF['more_clear'] = DF.contents.apply(lambda x: re.sub('[^ㄱ-ㅎ ㅏ-ㅣ가-힣A-Za-z]+', ' ', x))
        WT = self.soytokenizer(DF)
        DF['soytoken'] = DF.contents.apply(lambda x: WT.tokenize(x))
        #DF['doc_len'] = DF.more_clear.apply(lambda x: len(x))
        DF=DF.drop(columns=['more_clear'])
        DF['kiwi_nouns'] = self.Kiwi_nouns(DF)

        New = []
        Total = []
        Stopwords = ['클릭', '소통', '등급', '감사', '안녕', '리딩', '답변', '댓글', '엄청','등급', '기본', '안내', '규정', '체계',
                     '오늘', '친구', ' ᆸ', '확인', '글', '일', '와인', '드리다', '계시다','되다', '있다', '여쭈다',
                     '마리아','쥬브','하다', '가다', '나다', '스파클', '페어', '리슬','알다', '계시다', '나오다',
                     '들다', '부탁', '사다', '어떻다', '대하다','되다', '보다', '보이다', '나누다', '이야기', '즐기다', '살다', '비다','먹다',
                     '마시다', '같다', '좋다']
        for ind in tqdm(range(len(DF))):
            S = DF.soytoken[ind]
            K = DF.kiwi_nouns[ind]

            for q in S:
                for w in range(1, len(K)):
                    e = K[w]
                    s = K[w - 1]
                    if q.startswith(s) and q.endswith(e):
                        New.append(q)
                    else:
                        New.append(K[w - 1])
                        New.append(K[w])
            NEW = [i for i in list(set(New)) if i not in Stopwords if len(i) > 1 and (i not in ['향', '잔'])]
            Total.append(NEW)
            New = []
        DF['NOUNS'] = Total
        DF['corpus'] = DF.NOUNS.apply(lambda x: ' '.join(x))

        return DF

    def Get_Nouns_Freq(self,DF,num,WORDCLOUD):
        WORDS = [aa for a in DF.NOUNS for aa in a]
        count = Counter(WORDS)
        COUNT = pd.DataFrame(count.items())
        COUNT_DF=COUNT.sort_values(1, ascending=False)[:num]
        if WORDCLOUD:
            # 가장 많이 나온 단어부터 저장한다.
            counts = Counter(WORDS)
            tags = counts.most_common(num)
            lightwordcloud = WordCloud(background_color='white',
                                       width=480, height=480,
                                       font_path="AppleGothic",
                                       colormap='twilight_r').generate_from_frequencies(dict(tags))

            plt.imshow(lightwordcloud)
            lightwordcloud.to_file('WordCloud.jpg')
        return COUNT_DF

    # Not Use
    def Tokeninzing(DF):
        stopword = ['와인', '마시다', '하다', '있다', '어제', '이기',
                    '댓글', '대하다', '클릭', '드리다', '체계',
                    '댓글', '글', '답변', '소통', '등업',
                    '이렇다', '대부분', '그렇다', '그러다',
                    '감사', '되다', '등급', '기본', '안내', '규정', '체계'
                                                        '와쌉', '계시다', '사람', '읽다', '하다', '먹다',
                    '가능', '가다', '가요', '가져가다', '가지다', '그러다', ' ㅂ', 'ㅁ', '안녕', '안녕하세요']

        kiwi = Kiwi(num_workers=16)
        kiwi.prepare()
        E = []
        e = []
        for each_doc in kiwi.analyze(DF['contents'], top_n=1):
            for each_word in each_doc[0][0]:
                if each_word[0] not in stopword:
                    if ('VV' in each_word[1]) or ('VA' in each_word[1]):
                        word = each_word[0] + '다'
                        if word not in stopword:
                            e.append(word)
                    if ('NNG' in each_word[1]) or ('NNP' in each_word[1]):
                        e.append(each_word[0])
                    if each_word[0] == '리딩':
                        e.append('브' + each_word[0])
                    if each_word[0] == '페어':
                        e.append(each_word[0] + '링')
                else:
                    pass
            E.append(e)
            e = []
        temp_title = E

        #     temp_title = [[each_word[0] if ('NNG' in each_word[1]) or ('NNP' in each_word[1])
        #                   else each_word[0] + '다' if ('VV' in each_word[1]) or ('VA' in each_word[1])
        #                   else None for each_word in each_doc[0][0]]
        #                   for each_doc in kiwi.analyze(DF['contents'], top_n=1)]
        target_title = [[each_word for each_word in each_doc if each_word] for each_doc in temp_title]
        DF['token'] = target_title
        return DF










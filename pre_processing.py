import os
import json
import re
import pandas as pd
import numpy as np

class Pre_Process:
    def __init__(self):
        self.data_name=''
        self.data=pd.DataFrame
    def data_load(self):
        with open(self.data_name, 'r', encoding='utf-8')as f:
            self.data = json.load(f)
        return pd.DataFrame(self.data)
    def clean_data(self):
        self.data_load()
        def clean_text(text):
            re_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),|]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            text = re.sub(re_pattern, 'url', text)
            text = re.sub('[+]', ',', text)
            text = re.sub('[^ ㄱ-ㅣ가-힣A-Za-z0-9!?.,~]+', ' ', text)
            text = re.sub('[\s *]', ' ', text)
            return text
        self.data['clean_content'] = self.data.본문.apply(lambda x: clean_text(x))
        self.data['clean_title'] = self.data.제목.apply(lambda x: clean_text(x))
        self.data['contents'] = self.data.clean_title + self.data.clean_content



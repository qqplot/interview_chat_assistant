# import packages
import pandas as pd
import numpy as np
import torch
import sqlite3
from sentence_transformers import SentenceTransformer
# from model1 import Model1
# from model2 import Model2
from sklearn.feature_extraction.text import CountVectorizer

class Model3:
    def __init__(self):
        # self.model1 = Model1()
        # self.model2 = Model2()
        self.db_path = './model3/model3.db'
        self.key_dict = {}
        self.cnt = {}
        self.key_list = []
        self.model = SentenceTransformer('distilbert-base-nli-mean-tokens')
        self.ans = ''
        self.tag_lv0 = ''
        self.tag_lv1 = ''
        self.rank = []
        self.question
        self.Q = []
     

        #example answer
        self.example_answer_info = { 'from' : 'interviewee', 
                                          'info' : {'flag' : 1, 'answer' : 'I created an algorithm to sort through customer data and learn which devices our customers use and how it impacts their experience on our website and online portal. This SQL query interacted with a database of information collected from customers, and the code enabled our company to understand that our portal needed tweaking on certain devices to improve customer engagement. I have also contributed to an open-source big data project, which has been downloaded by users around the world.'} }
        
        self.question_ans = {'question' : ' What technical projects have you completed in data science?',
                                'tag_lv0' : 'general',
                                'tag_lv1' : 'experience',
                                'answer' : 'It was my ~~'}

    def get(self, params):
        if type(params) != dict:
            return {'message': 'params must be dict'}

        # if (params['tx'] == 'get_raw_text_upper'):
        #     res = self.model1.get({'tx': 'get_raw_data'})
        #     inp = [v['text'] for k, v in res.items()]
        #     out = self.model2.get({'tx': 'get_upper', 'txt': inp})
        #     return out

        #user가 follow up 선택
        if (params['tx'] == 'follow'):
            '''
            model warming
            '''

            self.df = self.get_df()
            self.tech_question = self.get_question(self.df, 'technical')
            self.question = self.get_question(self.df, 'all')

            # keywords list check
            print('>> Question keywords list')
            # self.get_Q_keywords(self.question)
            print(self.get_Q_keywords(self.question))
            print('-------   done   -------\n')

        # interviewee의 answer
        if (params['tx'] == 'answerq'):
            '''
            follow-up request 이후
            모델2로부터 최직근 QA를 받아
            follow-up question 생성 후 return한다.
            - argument format for self.recent_qa_from_model2
                params['info'] = {  'question' : 'What was the most difficult project you have done?',
                                    'tag_lv0' : 'general',
                                    'tag_lv1' : 'experience',
                                    'answer' :  'It was my ~~' } 
            '''

            #### 샘플 활용 및 불필요 함수 주석처리
            # print('\n [ (STEP2) Answer is accepted ]')
            # '''
            # 여기서 followup 할 답변을 받아야 합니다!
            # # '''
            # # self.receive_ans(params['answer'])
            # self.receive_ans(self.example_answer_info) # example로 구현함

            # print('>> Check answer')
            # print(self.ans)
            # print('-------   done   -------\n')  


            
            # self.recent_qa_from_model2(self.question_ans) 
            self.recent_qa_from_model2(params['info']) #실제 middle로부터 정보를 받아온다.
            print('>> Use previous question tags')
            print('>> Check q/tag_lv0/tag_lv1/answer')
            print(f"self.tag_lv0 is {self.tag_lv0}")
            print(f"self.tag_lv1 is {self.tag_lv1}")
            print(f"self.answer is {self.ans}")
            print('-------   done   -------\n') 
            
            print('>> Return 3 suggested question for the technical tag')
            if self.tag_lv0 == 'technical':
                for idx, Q in enumerate(self.tech_question):
                    print(idx+1,'.', Q)  
                print('-------   done   -------\n') 
                return None

            else:
                print('>> Get ranking keywords')
                self.get_rank(self.key_list)
                print('-------   done   -------\n') 

                print('>> Return 3 suggested question')
                ret = []
                if len(self.rank) > 3:
                    for i, pair in enumerate(self.rank):
                        if i < 3:
                            idx = pair[0]
                            # print('question: ', self.Q)
                            # print('key_dict: ', self.key_dict)
                            # print('key list: ', self.key_list)
                            # print('cnt: ', self.cnt)
                            # print('rank: ', self.rank)
                            # print('idx: ', idx)
                            print(i+1,'.', self.question[idx])
                            ret.append(self.question[idx])
                        else:
                            break
                else:
                    print(i+1,'.', self.question[idx])
                    ret.append(self.question[idx])
                print('-------   done   -------\n')
                return ret


    def __del__(self):
        pass

    ''' 
    사용할 function 구현 시작
    '''
    def get_df(self):
        '''
        input: follow up question table in db
        output: dataframe
        '''
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT * FROM followup")
        rows = cur.fetchall()
        cols = [column[0] for column in cur.description]

        self.df = pd.DataFrame.from_records(data=rows, columns=cols)
        df = self.df

        return df
    
    def get_question(self, df, tag):
        '''
        technical question 따로 뽑기도 가능
        input: df = dataframe, tag = string
        output: array
        '''
        if tag == 'technical':
            lst = df["question"].tolist()
            self.Q = lst[-3:]
        else:
            self.Q = df["question"].tolist()
        Q = self.Q
        return Q

    def cos_similarity(self, X, Y):
        
        numerator = X.T @ Y
        X_norm = np.linalg.norm(X)
        Y_norm = np.linalg.norm(Y)
        denominator = X_norm * Y_norm
        
        return numerator / denominator

    def get_Q_keywords(self, Q):
        '''
        문제들 keyword 뽑고 dict, list 형태로 저장하기
        input: question = array
        output: array
        '''
        n_gram_range = (1,1)
        stop_words = "english"

        for i, sentence in enumerate(Q):
            count = CountVectorizer(ngram_range=n_gram_range, stop_words=stop_words).fit([sentence])
            candidates = count.get_feature_names_out()

            sentence_embeddings = self.model.encode(sentence)
            candidate_embeddings = self.model.encode(candidates)

            top_n = 3
            distances = np.zeros(shape=candidate_embeddings.shape[0])
            for idx, keyword in enumerate(candidate_embeddings):
                distance = self.cos_similarity(sentence_embeddings, keyword)
                distances[idx] = distance
            
            keywords = [candidates[index] for index in distances.argsort()[-top_n:]]
            self.key_dict[i+1] = keywords
            
        for val in self.key_dict.values():
            self.key_list.append(val)
            
        key_list = self.key_list
        print('key list length 원본: ', len(self.key_list))
        print('__________________________')
        return key_list
    
    def get_rank(self, key_list):
        for index, box in enumerate(key_list):
            for key in box:
                if key in self.ans:
                    if index not in self.cnt:
                        self.cnt[index] = 1
                    else: 
                        self.cnt[index] += 1
        # Model2에서 받아 올 tags, 전 question 사용
        for ix, box in enumerate(key_list):
            if self.tag_lv0 in box:
                if ix not in self.cnt:
                    self.cnt[ix] = 1
                else:
                    self.cnt[ix] += 1
            if self.tag_lv1 in box:
                if ix not in self.cnt:
                    self.cnt[ix] = 1
                else:
                    self.cnt[ix] += 1          
        # print('count_dict: ', self.cnt)
        print('list lenght: ', len(self.key_list))
        print('_________________________________')
        self.cnt.items()
        self.rank = sorted(self.cnt.items(), key=lambda x: x[1], reverse = True)
        rank = self.rank
        return rank

    # 이 함수는 이제 불필요       
    def receive_ans(self, answer_info : dict ) :
        '''
        - (기능) interviewee가 answer하면 middle로부터 answer info를 받아 self.answer_now에 입력한다.
        - args 
            answer_info(dict) 
                - format (dictionary) : { 'from' : 'interviewee', 
                                          'info' : {'flag' : 1, 'answer' : 'I created an algorithm to sort through customer data and learn which devices our customers use and how it impacts their experience on our website and online portal. This SQL query interacted with a database of information collected from customers, and the code enabled our company to understand that our portal needed tweaking on certain devices to improve customer engagement. I have also contributed to an open-source big data project, which has been downloaded by users around the world.'} }
                    
        '''
        if answer_info['from'] != 'interviewee' :
            raise ValueError('Error raised in receive_answer ftn.')
        else :
            self.ans = answer_info['info']['answer']

    def recent_qa_from_model2(self, question_ans : dict):
        self.tag_lv0 = question_ans['tag_lv0']
        self.tag_lv1 = question_ans['tag_lv1']
        self.ans = question_ans['answer'] # answer도 model2에서 받은 정보를 활용한다.

if __name__ == '__main__':
    model3 = Model3()
    # print(model3.get({'tx': 'get_raw_text_upper'}))

    print('----- tx: follow -----')
    print(model3.get(params={'tx': 'follow'}))

    print('----- tx: answerq -----')
    print(model3.get(params={'tx': 'answerq'}))
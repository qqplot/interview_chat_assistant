import pandas as pd
import requests
from IPython.display import display

pd.set_option('display.max_colwidth', 1000)

class Tester:
    def __init__(self, interview_id, applicant_id, position, tot_time=30, sec_time_arr=None, cue=None):
        self.interview_id = interview_id
        self.interviewee_id = applicant_id
        self.position = position
        self.tot_time = tot_time
        self.sec_time_arr = sec_time_arr
        self.cue = cue
        self.history = []
        self._create_session()

    def _create_session(self):
        print('iterview_id', self.interview_id)
        print('iterviewee_id', self.interviewee_id)
        print('position', self.position)
        print('tot_time', self.tot_time)
        print('sec_time_arr', self.sec_time_arr)
        print('cue', self.cue)

        params = {
            'interview_id': self.interview_id,
            'interviewee_id': self.interviewee_id,
            'position': self.position,
            'tot_time': self.tot_time,
            'sec_time_arr': self.sec_time_arr,
            'cue': self.cue,
        }
        response = requests.put('http://127.0.0.1:5000/model/interview_session/', params=params)
        df_res = pd.DataFrame(response.json(), index=[0])
        display(df_res)

    def chat_round_1st(self):
        df_res = self._chat()
        display(df_res)
        self.df_res_last = df_res

    def chat_round(self, question_prev, answer_prev):
        self.df_res_last = self._chat(question_prev, answer_prev, is_follow_up=False)
        display(self.df_res_last)

    def chat_round_fu(self, question_prev, answer_prev):
        self.df_res_last = self._chat(question_prev, answer_prev, is_follow_up=True)
        display(self.df_res_last)

    def _chat(self, question_prev='', answer_prev='', is_follow_up=False):
        assert type(question_prev) in [str, int], 'question_prev_prev must be either str or int'
        if type(question_prev) == int:
            question_prev = self.df_res_last.loc[question_prev].question

        print('question_prev:', question_prev)
        print('answer_prev:', answer_prev)
        print('is_follow_up:', is_follow_up)

        if question_prev:
            self.history.append(('Q', question_prev))
        if answer_prev:
            self.history.append(('A', answer_prev))

        params = {
            'interview_id': self.interview_id,
            'interviewee_id': self.interviewee_id,
            'is_follow_up': str(is_follow_up).lower(),
            'question': question_prev,
            'answer': answer_prev,
        }
        response = requests.get('http://127.0.0.1:5000/model/question/', params=params)
        try:
            df_res = pd.DataFrame(response.json())
        except ValueError as ve:
            df_res = pd.DataFrame(response.json(), index=[0])
        return df_res

    def report(self):
        # for i in self.history:
        #     print(i)
        response = requests.get('http://127.0.0.1:5000/model/summary/')
        try:
            df_res = pd.DataFrame(response.json())
        except ValueError as ve:
            df_res = pd.DataFrame(response.json(), index=[0])
        df_res.answer = df_res.answer.bfill()
        df_res.dropna(subset='question', inplace=True)
        df_res = df_res.reset_index(drop=True)
        return df_res
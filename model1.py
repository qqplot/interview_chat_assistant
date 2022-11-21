import sqlite3
import pandas as pd

class Model1:
    def __init__(self):
        
        '''
        ■ README
        DB로 데이터를 만들지 않은 현재로서는
        csv파일로 DB를 생성하고,
        해당 DB로부터 자료를 가져오는 식으로 구현하였음
        '''

        self.q_result = list() #모델1의 최종 결과물
        '''
        self.q_result
        - model1의 결과물(question list generated from model 1(cv, jd based)) -> model2로 보낸다.
        - format(dictionary) : { 'qfromcvjd' : 
                            [ {'section' : 'knowledge',
                            'question' : 'You don\'t seem to have dealt with the lower language like C++ much. We need someone who can use the C++ language, do you know how to use the C++ language?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'knowledge',
                            'tag_lv1' : 'skill'},
                            {'section' : 'experience',
                            'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experience',
                            'tag_lv1' : 'relationship'},
                            {'section' : 'experties',
                            'question' : 'You said you have studied reinforcement learning. What areas did you research in detail?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experties',
                            'tag_lv1' : 'knowledge'} ] }

        '''


        # cv, jd 정보가 입력되어 있는 DB filepath
        self.db_filepath = './model1/cvjd_db.sqlite' # csv를 원천자료로 할 때에는 해당 db로 만들어 활용한다(향후에는 db를 불러와 사용할 것이므로 이것을 기본으로 하여 기능 설계)

        # DB내 table name
        self.db_table_name = ['cv_app', 'cv_edu', 'cv_pro', 'cv_ski', 'cv_exh', 'jd_com', 'jd_ski']
        '''
        self.db_table_name = db에 담긴 table명에 대한 list
        ['cv_app', 'cv_edu', 'cv_pro', 'cv_ski', 'cv_exh', 'jd_com', 'jd_ski']
        '''


        # DB에서 자료 뽑아올 때 사용할 id
        # middle로부터 받아옴 (if params['tx'] == 'runm1' 부분 참조바랍니다.)
        self.applicant_id : int
        self.jd_id : int



        #임시용 : csv로 작업할 때 사용할 임시용 variable
        self.csv_path = './model1/cvjd_1119' #현재 원천자료가 있는 폴더
        self.csv_cv_app = pd.read_csv(self.csv_path + '/CV_1119 - Applicant.csv' , encoding='euc-kr')
        self.csv_cv_edu = pd.read_csv(self.csv_path + '/CV_1119 - Education.csv' , encoding='euc-kr')
        self.csv_cv_pro = pd.read_csv(self.csv_path + '/CV_1119 - Projects.csv' , encoding='utf-8')
        self.csv_cv_ski = pd.read_csv(self.csv_path + '/CV_1119 - Skill.csv' , encoding='euc-kr')
        self.csv_cv_exh = pd.read_csv(self.csv_path + '/CV_1119 - Work Experience History.csv' , encoding='euc-kr')
        self.csv_jd_com = pd.read_csv(self.csv_path + '/JD_1119 - Company.csv' , encoding='utf-8', delimiter =",")
        self.csv_jd_ski = pd.read_csv(self.csv_path + '/JD_1119 - Skill.csv' , encoding='euc-kr')
        self.csv_dict_df = dict(zip(self.db_table_name, [self.csv_cv_app, self.csv_cv_edu, self.csv_cv_pro, self.csv_cv_ski, self.csv_cv_exh, self.csv_jd_com, self.csv_jd_ski]))


        #임시용 : csv로 작업할 때, 일단 csv파일을 모두 읽어 하나의 db로 만들어주는 과정을 __init__에 넣어준다(향후 삭제 예정)
        self.make_db()

        # interview 관련 jd, cv 정보만으로 구성된 DataFrame
        # 질문 생성시 자주 사용할 dataFrame 
        # (self.set_df_from_db()를 통해 db로부터 자료를 읽어와 setting한다.)
        self.df_cv_app : pd.DataFrame
        self.df_cv_edu : pd.DataFrame
        self.df_cv_pro : pd.DataFrame
        self.df_cv_ski : pd.DataFrame
        self.df_cv_exh : pd.DataFrame
        self.df_jd_com : pd.DataFrame
        self.df_jd_ski : pd.DataFrame
        self.dict_df = dict()# 위 dataFrame들을 value로 하는 dictionary(key는 table name)
        '''
        self.dict_df :  dictionary with
                        key = self.db_table_name
                        value = pd.DataFrame 예) self.df_cv_app
        '''

    
    # method
    def get_df_cv_app(self) : return self.df_cv_app
    def get_df_cv_edu(self) : return self.df_cv_edu
    def get_df_cv_pro(self) : return self.df_cv_pro
    def get_df_cv_ski(self) : return self.df_cv_ski
    def get_df_cv_exh(self) : return self.df_cv_exh
    def get_df_jd_com(self) : return self.df_jd_com
    def get_df_jd_ski(self) : return self.df_jd_ski
    
    
    # 임시용 : csv read test용 method (향후 csv 안쓰면 삭제)
    def get_csv_cv_app(self) : return self.csv_cv_app
    def get_csv_cv_edu(self) : return self.csv_cv_edu
    def get_csv_cv_pro(self) : return self.csv_cv_pro
    def get_csv_cv_ski(self) : return self.csv_cv_ski
    def get_csv_cv_exh(self) : return self.csv_cv_exh
    def get_csv_jd_com(self) : return self.csv_jd_com
    def get_csv_jd_ski(self) : return self.csv_jd_ski


    # 임시용 : csv 원천자료를 db로 만들어 활용한다(향후에는 db를 불러와 사용할 것이므로 삭제 가능)
    def make_db(self) :
        '''
        csv 파일을 원천자료로 하여 작업하는 과정에서도
        해당 csv파일을 db로 만들어서 처리하도록 한다.
        __init__ 에서 실행된다.
        
        db의 테이블 명은 self.db_table_name을 참고
        '''
        con = sqlite3.connect(self.db_filepath)
        for name in self.db_table_name : 
            self.csv_dict_df[name].to_sql(name, con, index = False, if_exists = 'replace')
        con.close()


    def set_df_from_db(self, applicant_id : int, jd_id : int) : 
        '''
        self.jd_id, self.applicant_id를 이용하여
        database로부터 관련 자료를 불러와 
        self.dict_df를 생성하고
        self.df_'테이블명'도 생성한다.
        '''

        #self.dict_df 생성
        with sqlite3.connect(self.db_filepath) as con:
            for name in self.db_table_name : 
                if name[:2] == 'cv' :
                    self.dict_df[name] = pd.read_sql(f'select * from {name} where applicant_id = {applicant_id}', con)
                else :
                    self.dict_df[name] = pd.read_sql(f'select * from {name} where jd_id = {jd_id}', con)

        #self.df_'테이블명' 생성
        self.df_cv_app = self.dict_df['cv_app']
        self.df_cv_edu = self.dict_df['cv_edu']
        self.df_cv_pro = self.dict_df['cv_pro']
        self.df_cv_ski = self.dict_df['cv_ski']
        self.df_cv_exh = self.dict_df['cv_exh']
        self.df_jd_com = self.dict_df['jd_com']
        self.df_jd_ski = self.dict_df['jd_ski']


    def generate_q(self) :
        '''
        데이터가 셋팅된 상황에서
        class variable들을 활용하여
        question을 generate한다.

        return format
        sample_result = { 'qfromcvjd' : 
                            [ {'section' : 'knowledge',
                            'question' : 'You don\'t seem to have dealt with the lower language like C++ much. We need someone who can use the C++ language, do you know how to use the C++ language?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'knowledge',
                            'tag_lv1' : 'skill'},
                            {'section' : 'experience',
                            'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experience',
                            'tag_lv1' : 'relationship'},
                            {'section' : 'experties',
                            'question' : 'You said you have studied reinforcement learning. What areas did you research in detail?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experties',
                            'tag_lv1' : 'knowledge'} ] }
        '''


        sample_result = { 'qfromcvjd' : 
                            [ {'section' : 'knowledge',
                            'question' : 'You don\'t seem to have dealt with the lower language like C++ much. We need someone who can use the C++ language, do you know how to use the C++ language?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'knowledge',
                            'tag_lv1' : 'skill'},
                            {'section' : 'experience',
                            'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experience',
                            'tag_lv1' : 'relationship'},
                            {'section' : 'experties',
                            'question' : 'You said you have studied reinforcement learning. What areas did you research in detail?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experties',
                            'tag_lv1' : 'knowledge'} ] }
        result = sample_result
        return result


    def get(self, params):
        if type(params) != dict:
            return {'message': 'params must be dict'}

        if (params['tx'] == 'runm1'):
            '''
            jd_id 와 interviewee_id를 setting한다.
            이를 토대로 사용할 database variable을 셋팅해준다.
            셋팅 후 generate_q ftn을 통해 생성된 결과를 return한다.
            (결과는 아래 return format 그대로 model2에 던져주시면 됩니다. 
             model2의 (params['tx'] == 'set_initial_with_example')가 실행될때
             던져주시면 되고 params['cvjdq'] 로 해주시면 감사하겠습니다.)


            < 현재 section(params['tx'] == 'runm1')은 params가 아래와 같은 key-value를 가지고 있다고 가정하고 만들었습니다.>
            params['interview_id'] = 'DS001'
            params['interviee_id'] = 'Elon_Musk' #name of applicant
            
            return foramt

            result = { 'qfromcvjd' : 
                            [ {'section' : 'knowledge',
                            'question' : 'You don\'t seem to have dealt with the lower language like C++ much. We need someone who can use the C++ language, do you know how to use the C++ language?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'knowledge',
                            'tag_lv1' : 'skill'},
                            {'section' : 'experience',
                            'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experience',
                            'tag_lv1' : 'relationship'},
                            {'section' : 'experties',
                            'question' : 'You said you have studied reinforcement learning. What areas did you research in detail?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'experties',
                            'tag_lv1' : 'knowledge'} ] }

            '''
            
            #jd_id setting
            interview_id = params['interview_id']
            if interview_id[:2] == 'DS' : self.jd_id = 0
            else : self.jd_id = 1

            #applicant_id setting
            interviewee_id = params['interviewee_id']
            with sqlite3.connect(self.db_filepath) as con:
                df_row = pd.read_sql(f'select * from cv_app where applicant_name = \'{interviewee_id}\'', con)
            self.applicant_id = df_row['applicant_id'][0]

            #data setting for generating
            self.set_df_from_db(self.applicant_id, self.jd_id)

            #generate q and return
            result = self.generate_q()
            return result


    def __del__(self):
        pass

if __name__ == '__main__':
    model1 = Model1()
    
    print('[ CHECK CSV FILE(ALL APPLICANT, ALL JD) ]')
    print('\n>>cv_app file')
    print(model1.get_csv_cv_app())
    print('\n>>cv_edu file')
    print(model1.get_csv_cv_edu())
    print('\n>>cv_pro file')
    print(model1.get_csv_cv_pro())
    print('\n>>cv_ski file')
    print(model1.get_csv_cv_ski())
    print('\n>>cv_exh file')
    print(model1.get_csv_cv_exh())
    print('\n>>cv_com file')
    print(model1.get_csv_jd_com())
    print('\n>>cv_ski file')
    print(model1.get_csv_jd_ski())

    # csv_jd_com 제대로 들어갔나 체크용    
    # jd_com = model1.get_csv_jd_com()
    # for col in jd_com.columns :
    #     print(f"{col} : ") 
    #     print(jd_com[col][0])
    #     print('----------------')

    
    # model run test
    result = model1.get({'tx': 'runm1', 'interview_id' : 'DS001', 'interviewee_id' : 'Rachel_Lee'})

    print('\n\n[ APPLICANT_ID, JD_ID SPECIFIED. LET\'S CHECK DATAFRAMES TO GENERATE Q ]------applicant_id, jd_id specified-----\n')
    
    print('\n>>cv_app file')
    print(model1.get_df_cv_app())
    print('\n>>cv_app file')
    print(model1.get_df_cv_edu())
    print('\n>>cv_app file')
    print(model1.get_df_cv_pro())
    print('\n>>cv_app file')
    print(model1.get_df_cv_ski())
    print('\n>>cv_app file')
    print(model1.get_df_cv_exh())
    print('\n>>cv_app file')
    print(model1.get_df_jd_com())
    print('\n>>cv_app file')
    print(model1.get_df_jd_ski())
    

    print(f"\n>>result : \n {result}")



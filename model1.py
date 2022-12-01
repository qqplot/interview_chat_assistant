#-*- coding: utf-8 -*-
import os
import sqlite3
import pandas as pd
import datetime as dt
import dateutil
from dateutil import relativedelta as rd
import typing

class Model1:
    def __init__(self):
        
        '''
        README
        DB로 데이터를 만들지 않은 현재로서는
        csv파일로 DB를 생성하고,
        해당 DB로부터 자료를 가져오는 식으로 구현하였음
        '''

        self.q_result = {} #모델1의 최종 결과물

        '''
        self.q_result
        - model1의 결과물(question list generated from model 1(cv, jd based)) -> model2로 보낸다.
        - format(dictionary) : { 'qfromcvjd' : 
                            [ {'section' : 'knowledge',
                            'question' : 'You don't seem to have dealt with the lower language like C++ much. We need someone who can use the C++ language, do you know how to use the C++ language?',
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
        self.db_table_name = ['cv_app', 'cv_edu', 'cv_pro', 'cv_ski', 'cv_exp', 'jd_com', 'jd_ski']
        '''
        self.db_table_name = db에 담긴 table명에 대한 list
        ['cv_app', 'cv_edu', 'cv_pro', 'cv_ski', 'cv_exp', 'jd_com', 'jd_ski']
        '''

        #임시용 : csv로 작업할 때 사용할 임시용 variable
        self.csv_path = './model1/cvjd_1119' #현재 원천자료가 있는 폴더
        self.csv_cv_app = pd.read_csv(self.csv_path + '/CV_1119 - Applicant.csv' , encoding='euc-kr')
        self.csv_cv_edu = pd.read_csv(self.csv_path + '/CV_1119 - Education.csv' , encoding='euc-kr')
        self.csv_cv_pro = pd.read_csv(self.csv_path + '/CV_1119 - Projects.csv' , encoding='utf-8')
        self.csv_cv_ski = pd.read_csv(self.csv_path + '/CV_1119 - Skill.csv' , encoding='euc-kr')
        self.csv_cv_exp = pd.read_csv(self.csv_path + '/CV_1119 - Work Experience History.csv' , encoding='euc-kr')
        self.csv_jd_com = pd.read_csv(self.csv_path + '/JD_1119 - Company.csv' , encoding='utf-8', delimiter =",")
        self.csv_jd_ski = pd.read_csv(self.csv_path + '/JD_1119 - Skill.csv' , encoding='euc-kr')
        self.csv_dict_df = dict(zip(self.db_table_name, [self.csv_cv_app, self.csv_cv_edu, self.csv_cv_pro, self.csv_cv_ski, self.csv_cv_exp, self.csv_jd_com, self.csv_jd_ski]))


        # DB에서 자료 뽑아올 때 사용할 CV & JD id
        # middle로부터 받아옴 (if params['tx'] == 'runm1' 부분 참조바랍니다.)
        self.applicant_name = None
        self.applicant_id = None
        self.position_name = None
        self.jd_id = None

        #임시용 : csv로 작업할 때, 일단 csv파일을 모두 읽어 하나의 db로 만들어주는 과정을 __init__에 넣어준다(향후 삭제 예정)
        self.make_db()

        # 현재 interview 관련 jd, cv 정보만으로 구성된 DataFrame
        # 질문 생성시 자주 사용할 dataFrame 
        # (self.set_df_from_db()를 통해 db로부터 자료를 읽어와 setting한다.)
        self.df_cv_app = None
        self.df_cv_edu = None
        self.df_cv_pro = None
        self.df_cv_ski = None
        self.df_cv_exp = None
        self.df_jd_com = None
        self.df_jd_ski = None
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
    def get_df_cv_exp(self) : return self.df_cv_exp
    def get_df_jd_com(self) : return self.df_jd_com
    def get_df_jd_ski(self) : return self.df_jd_ski
    
    
    # 임시용 : csv read test용 method (향후 csv 안쓰면 삭제)
    def get_csv_cv_app(self) : return self.csv_cv_app
    def get_csv_cv_edu(self) : return self.csv_cv_edu
    def get_csv_cv_pro(self) : return self.csv_cv_pro
    def get_csv_cv_ski(self) : return self.csv_cv_ski
    def get_csv_cv_exp(self) : return self.csv_cv_exp
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


    def set_df_from_db(self, applicant_id, jd_id) : 
        '''
        self.applicant_id를 이용하여
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

        #self.df_'테이블명' 생성2
        self.df_cv_app = self.dict_df['cv_app']
        self.df_cv_edu = self.dict_df['cv_edu']
        self.df_cv_pro = self.dict_df['cv_pro']
        self.df_cv_ski = self.dict_df['cv_ski']
        self.df_cv_exp = self.dict_df['cv_exp']
        self.df_jd_com = self.dict_df['jd_com']
        self.df_jd_ski = self.dict_df['jd_ski']

        #Convert date columns of self.df_cv_exp for date calculation later on
        self.df_cv_exp['start_date'] = pd.to_datetime(self.df_cv_exp['start_date'], errors='coerce')
        self.df_cv_exp['end_date'] = pd.to_datetime(self.df_cv_exp['end_date'], errors='coerce')


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
        # list of generated question
        q_list = []

        # source for all question dictionaries
        source = 'cvjd' 

        ##### 1. Skill #####
        skill_section = 'expertise'
        skill_tag_lv0 = 'technical'
        skill_tag_lv1 = 'skill'

        # Programming
        cv_skill_programming = self.df_cv_ski[self.df_cv_ski['skill_category'] == 'programming']
        jd_skill_programming = self.df_jd_ski[self.df_jd_ski['skill_category'] == 'programming']
        cv_skill_name_list = cv_skill_programming['skill_name'].tolist()
        for i in range(len(jd_skill_programming)):
            skill = jd_skill_programming.skill_name.iloc[i]
            skill_level = jd_skill_programming.skill_level.iloc[i]
            if skill not in cv_skill_name_list:
                q_list.append({
                    'section' : skill_section,
                    'question' : "You haven't mentioned {} in your CV as your skill, which is necessary for this position. How will you make up for your skill insufficiency?".format(skill),
                    'source' : source,
                    'tag_lv0' : skill_tag_lv0,
                    'tag_lv1' : skill_tag_lv1    
                })

            else:
                cv_skill_idx = cv_skill_name_list.index(skill)
                cv_skill_level = cv_skill_programming.skill_level.iloc[cv_skill_idx]
                if ((skill_level == 'high') & (cv_skill_level in ['middle', 'low'])) or ((skill_level == 'middle') & (cv_skill_level == 'low')):
                    q_list.append({
                        'section' : skill_section,
                        'question' : "This position requires {} level of {}. Can you boost your {} skill upto that level in a short amount of time?".format(skill_level, skill, skill),
                        'source' : source,
                        'tag_lv0' : skill_tag_lv0,
                        'tag_lv1' : skill_tag_lv1    
                    })

        ##### 2. Education #####
        education_section = 'experience'
        education_tag_lv0 = 'general'
        education_tag_lv1 = 'education'
        
        # final school level
        cv_school_level = self.df_cv_edu['school_level'].tolist()
        if ((self.df_jd_com['max_school_level'][0] == 'MS') & ('MS' not in cv_school_level) & ('PhD' not in cv_school_level)) or ((self.df_jd_com['max_school_level'][0] == 'PhD') & ('PhD' not in cv_school_level)):
            q_list.append({
                'section' : education_section,
                'question' : "We require an applicant with a {} degree in related majors. Do you think you are qualified enough for this job despite the lack of university education?".format(self.df_jd_com['max_school_level'][0]),
                'source' : source,
                'tag_lv0' : education_tag_lv0,
                'tag_lv1' : education_tag_lv1    
            })

        # preferred majors
        cv_majors = set(self.df_cv_edu['major_name'].tolist())
        jd_company_favored_majors = self.df_jd_com['favored_majors'][0].split(", ")

        is_favored_major = False
        for major in cv_majors:
            if major in jd_company_favored_majors:
                is_favored_major = True
                q_list.append({
                    'section' : education_section,
                    'question' : "Tell us how your {} major could be helpful for this position.".format(major),
                    'source' : source,
                    'tag_lv0' : education_tag_lv0,
                    'tag_lv1' : education_tag_lv1    
                })

        if is_favored_major == False:
            q_list.append({
                'section' : education_section,
                'question' : "Your educational background seems irrelevant to our position. Are you confident that you have enough knowledge and experience that corresponds to or exceeds university education in related majors?",
                'source' : source,
                'tag_lv0' : education_tag_lv0,
                'tag_lv1' : education_tag_lv1    
            })


        ##### 3. Work History #####
        work_section = 'experience'
        work_tag_lv0 = 'general'
        work_tag_lv1 = 'work history'
        
        # position years
        duration = 0
        for i in range(len(self.df_cv_exp)):
            if self.df_cv_exp.position_name.iloc[i] == self.df_cv_app['position_name'][0]:
                diff = rd.relativedelta(self.df_cv_exp.end_date.iloc[i], self.df_cv_exp.start_date.iloc[i])
                duration += diff.months

        if (self.df_jd_com.position_minimum_years[0]*4 - duration) > 6:
            q_list.append({
                'section' : work_section,
                'question' : "We require at least {} years of experience as a {}. What makes you qualified for this job despite the lack of work experience?".format(self.df_jd_com.position_minimum_years[0], self.df_cv_app['position_name'][0]),
                'source' : source,
                'tag_lv0' : work_tag_lv0,
                'tag_lv1' : work_tag_lv1    
            })

        # favored domain
        jd_favored_domain = self.df_jd_com['favored_domains'][0].split(", ")

        for i in range(len(self.df_cv_exp)):
            cv_domains = self.df_cv_exp.domain_name.iloc[i].split(", ")
            for domain in cv_domains:
                if domain in jd_favored_domain:
                    q_list.append({
                        'section' : work_section,
                        'question' : "We want to know more about your experience at {}, which is in the domain of {}. How would that domain knowledge help in working here?".format(self.df_cv_exp.company_name.iloc[i], domain),
                        'source' : source,
                        'tag_lv0' : work_tag_lv0,
                        'tag_lv1' : work_tag_lv1    
                    })


        ##### 4. Projects #####
        project_section = 'experience'
        project_tag_lv0 = 'technical'
        project_tag_lv1 = 'experience'

        case_jd_company_favored_experience = self.df_jd_com['favored_experience_keywords'][0].split(", ")

        no_favored_keyword = True
        for i in range(len(self.df_cv_pro)):
            parsed_project = self.df_cv_pro.project_description.iloc[i].split(" ")
            for keyword in case_jd_company_favored_experience:
                if keyword in parsed_project:
                    no_favored_keyword = False
                    work_id = self.df_cv_pro.work_id.iloc[i]
                    work_row = self.df_cv_exp.loc[self.df_cv_exp.work_id == work_id]
                    company_name = work_row.company_name.iloc[0].strip()
                    
                    q_list.append({
                        'section' : project_section,
                        'question' : "Tell us in detail about your project at {} regarding {}.".format(company_name, keyword),
                        'source' : source,
                        'tag_lv0' : project_tag_lv0,
                        'tag_lv1' : project_tag_lv1    
                    })

        if no_favored_keyword == True:
            q_list.append({
                'section' : project_section,
                'question' : "It seems you have no project experience related to favored keywords mentioned in our JD. Have we missed something or do you really have none?",
                'source' : source,
                'tag_lv0' : project_tag_lv0,
                'tag_lv1' : project_tag_lv1    
            })

        
        self.q_result = {'qfromcvjd': q_list}

        return self.q_result


    def get(self, params):
        if type(params) != dict:
            return {'message': 'params must be dict'}

        if (params['tx'] == 'runm1'):
            '''
            applicant_id 및 jd_id를 setting한다.
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
            
            # self.applicant_id setting    
            self.applicant_name = params['interviewee_id'] 
            self.position_name = params['position']
            with sqlite3.connect(self.db_filepath) as con:
                df_row = pd.read_sql(f'select * from cv_app where applicant_name = \'{self.applicant_name}\'', con)
            self.applicant_id = df_row['applicant_id'][0]

            if self.position_name == "Data Scientist":
                self.jd_id = 0
            elif self.position_name == "Software Engineer":
                self.jd_id = 1

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
    print('\n>>cv_exp file')
    print(model1.get_csv_cv_exp())
    print('\n>>cv_com file')
    print(model1.get_csv_jd_com())
    print('\n>>cv_ski file')
    print(model1.get_csv_jd_ski())
    
    # model run test
    result = model1.get({'tx': 'runm1', 'interview_id' : 'DS002', 'interviewee_id' : 'Daniel_Manson', 'position' : 'Data Scientist'})

    print('\n\n[ APPLICANT_ID, JD_ID SPECIFIED. LET\'S CHECK DATAFRAMES TO GENERATE Q ]------applicant_id, jd_id specified-----\n')
    
    print('\n>>cv_app file')
    print(model1.get_df_cv_app())
    print('\n>>cv_edu file')
    print(model1.get_df_cv_edu())
    print('\n>>cv_pro file')
    print(model1.get_df_cv_pro())
    print('\n>>cv_ski file')
    print(model1.get_df_cv_ski())
    print('\n>>cv_exp file')
    print(model1.get_df_cv_exp())
    print('\n>>jd_com file')
    print(model1.get_df_jd_com())
    print('\n>>jd_ski file')
    print(model1.get_df_jd_ski())

    # model run test
    result = model1.get({'tx': 'runm1', 'interview_id' : 'DS002', 'interviewee_id' : 'Daniel_Manson', 'position' : 'Data Scientist'})

    

    print(f"\n>>result : \n {result}")



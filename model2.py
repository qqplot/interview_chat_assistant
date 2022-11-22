import typing
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer  #sentence_transformers 설치 필요
# from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline #transformers 설치필요 #자동 응답용

PRIORITYSCORE_FOR_CVJD = 1000 #cvjd base question을 상단에 올리는 데에 사용됨(score에 가산)
PRIORITYSCORE_FOR_FOLLOWUP = 2000 #follow up question을 상단에 올리는 데에 사용됨(score에 가산)


class Model2:

    def __init__(self) :

        print('>> Model2 is instantiated.\n')
        

        ############################################
        #### initial argument variable section  ####
        ############################################
        
        # initial argument : 평가항목 / 총 시간 / 평가항목별 문항별 소요시간 / 평가항목별 평가비중
        self.section = list() #평가항목 예) ['intro', 'experience', 'knowledge', 'experties', 'relationship']
        self.section_ratio = list() #평가항목별 평가비중(합계100) / 문항수 배분에 사용 / 예시) [25, 25, 30, 20]
        self.total_time = int() #총 면접시간(분)) 예) 20
        self.timeperqa_bysection = list() #평가항목별 qa 1loop 소요시간(분) / 문항수 count시 고려

        # initial argument : question from bank, question from model1, cv ,j d
        self.q_from_bank = {} #from question bank or else
        '''
        - question list from question bank
        - format(dictionary) :  {'qfrombank' : [
            {'section' : 'experience',
            'question' : 'What was the most difficult project you have done?',
            'source' : 'bank',
            'tag_lv0' : 'general',
            'tag_lv1' : 'experience'},
            {'section' : 'knowledge',
            'question' : 'Can you explain the trade off between bias and variance of estimator.',
            'source' : 'bank',
            'tag_lv0' : 'knowledge',
            'tag_lv1' : 'machineLearning'},... 
            ] }
        '''
        self.q_from_cvjd = {} #cv, jd specific questions from model1 (priority!)
        '''
        - question list from model 1(cv, jd based)
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
        self.info_cv = list() #cv 정보
        '''
        - format(list) : [{'factor' : 'educate', 'contents' : 'graduate school'},
                {'factor' : 'skill', 'contents' : 'python, R, javascript, webprogramming'},
                {'factor' : 'experience', 'contents' : 'Big project'} ]
        '''
        self.info_jd = list() #jd 정보
        '''
        - format(list) : [{'factor' : 'Skills and Qualifications', 'contents' : 'Excellent understanding of machine learning techniques and algorithms, such as k-NN, Naive Bayes, SVM, Decision Forests, etc.'},
                {'factor' : 'Skills and Qualifications', 'contents' : 'Great communication skills'},
                {'factor' : 'Responsibilities', 'contents' : 'Enhancing data collection procedures to include information that is relevant for building analytic systems'} ]
        '''



        ####################################################################
        ### variables for calculating the number of questions for front  ###
        ####################################################################
        
        # calculated for determining questions per second
        self.time_left = int() #남은 면접시간(분) ★middle로부터 받아야 함
        self.time_limit_by_section = list() #평가항목별 소요시간
        self.time_left_by_section = list() #평가항목별 소요시간
        self.possible_q_cnt_by_section = list() #남은시간을 고려한 section별 질문개수



        ##################################
        ### model and context section  ###
        ##################################

        # embedding model (sentence to a vector with length 384)
        self.embed_model = SentenceTransformer('flax-sentence-embeddings/all_datasets_v4_MiniLM-L6')
        '''
        - embed a sentence(question) to a vector(with len = 384) 
        - (model reference) https://huggingface.co/flax-sentence-embeddings/all_datasets_v4_MiniLM-L6 
        '''

        ### variables regarding context section starts--------------------------------
        # initial context based on CV and JD (narray)
        self.initial_context = np.array([])
        # current context based on q&a history (narray)
        self.current_context = np.array([])
        # context history(list of narrays)
        self.context_history = list()
        ### variables regarding context section ends--------------------------------


        ################################
        ### scored question section  ###
        ################################

        # the first scored q list (set before interview starts / source : bank, cvjd)
        self.q_initial_scored = list()
        '''
         - list
         - q_initial_scoring 함수로 생성됨
         - format : [  {'section' : 'experience',
                        'question' : 'What was the most difficult project you have done?',
                        'source' : 'bank',
                        'tag_lv0' : 'general',
                        'tag_lv1' : 'experience',
                        'score' : 24.5 },
                       {'section' : 'knowledge',
                        'question' : 'Can you explain the trade off between bias and variance of estimator.',
                        'source' : 'bank',
                        'tag_lv0' : 'knowledge',
                        'tag_lv1' : 'machineLearning',
                        'score' : 48.6 },... 
                    ] 
        '''
        # question이 picked되고 나면 남은 question들로만 구성하여 가지고 있는다(계속 업데이트)
        self.q_remaining = list()
        #follow_up mode가 되었을 때 준비된 question을 담아두는 곳[temporary] (front에 보낼 때 사용됨)
        self.follow_up_q = list() 


        #####################################
        ### variables for qa interaction  ###
        #####################################
        
        # interviewer가 q를 고르면 update 작업을 위해 기록해둠(dict)
        self.picked_q_now = {}
        '''
        format 예시 : {'flag' : 23, 'question' : 'What was the most difficult project you have done?'}
        '''
        # interviewee가 answer하면 update 작업을 위해 기록해둠(dict)
        self.answer_now = {}
        '''
        format 예시 : {'flag' : 1, 'answer' : 'It was the matrix multiplication parallel project with MPI. It was challenging to me'}
        '''
        self.follow_up_q_mode = False #follow_up_mode가 되면 True가 된다.(Front에 q보내고 다시 False로 전환)
        self.follow_up_q_ready = False #follow_up_q가 준비되면 True가 된다.(Front에 q보내고 다시 False로 전환)


        ##############################
        ### variables for history  ###
        ##############################

        # interviewer가 선택한 question list에 대한 history
        self.picked_q_history = list()
        # interviewee가 답변한 answer에 대한 history
        self.answer_history = list()
        #model3와 주고받은 history 기록
        self.provide_history_with_m3 = list() 
        '''
        format [{'question' : 'What was the most difficult project you have done?',
            'tag_lv0' : 'general',
            'tag_lv1' : 'experience',
            'answer' :  'It was my ~~' }, ... ]
        '''
        self.receive_history_with_m3 = list() 
        '''
        format [{ 1: 'follow-up q1',  2: 'follow-up q2',  3: 'follow-up q3'}, ... ]
        '''


        #############################
        ### sample data for test  ###
        #############################

        # (initial info) 면접평가표의 평가문항(optional한 부분이나 시나리오를 위해 필요할 것으로 생각됨)
        self.exampleSection = ['intro', 'general', 'experience', 'knowledge', 'experties', 'relationship']
        self.example_total_time = 25 #총 면접시간(분)
        self.example_timeperqa_bysection = [2, 2, 2, 2, 2, 2] #평가항목별 qa 1loop 소요시간(분) / 문항수 count시 고려
        self.example_section_ratio = [5, 10, 20, 20, 25, 20] #평가항목별 평가비중(합계100) / 문항수 배분에 사용 / 예시) [25, 25, 30, 20]

        # init argument : question bank 전체(dict)
        self.example_q_from_bank = { 'qfrombank' : 
                            [ {'section' : 'intro',
                            'question' : 'Nice to meet you. Please introduce yourself briefly in 1 minute',
                            'source' : 'bank',
                            'tag_lv0' : 'intro',
                            'tag_lv1' : 'general'},
                            {'section' : 'experience',
                            'question' : 'What was the most difficult project you have done?',
                            'source' : 'bank',
                            'tag_lv0' : 'general',
                            'tag_lv1' : 'experience'},
                            {'section' : 'experience',
                            'question' : 'How was the latest project?',
                            'source' : 'bank',
                            'tag_lv0' : 'general',
                            'tag_lv1' : 'experience'},
                            {'section' : 'experience',
                            'question' : 'Have you ever in a team more than 100 pepoles?',
                            'source' : 'bank',
                            'tag_lv0' : 'general',
                            'tag_lv1' : 'experience'},
                            {'section' : 'knowledge',
                            'question' : 'Can you explain the trade off between bias and variance of estimator.',
                            'source' : 'bank',
                            'tag_lv0' : 'knowledge',
                            'tag_lv1' : 'machineLearning'},
                            {'section' : 'knowledge',
                            'question' : 'Tell me about ERM approach.',
                            'source' : 'bank',
                            'tag_lv0' : 'knowledge',
                            'tag_lv1' : 'machineLearning'},
                            {'section' : 'knowledge',
                            'question' : 'Do you know PAC(Probably Approximately Correct)?',
                            'source' : 'bank',
                            'tag_lv0' : 'knowledge',
                            'tag_lv1' : 'machineLearning'} ] }

        # init argument : cv, jd based question(dict) from model1
        self.example_q_from_cvjd = { 'qfromcvjd' : 
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
        
        # (initial info) 최초 context 계산 등에 필요한 cv, jd 정보 (format은 아래를 가정함)
        self.example_info_cv = [{'factor' : 'educate', 'contents' : 'graduate school'},
                {'factor' : 'skill', 'contents' : 'python, R, javascript, webprogramming'},
                {'factor' : 'experience', 'contents' : 'Big project'} ]
        self.example_info_jd = [{'factor' : 'Skills and Qualifications', 'contents' : 'Excellent understanding of machine learning techniques and algorithms, such as k-NN, Naive Bayes, SVM, Decision Forests, etc.'},
                {'factor' : 'Skills and Qualifications', 'contents' : 'Great communication skills'},
                {'factor' : 'Responsibilities', 'contents' : 'Enhancing data collection procedures to include information that is relevant for building analytic systems'} ]

        # (interaction) interviewer가 pick한 question 정보(여러 qa 오가기 위해 tag 세워둠)
        self.example_picked_q_info = {
             1: { 'from' : 'interviewer',  'info' : {'flag' : 1, 'question' : 'Nice to meet you. Please introduce yourself briefly in 1 minute'}  }, 
             2: { 'from' : 'interviewer',  'info' : {'flag' : 2, 'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?'}  }, 
             3: { 'from' : 'interviewer',  'info' : {'flag' : 3, 'question' : 'follow-up q1'}  }
        }

        # (interaction) interviewee answer 정보
        self.example_answer_info = {
            1: { 'from' : 'interviewee', 'info' : {'flag' : 1, 'answer' : 'Nice to meet you. Thank you. I\'m here to be a data scientist. I\'m working in Amazon for ..'} },
            2: { 'from' : 'interviewee', 'info' : {'flag' : 2, 'answer' : 'It was the matrix multiplication parallel project with MPI. It was challenging to me'} },
            3: { 'from' : 'interviewee', 'info' : {'flag' : 3, 'answer' : 'answer for the follow-up q1'} }
        
        }
        #example_test용_flag
        self.example_flag = 1 

        # (interaction) question from model3 정보
        self.example_q_from_m3 = {1 : { 1: '1_follow-up q1',  2: '1_follow-up q2',  3: '1_follow-up q3'}}
        
        #example_test용_flag2
        self.example_flag2 = 1
        
        # { 'qfromm3' :  
        #                           [{'section' : 'experience',
        #                             'question' : 'Think back to a data project you have worked on where you encountered a problem or challenge. What was the situation, what was the obstacle, and how did you overcome it?',
        #                             'source' : 'model3',
        #                             'tag_lv0' : 'experience',
        #                             'tag_lv1' : 'project'} ] }
        # self.example_picked_q_info = { 'from' : 'interviewer',  
        #               'info' : {'flag' : 23, 'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?'}  }
        # self.example_picked_q_info2 = { 'from' : 'interviewer',  
        #               'info' : {'flag' : 25, 'question' : 'follow-up q1'}  }
        # # (interaction) interviewee answer 정보
        # self.example_answer_info = { 'from' : 'interviewee', 
        #                 'info' : {'flag' : 1, 'answer' : 'It was the matrix multiplication parallel project with MPI. It was challenging to me'} }
        # self.example_answer_info2 = { 'from' : 'interviewee', 
        #                 'info' : {'flag' : 2, 'answer' : 'answer for the follow-up q1'} }

        #answering machine
        # self.answer_generated = ''
        # self.model_name = "deepset/roberta-base-squad2"
        # self.answer_machine = pipeline('question-answering', model=self.model_name, tokenizer=self.model_name)
        # self.cnt_answer = 0

    ###############
    ### methods ###
    ###############


    # 초기 자료입력 셋팅 method ★외부데이터필요(middle 등)
    def set_initial_state(self, section : list, section_ratio : list, total_time : int, timeperqa_bysection : list, q_from_bank : dict, q_from_cvjd : dict, info_cv : list, info_jd : list) :
        # insert
        self.section = section #평가항목
        self.section_ratio = section_ratio #평가항목별 비중(합계100)
        self.total_time = total_time #총 면접시간(분)
        self.timeperqa_bysection = timeperqa_bysection #평가항목별 qa 예상소요시간(분)
        self.q_from_bank = q_from_bank
        self.q_from_cvjd = q_from_cvjd
        self.info_cv = info_cv
        self.info_jd = info_jd
        # calculate
        self.time_left = total_time #남은 면접시간(분)
        self.time_limit_by_section = [i * self.total_time / 100 for i in self.section_ratio]
        self.time_left_by_section = [i * self.total_time / 100 for i in self.section_ratio]
        self.possible_q_cnt_by_section = [ int( t / self.timeperqa_bysection[i] )  for i, t in enumerate(self.time_left_by_section)]

    # intial context 계산 with 초기자료 (※세부구현 필요)
    def set_initial_context(self) :
        '''
        - 기능 : initial context를 np.array vector로 계산한 뒤 self.initial_context에 입력
        - used variables : self.info_cv(list of dictionaries), self.info_jd(list of dictionaries)
        - context 계산방법 세부적으로 implement 해야함
        '''
        df_cv = pd.DataFrame(self.info_cv)
        df_jd = pd.DataFrame(self.info_jd)
        cv_embedding = self.embed_model.encode(df_cv['contents'].tolist()) 
        jd_embedding = self.embed_model.encode(df_jd['contents'].tolist()) 
        joined_embedding = cv_embedding.sum(axis=0) + jd_embedding.sum(axis=0)

        self.initial_context = joined_embedding  #calculate and set initial context
        self.current_context = joined_embedding #update current context
        self.context_history.append(self.initial_context.copy()) #update context history

    # current context 
    def get_current_context(self) : return self.current_context

    # update context (※세부구현 필요 / 현재 단순하게 (+) 하는 식으로 일단 구현 )
    def update_context(self, input_context : np.ndarray) :  
        '''
        - 기능 : middle로부터 온 Q 또는 A의 context를 이용하여 전체 context를 업데이트
        - args
            - input_context(np.ndarray) : embedmodel을 이용하여 vector로 변형된 context
        '''
        self.current_context += input_context
        self.context_history.append(self.current_context.copy())
        
    # score는 일단 dot product로 간단한게 구현함 ※세부구현 필요
    def score_q_by_context(self, embeddedQ : np.ndarray) :
        '''
        - 기능 : embedded된 question들에 대해서 현재 context와 dot product를 하여 score를 부여한다.
        - args
            - embeddedQ(np.ndarray) : embedding model에 의해 embedd된 question vector 목록
        '''
        return np.matmul( embeddedQ, self.get_current_context() ) 

    # initial scoring
    def q_initial_scoring(self) : 
        '''
        - 기능 : Score the importance of each question from Model1 
                and store it in self.q_initial_scored
        - class variables used in this function
            - self.q_from_bank(dict) : question list from question bank
                - format (dictionary) : { 'qfrombank' : 
                    [ {'section' : 'experience',
                       'question' : 'What was the most difficult project you have done?',
                       'tag_lv0' : 'general',
                       'tag_lv1' : 'experience'},
                      {'section' : 'knowledge',
                       'question' : 'Can you explain the trade off between bias and variance of estimator.',
                       'tag_lv0' : 'knowledge',
                       'tag_lv1' : 'machineLearning'},... 
                    ] 
                    }
            - self.initial_context(numpy array)
            - self.q_initial_scored(list) : 최초로 score 매긴 qlist 전체
                - format (list) : 
                    [ {'section' : 'experience',
                       'question' : 'What was the most difficult project you have done?',
                       'tag_lv0' : 'general',
                       'tag_lv1' : 'experience',
                       'score' : 24.5 },
                      {'section' : 'knowledge',
                       'question' : 'Can you explain the trade off between bias and variance of estimator.',
                       'tag_lv0' : 'knowledge',
                       'tag_lv1' : 'machineLearning',
                       'score' : 48.6 },... 
                    ] 
        '''
        # convert q_from_bank and q_from_cvjd(dict) into DataFrame
        df_bank = pd.DataFrame(self.q_from_bank[ next(iter(self.q_from_bank.keys())) ])
        df_cvjd = pd.DataFrame(self.q_from_cvjd[ next(iter(self.q_from_cvjd.keys())) ])

        # add column for score 
        df_bank = df_bank.reindex(columns = df_bank.columns.tolist() + ['score'])
        df_cvjd = df_cvjd.reindex(columns = df_cvjd.columns.tolist() + ['score'])

        # output('question_embedding') : numpy array with shape = (# of questions, length of each vector = 384)
        question_embedding_bank = self.embed_model.encode(df_bank['question'].tolist()) 
        question_embedding_cvjd = self.embed_model.encode(df_cvjd['question'].tolist()) 

        # score 
        df_bank['score'] = self.score_q_by_context(question_embedding_bank) 
        df_cvjd['score'] = self.score_q_by_context(question_embedding_cvjd) + PRIORITYSCORE_FOR_CVJD # considering priority

        # set the q_initial_scored
        self.q_initial_scored = df_bank.to_dict(orient='records') + df_cvjd.to_dict(orient='records')
        self.q_remaining = df_bank.to_dict(orient='records') + df_cvjd.to_dict(orient='records')

    def get_q_initial_scored(self) : return self.q_initial_scored

    def get_q_remaining(self) : return self.q_remaining

    # Front에 보낼 Q ★Front에필요한 양식에 따라 argument 설정필요 / follow-up q 준비된 상황에서는 호출 1번만 해야함(호출 후 flag초기화되기 떄문)
    def makeQforFront(self, ordering_section_first : bool = False, num : int = 1 ) : 
        '''
        - 기능 : score에 기반하여 front로 보낼 qlist를 생성
        - args
            - ordering_section_first(bool) : front에서 평가항목(section)을 기준으로 먼저 ordering 하고자 할 때 True로 설정
            - num : 받고자 하는 question의 개수(ordering_section_first가 true인 경우는 section별 개수)
        - class variable used 
            - self.get_q_remaining
        - return 
            - question list sorting by [section(평가항목)(ascending), score(descending)] (정렬기준은 필요시 변경)
            - format (list)
                    [ {'order' : 0,
                       'section' : 'knowledge',
                       'question' : 'Can you~~',
                       'source' : 'model3',
                       'score' : 48.6 },
                      {'order' : 1,
                       'section' : 'experience',
                       'question' : 'What was~~~~?',
                       'source' : 'cvjd',
                       'score' : 24.5 },
                       {'order' : 2,
                       'section' : 'experience',
                       'question' : 'Have you ever ~~?',
                       'source' : 'bank',
                       'score' : 24.5 },... 
                    ] 
        '''
        df = pd.DataFrame( self.get_q_remaining() )
        # # convert q_remaining into DataFrame(follow_up Q 상황이면 준비된 q도 포함하여 다룬다.)
        # if self.follow_up_q_ready :
        #     df = pd.DataFrame( self.get_q_remaining() + self.follow_up_q )
        #     self.follow_up_q_mode = False # 사용후 mode 꺼주기
        #     self.follow_up_q_ready = False # 사용후 mode 꺼주기
        # else :
        #     df = pd.DataFrame( self.get_q_remaining() )
        
        # 임시 column 추가(section order부여용)
        df = df.reindex(columns = df.columns.tolist() + ['section_tmp_order'])
        
        # sort(옵션 argument에 따라 다르게 구현)
        if ordering_section_first :
            # section별로 구분 후 나열하려면
            # section에 순서를 부여해주고(score가 descending이라 역순으로 부여)
            tmp_order = dict( zip(self.section, range(len(self.section), 0, -1)))
            # column value 부여
            df['section_tmp_order'] = pd.DataFrame([ tmp_order[name] for name in df['section']])
            # sort
            df.sort_values(by=['section_tmp_order', 'score'], axis = 0, ascending = False, inplace = True)
        else : #section 구분 없이 score로만 sort
            df.sort_values(by=['score'], axis = 0, ascending = False, inplace = True)
        
        # index 정비
        df.reset_index(drop = True, inplace = True)

        # 'order' column 생성 및 입력
        df = df.reindex(columns = df.columns.tolist() + ['order'])
        df['order'] = df.index

        # 남은 시간에 따라 section별로 가능한 질문수가 결정(self.possible_q_cnt_by_section)되어 있으니
        # 이를 반영하여 list를 정리한다
        # follow_up_q를 제공할 때는 가장 상단에 생성된 follow_up_q 모두가 보이도록 조치한다
        if ordering_section_first :
            df_new = pd.DataFrame(columns = df.columns)
            for i in range(len(self.section), 0, -1) :
                df_new = pd.concat([df_new, df[ df['section_tmp_order']==i][:self.possible_q_cnt_by_section[len(self.section)-i]] ], axis = 0) 
            df_new.reset_index(drop = True, inplace = True)
            df_new['order'] = df_new.index
            if self.follow_up_q_ready :
                self.follow_up_q_mode = False # 사용후 mode 꺼주기
                self.follow_up_q_ready = False # 사용후 mode 꺼주기
                df_fq = pd.DataFrame( self.follow_up_q )
                df_fq = df_fq.reindex(columns = df_fq.columns.tolist() + ['section_tmp_order', 'order'])
                df_fq.sort_values(by=['score'], axis = 0, ascending = False, inplace = True)
                df_fq.reset_index(drop = True, inplace = True)
                df_new = pd.concat([df_fq, df_new], axis = 0) 
                df_new.reset_index(drop = True, inplace = True)
                df_new['order'] = df_new.index
            return df_new[['order', 'section', 'question', 'source', 'score']].to_dict(orient='records')
        else : return df[['order', 'section', 'question', 'source', 'score']][:num].to_dict(orient='records')

        # if not ordering_section_first :
        #     return df[['order', 'section', 'question', 'source', 'score']][:num].to_dict(orient='records')
        # else :
        #     df_new = pd.DataFrame(columns = df.columns)
        #     for i in range(len(self.section), 0, -1) :
        #         # df_new = pd.concat([df_new, df[ df['section_tmp_order']==i][:num] ], axis = 0)
        #         df_new = pd.concat([df_new, df[ df['section_tmp_order']==i][:self.possible_q_cnt_by_section[len(self.section)-i]] ], axis = 0) 
        #         df_new.reset_index(drop = True, inplace = True)
        #         df_new['order'] = df_new.index
        #     return df_new[['order', 'section', 'question', 'source', 'score']].to_dict(orient='records')

    # interviewer choosed q ★외부데이터필요(middle 등)
    def receive_q_choosed(self, picked_q_info : dict ) :
        '''
        - (기능) interviewer가 Q를 choosed하면 middle로부터 picked_q_info를 받아 self.picked_q_now에 입력한다.
        - args 
            picked_q_info(dict) 
                - format (dictionary) : { 'from' : 'interviewer', 
                                          'info' : {'flag' : 23, 'question' : 'What was the most difficult project you have done?'} 
                                        }
                    
        '''
        if picked_q_info['from'] != 'interviewer' :
            raise ValueError('Error raised in receive_q_choosed ftn.')
        else :
            self.picked_q_now = picked_q_info['info']

    # interviewer question에 따른 업데이트 일괄수행
    def update_with_picked_q(self) :
        '''
        - (기능) interviewer가 choose한 Q를 활용하여 
            context, qna list, remaining question를 update한다.
            (Question rescoring은 A까지 받고 하는 것으로-)
        '''
        # 실제 선택한 q history update
        self.picked_q_history.append(self.picked_q_now['question'])

        # q_remaining update(선택한 q 삭제)
        df = pd.DataFrame( self.get_q_remaining() )
        self.q_remaining = df[df['question']!=self.picked_q_now['question']].to_dict(orient='records')

        # context 계산 후 업데이트 ※세부구현 필요 (Q만 가지고 update하는게 맞을지 의문, A와 조화를 이뤄야할듯)
        context = self.embed_model.encode(self.picked_q_now['question'])
        self.update_context(context)
        # Question rescoring까지 할 필요는 없을 듯.. - answer 받으면 하는 것으로


    # interviewee answer ★외부데이터필요(middle 등) ★남은시간(분)도 받을 수 있는지 체크하기
    def receive_answer(self, answer_info : dict, time_left : float ) :
        '''
        - (기능) interviewee가 answer하면 middle로부터 answer info를 받아 self.answer_now에 입력한다.
        - args 
            answer_info(dict) 
                - format (dictionary) : { 'from' : 'interviewee', 
                                          'info' : {'flag' : 1, 'answer' : 'It was the matrix multiplication parallel project with MPI. It was challenging to me'} }
                    
        '''
        if answer_info['from'] != 'interviewee' :
            raise ValueError('Error raised in receive_answer ftn.')
        else :
            self.answer_now = answer_info['info']
        self.time_left = time_left


    # interviewee answer에 따른 업데이트 일괄수행
    def update_with_answer(self) :
        '''
        - (기능) interviewee answer를 활용하여 
            context, qna list, remaining question를 update한다.
            ★Question rescoring도 수행한다.★)
        '''
        # 실제 answer history update
        self.answer_history.append(self.answer_now['answer'])

        # context 계산 후 업데이트 ※ 세부구현 필요 (Q만 가지고 update하는게 맞을지 의문, A와 조화를 이뤄야할듯)
        context = self.embed_model.encode(self.answer_now['answer'])
        print(f'calculated context[:5] = {context[:5]}')
        self.update_context(context)

        # Question rescoring ※ 세부구현 필요
        score_updated = self.score_q_by_context(self.embed_model.encode( pd.DataFrame(self.get_q_remaining()).question ))
        df = pd.DataFrame(self.get_q_remaining())
        df.score = score_updated
        #cvj based q는 Priorityscore_FOR_CVJD 계속 더해주기
        for i in range(len(df.score)) :
            if df['source'][i] == 'cvjd':
                df.score[i] += PRIORITYSCORE_FOR_CVJD
        self.q_remaining = df.to_dict(orient='records')
        # remaining time possible_q_cnt_by_section 
        self.update_with_time_left()

    def update_with_time_left(self) :
        '''
        self.time_left를 이용하여  self.time_left_by_section 과 self.possible_q_cnt_by_section을 update한다.
        '''
        time_consumed = sum(self.time_left_by_section) - self.time_left
        for i in range(len(self.section)) :
            if time_consumed <= 0 : break
            if time_consumed <= self.time_left_by_section[i] :
                self.time_left_by_section[i] -= time_consumed 
                break
            if time_consumed > self.time_left_by_section[i] :
                time_consumed -= self.time_left_by_section[i]
                self.time_left_by_section[i] = 0
        self.possible_q_cnt_by_section = [ int( t / self.timeperqa_bysection[i] )  for i, t in enumerate(self.time_left_by_section)]
        
        #시간이 조금 남았는데 Q가 0개라면 1개 할당하기(follow-up question 잘리는 거 방지하기 위함)
        for i in range(len(self.section)) :
            if self.time_left_by_section[i]>0 and self.possible_q_cnt_by_section[i]==0 :
                self.possible_q_cnt_by_section[i] = 1

    # follow-up 요청이 오면 flag 세워 둠
    def set_follow_up_q_mode(self) : self.follow_up_q_mode = True

    # follow-up 요청이 오면 model3에 최직근 qa제공
    def provide_latest_qa_to_m3(self) :
        '''
        (기능) 모델3에서 follow-up question을 생성하기 위해 필요한 직전 qa 제공
        return(dictionary) format 
        : {'question' : 'What was the most difficult project you have done?',
            'tag_lv0' : 'general',
            'tag_lv1' : 'experience',
            'answer' :  'It was my ~~' }
        '''
        if len(self.picked_q_history) ==0 or len(self.answer_history) ==0 : 
            raise ValueError('There is no question history or answer history')
        df = pd.DataFrame(self.q_initial_scored)
        # df = pd.DataFrame.from_dict(self.q_initial_scored, orient = 'columns')
        if self.picked_q_history[-1] in df['question'].to_list() :
            q_row = df[ df['question'] == self.picked_q_history[-1] ].iloc[0,:]
            result = {'question' : self.picked_q_history[-1], 'tag_lv0' : q_row['tag_lv0'], 'tag_lv1' : q_row['tag_lv1'], 'answer' : self.answer_history[-1] }
        else :
            result = {'question' : self.picked_q_history[-1], 'tag_lv0' : 'unknown', 'tag_lv1' : 'unknown', 'answer' : self.answer_history[-1] }
        # result = {'question' : self.picked_q_history[-1], 'tag_lv0' : q_row['tag_lv0'].item(), 'tag_lv1' : q_row['tag_lv1'].item(), 'answer' : self.answer_history[-1] }
        
        self.provide_history_with_m3.append(result) # 제공 내역 기록해두기
        return result


    # model3이 생성한 q를 받아옴 ★외부데이터필요(middle 등)
    def receive_q_from_m3(self, q_from_m3 : dict) :
        '''
        model3로부터 follow-up question 받아 처리한다.
        q_from_m3 format is assumed as below
        { 1: 'follow-up q1',  2: 'follow-up q2',  3: 'follow-up q3'}
        '''
        self.receive_history_with_m3.append(q_from_m3) # 수신 내역 기록해두기
        tmp_df = pd.DataFrame(self.q_remaining)
        df_new = pd.DataFrame(columns=tmp_df.columns) # frame setting
        df_new['question'] = pd.DataFrame.from_dict(q_from_m3, orient = 'index') # question 먼저 입력
        df_new.reset_index(drop = True, inplace = True)
        #최직근 Q 정보 가져와서 활용할 예정
        df = pd.DataFrame(self.q_initial_scored)
        
        if self.picked_q_history[-1] in df['question'].to_list() :
            q_row = df[ df['question'] == self.picked_q_history[-1] ].iloc[0,:]
        # q_row = df[ df['question'] == self.picked_q_history[-1] ].iloc[0,:]

        for col in tmp_df.columns :
            if col == 'question': pass #기입력하였음
            elif col == 'score' : #score는 상단에 위치할 수 있도록 부여
                for i in range(len(df_new[col])) :
                    df_new[col][i] = PRIORITYSCORE_FOR_FOLLOWUP + ( len(df_new[col]) - i ) #score는 상단에 위치할 수 있도록 부여
            elif col == 'source' : #source 표기
                df_new[col] = 'model3'
            else : #나머지는 original question의 format을 따르도록
                if self.picked_q_history[-1] in df['question'].to_list() :
                    df_new[col] = q_row[col]
                elif col == 'section' : df_new[col] = 'unknown'

        self.q_initial_scored += df_new.to_dict(orient='records') # follow-up question의 follow-up question을 대비하여...
        self.follow_up_q = df_new.to_dict(orient='records') # model3로부터 제공된 Q 리스트는 임시적인 성격이므로 self.q_remaining에는 보관하지 않고, front 보낼 function에서만 사용한다.
        self.follow_up_q_ready = True #follow-up question이 준비되면 flag를 세운다
        
    # def answer_generate(self, question_history : list, answer_history : list) :
    #     question = question_history[-1]
    #     context = ''
    #     for dict in self.example_info_cv :
    #         context += dict['contents']
    #     for dict in self.example_info_jd :
    #         context += dict['contents']            
    #     for i in range(len(answer_history)) :
    #         context += question_history[i] + answer_history[i] 
    #     QA_input = {'question': question, 'context': context }
    #     res = self.answer_machine(QA_input)
    #     answer_format = { 'from' : 'interviewee',  'info' : {'flag' : 1, 'answer' : res['answer']} }
    #     self.cnt_answer +=1
    #     return answer_format


    '''
    ※추가 구현해야할 사항 
    - cv jd specific question을 어떻게 다룰지 셋팅(최상단 위치 등) ->done
    - follow up question받아오는 logic ->done
    - time에 따른 문항수 setting ->done
    - Question section설정
    - 모델 정교화(context화 방법 등 고민)
    - 사용할 data 정교화
    
    '''

    def get(self, params):
        if type(params) != dict:
            return {'message': 'params must be dict'}
        if (params['tx'] == 'get_upper'):
            return pd.Series(params['txt']).str.upper().to_dict()


        # (STEP1) 초기값 셋팅 -> initial context 계산 -> scoring -> front 보낼 Q return (일단 example date로 구현)
        if (params['tx'] == 'set_initial_with_example'):
            '''
            ※ 필요한 입력 정보(from middle or else)(self.set_initial_state 에 입력필요)
            self.section 
            self.section_ratio 
            self.total_time 
            self.timeperqa_bysection 
            self.q_from_bank 
            self.q_from_cvjd 
            self.info_cv 
            self.info_jd 

            ※ return : front에 보낼 Qlist
                - format(list) : [ {'order' : 0,
                                    'section' : 'knowledge',
                                    'question' : 'Can you~~',
                                    'source' : 'model3',
                                    'score' : 48.6 },
                                    {'order' : 1,
                                    'section' : 'experience',
                                    'question' : 'What was~~~~?',
                                    'source' : 'cvjd',
                                    'score' : 24.5 },
                                    {'order' : 2,
                                    'section' : 'experience',
                                    'question' : 'Have you ever ~~?',
                                    'source' : 'bank',
                                    'score' : 24.5 },... 
                                ] 
            '''

            print('\n[ SET_INITIAL_WITH_EXAMPLE starts ]')
            # # 초기값 셋팅(일단 example data로 구현)
            # self.set_initial_state (section = self.exampleSection, 
            #                         section_ratio = self.example_section_ratio, 
            #                         total_time = self.example_total_time, 
            #                         timeperqa_bysection = self.example_timeperqa_bysection,
            #                         q_from_bank = self.example_q_from_bank, 
            #                         q_from_cvjd = self.example_q_from_cvjd,
            #                         info_cv = self.example_info_cv, 
            #                         info_jd = self.example_info_jd,
            #                         )

            # q_from_bank
            df = pd.read_csv('./model2/bank.csv', encoding='euc-kr')
            columns = df.columns[:-1]
            self.q_from_bank = { 'qfrombank' : df[columns].to_dict(orient='records') }

            self.section = ['intro', 'general', 'experience', 'knowledge', 'experties', 'relationship']
            self.section_ratio = [5, 10, 20, 20, 25, 20] #평가항목별 평가비중(합계100) / 문항수 배분에 사용 / 예시) [25, 25, 30, 20]
            # total_time = 40 #총 면접시간(분)
            self.total_time = params['tot_time'] #총 면접시간(분)
            
            self.timeperqa_bysection = [2, 2, 2, 2, 2, 2] #평가항목별 qa 1loop 소요시간(분) / 문항수 count시 고려
            
            # ★need to update
            self.info_cv = self.example_info_cv # need to update★
            self.info_jd = self.example_info_jd # need to update★


            # q_from_cvjd 받아오기
            self.q_from_cvjd = { 'qfromcvjd' : params['cvjdq'] }
            self.set_initial_state (section = self.section, 
                                    section_ratio = self.section_ratio, 
                                    total_time = self.total_time, 
                                    timeperqa_bysection = self.timeperqa_bysection,
                                    q_from_bank = self.q_from_bank, 
                                    q_from_cvjd = self.q_from_cvjd,
                                    info_cv = self.info_cv, 
                                    info_jd = self.info_jd
                                    )
            

            # initial context 계산(cv, jd 정보 이용)
            self.set_initial_context()

            #context 계산 잘 되었나 check
            print('\n>> check current context / show 5 elements')
            print(self.get_current_context()[:5])
            print('-------   done   -------\n')

            # scoring
            self.q_initial_scoring()

            # scoring 잘 되었나 check
            print('\n>> check get_q_remaining(top10)')
            print(pd.DataFrame(self.get_q_remaining()).iloc[:10,:])
            print('-------   done   -------\n')

            print('\n----------- SET_INITIAL_WITH_EXAMPLE ends with returns ------------\n')
            self.update_with_time_left()
            print('1')
            #return은 프론트에서 사용가능한 Q 목록임(dictionary)
            return self.makeQforFront(ordering_section_first = True, num = 2)


        # (STEP2) interviewer가 Q를 선택
        if (params['tx'] == 'pickq'):
            '''
            ※ 필요한 입력 정보(from middle)
                - 유저가 선택한 question 정보(self.receive_q_choosed 에 입력필요)
                    - format(dictonary) : { 'from' : 'interviewer',  
                                          'info' : {'flag' : 23, 'question' : 'What was the most difficult project you have done?'} 
                                            }
            ※ return : {'is_done' : True}(없애도 될까요?)
            '''

            print('\n[ PICKQ starts ]')
            # params를 통해 question 내용 읽기
            # self.receive_q_choosed(params['question']) ##실제로는 middle에서 받아오나
            # self.receive_q_choosed(self.example_picked_q_info[self.example_flag]) ##일단 example로 구현
            self.receive_q_choosed({ 'from' : params['from'],  'info' : params['info'] }) # param 정보 활용하기
            
            print('\n>> check self.picked_q_now')
            print(self.picked_q_now)
            
            # picked_q_info에 따라 update
            self.update_with_picked_q()
    
            print('\n>> check self.picked_q_history')
            print(self.picked_q_history)
            
            print('\n>> check get_q_remaining(top10)')
            print(pd.DataFrame(self.get_q_remaining()).iloc[:10,:])

            print('\n>> check current context / show 5 elements')
            print(self.get_current_context()[:5])
            
            print('\n>> check context history / show 5 elements')
            tmp = self.context_history
            for i in tmp :
                print(i[:5])
            
            print('\n----------- PICKQ ends with returns ------------\n')
            return {'is_done' : True}

        # (STEP3) interviewee가 Answer
        if (params['tx'] == 'answerq'):
            '''
            ※ 필요한 입력 정보(from middle)
                - answer 정보(self.receive_answer에 입력필요)
                    - format(dictonary) : { 'from' : 'interviewee', 
                                          'info' : {'flag' : 1, 'answer' : 'It was the matrix multiplication parallel project with MPI. It was challenging to me'} }
                - time_left 정보(self.receive_answer에 입력필요)
                    - format(int or float) : 15.5
            ※ return : front에 보낼 Qlist
                - format(list) : [ {'order' : 0,
                                    'section' : 'knowledge',
                                    'question' : 'Can you~~',
                                    'source' : 'model3',
                                    'score' : 48.6 },
                                    {'order' : 1,
                                    'section' : 'experience',
                                    'question' : 'What was~~~~?',
                                    'source' : 'cvjd',
                                    'score' : 24.5 },
                                    {'order' : 2,
                                    'section' : 'experience',
                                    'question' : 'Have you ever ~~?',
                                    'source' : 'bank',
                                    'score' : 24.5 },... 
                                ] 
            '''

            print('\n[ ANSWERQ starts ]')
            
            # params를 통해 answer 내용 및 time_left 읽기
            '''
            param format
            {'interview_id': 'DS001', 'tot_time': 30, 'rem_time': 26, 'tx': 'answerq', 'from': 'interviewee', 'info': {'flag': 0, 'answer': 'test answer 1'}}
            '''
            self.time_left = params['rem_time']
            # self.receive_answer(answer_info=self.example_answer_info, time_left=time_left-2) ##일단 example로 구현 / 
            answer_info = { 'from' : params['from'], 'info' : params['info']}
            self.receive_answer(answer_info = answer_info, time_left = self.time_left) 
            # self.receive_answer(answer_info = self.example_answer_info[self.example_flag], time_left = self.time_left) 
            # self.receive_answer(answer_info = self.answer_generate(self.picked_q_history, self.answer_history), time_left = time_left-2) ##일단 answermachine으로 구현
            # print(f'FLAG = {self.example_flag}')
            # self.example_flag +=1 
            # if self.example_flag >= 4 :
            #     for s in np.random.permutation(self.section).tolist() :
            #         dummyquestion = 'dummyQ_'+str(self.example_flag)+' for '+s
            #         dummyanswer = 'dummyA_'+str(self.example_flag)+' for '+s
            #         question_to_store = {'section' : s, 'question' : dummyquestion, 'source' : 'bank', 'tag_lv0' : 'general', 'tag_lv1' : 'experience', 'score' : 24.5 }
            #         self.q_initial_scored.append(question_to_store)
            #         self.q_remaining.append(question_to_store)
            #     self.example_picked_q_info[self.example_flag] = { 'from' : 'interviewer',  'info' : {'flag' : self.example_flag, 'question' : dummyquestion}}
            #     self.example_answer_info[self.example_flag] = { 'from' : 'interviewee', 'info' : {'flag' : self.example_flag, 'answer' : dummyanswer} }

            
            print('\n>> check self.answer_now')
            print(self.answer_now)
            
            # picked_q_info에 따라 update
            self.update_with_answer()
            
            print('\n>> check self.answer_history')
            print(self.answer_history)
            
            print('\n>> check current context / show 5 elements')
            print(self.get_current_context()[:5])

            print('\n>> check context history / show 5 elements')
            tmp = self.context_history
            for i in tmp :
                print(i[:5])

            # rescoring 잘 되었나 check
            print('\n>> check whether question re-scoring works by get_q_remaining(top10)')
            print(pd.DataFrame(self.get_q_remaining()).iloc[:10,:])

            print('\n----------- ANSWERQ ends with returns ------------\n')
            return self.makeQforFront(ordering_section_first = True, num = 2)



        # (STEP4) interviewer가 follow-up q를 요청
        if (params['tx'] == 'request_for_followup_q'):
            '''
            ※ 필요한 입력 정보(from middle) : 없음
            ※ return : model3에 제공할 최직근 qa 데이터<성문님과 양식합의 완료>
                - format(dictionary) : {'question' : 'What was the most difficult project you have done?',
                                        'tag_lv0' : 'general',
                                        'tag_lv1' : 'experience',
                                        'answer' :  'It was my ~~' } 
            '''
            print('\n[ REQUEST_FOR_FOLLOWUP_Q starts ]')
            self.set_follow_up_q_mode()
            print('\n----------- REQUEST_FOR_FOLLOWUP_Q ends with returns ------------\n')
            return self.provide_latest_qa_to_m3()


        # (STEP5) model3이 choose한 q list  작헙 후 리턴하기
        if (params['tx'] == 'receive_followup_q'):
            '''
            ※ 필요한 입력 정보(from middle) : 
                - model3이 보내온 follow-up question list 정보(self.receive_q_from_m3에 입력필요)
                    - format(dictonary) : { 1: 'follow-up q1',  2: 'follow-up q2',  3: 'follow-up q3'}
            ※ return : front에 보낼 Qlist
                - format(list) : [ {'order' : 0,
                                    'section' : 'knowledge',
                                    'question' : 'Can you~~',
                                    'source' : 'model3',
                                    'score' : 48.6 },
                                    {'order' : 1,
                                    'section' : 'experience',
                                    'question' : 'What was~~~~?',
                                    'source' : 'cvjd',
                                    'score' : 24.5 },
                                    {'order' : 2,
                                    'section' : 'experience',
                                    'question' : 'Have you ever ~~?',
                                    'source' : 'bank',
                                    'score' : 24.5 },... 
                                ] 
            '''
            print('\n[ RECEIVE_FOLLOWUP_Q starts ]')
            self.receive_q_from_m3(q_from_m3 = params['fq']) ##실제로는 middle에서 받아오나
            # self.receive_q_from_m3(q_from_m3=self.example_q_from_m3[self.example_flag2])##일단 example로 구현
            # self.example_flag2+=1
            # self.example_q_from_m3[self.example_flag2]={ 1: str(self.example_flag2) + '_follow-up q1',  2: str(self.example_flag2) + '_follow-up q2',  3: str(self.example_flag2) + '_follow-up q3'}
            print('\n----------- RECEIVE_FOLLOWUP_Q ends with returns ------------\n')
            return self.makeQforFront(ordering_section_first = True, num = 2)


    def __del__(self):
        pass

if __name__ == '__main__':


    model2 = Model2() 


    result1 = model2.get({'tx':'set_initial_with_example'})
    print('\n##### STEP1 return check makeQforFront : consider section')
    print(pd.DataFrame(result1))
    print('\n\n\n')

    
    result2 = model2.get({'tx':'pickq'})
    print('\n##### STEP2 return check')
    print(result2)
    print('\n\n\n')

    
    result3 = model2.get({'tx':'answerq'})
    print('\n##### STEP3 return check makeQforFront : consider section')
    print(pd.DataFrame(result3))
    print('\n\n\n')

    
    result4 = model2.get({'tx':'pickq'})
    print('\n##### STEP4 return check')
    print(result4)
    print('\n\n\n')

    
    result5 = model2.get({'tx':'answerq'})
    print('\n##### STEP5 return check makeQforFront : consider section')
    print(pd.DataFrame(result5))
    print('\n\n\n')
    
    result6 = model2.get({'tx':'request_for_followup_q'})
    print('\n##### STEP6 return check')
    print(result6)
    print('\n\n\n')

    result7 = model2.get({'tx':'receive_followup_q'})
    print('\n##### STEP7 return check')
    print(pd.DataFrame(result7))
    print('\n\n\n')

    
    result4 = model2.get({'tx':'pickq'})
    print('\n##### STEP4 return check')
    print(result4)
    print('\n\n\n')

    
    result5 = model2.get({'tx':'answerq'})
    print('\n##### STEP5 return check makeQforFront : consider section')
    print(pd.DataFrame(result5))
    print('\n\n\n')

    
    result4 = model2.get({'tx':'pickq'})
    print('\n##### STEP4 return check')
    print(result4)
    print('\n\n\n')

    
    result5 = model2.get({'tx':'answerq'})
    print('\n##### STEP5 return check makeQforFront : consider section')
    print(pd.DataFrame(result5))
    print('\n\n\n')

    
    result4 = model2.get({'tx':'pickq'})
    print('\n##### STEP4 return check')
    print(result4)
    print('\n\n\n')

    
    result5 = model2.get({'tx':'answerq'})
    print('\n##### STEP5 return check makeQforFront : consider section')
    print(pd.DataFrame(result5))
    print('\n\n\n')

    
    result4 = model2.get({'tx':'pickq'})
    print('\n##### STEP4 return check')
    print(result4)
    print('\n\n\n')

    
    result5 = model2.get({'tx':'answerq'})
    print('\n##### STEP5 return check makeQforFront : consider section')
    print(pd.DataFrame(result5))
    print('\n\n\n')

    
    result4 = model2.get({'tx':'pickq'})
    print('\n##### STEP4 return check')
    print(result4)
    print('\n\n\n')

    
    result5 = model2.get({'tx':'answerq'})
    print('\n##### STEP5 return check makeQforFront : consider section')
    print(pd.DataFrame(result5))
    print('\n\n\n')

    
    result4 = model2.get({'tx':'pickq'})
    print('\n##### STEP4 return check')
    print(result4)
    print('\n\n\n')

    
    result5 = model2.get({'tx':'answerq'})
    print('\n##### STEP5 return check makeQforFront : consider section')
    print(pd.DataFrame(result5))
    print('\n\n\n')
    
    result6 = model2.get({'tx':'request_for_followup_q'})
    print('\n##### STEP6 return check')
    print(result6)
    print('\n\n\n')

    result7 = model2.get({'tx':'receive_followup_q'})
    print('\n##### STEP7 return check')
    print(pd.DataFrame(result7))
    print('\n\n\n')
    
    result6 = model2.get({'tx':'request_for_followup_q'})
    print('\n##### STEP6 return check')
    print(result6)
    print('\n\n\n')

    result7 = model2.get({'tx':'receive_followup_q'})
    print('\n##### STEP7 return check')
    print(pd.DataFrame(result7))
    print('\n\n\n')
    
    result6 = model2.get({'tx':'request_for_followup_q'})
    print('\n##### STEP6 return check')
    print(result6)
    print('\n\n\n')

    result7 = model2.get({'tx':'receive_followup_q'})
    print('\n##### STEP7 return check')
    print(pd.DataFrame(result7))
    print('\n\n\n')

    # pd.DataFrame(model2.q_initial_scored).to_csv('./q_initial_scored.csv')
    # pd.DataFrame(model2.picked_q_history).to_csv('./question_history.csv')
    # pd.DataFrame(model2.answer_history).to_csv('./answer_history.csv')
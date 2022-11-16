import typing
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer  #sentence_transformers 설치 필요

PRIORITYSCORE_FOR_CVJD = 1000 #cvjd base question을 상단에 올리는 데에 사용됨(score에 가산)
PRIORITYSCORE_FOR_FOLLOWUP = 1000000 #follow up question을 상단에 올리는 데에 사용됨(score에 가산)


class Model2:

    def __init__(self) :

        print('>> Model2 is instantiated.\n')
        
        ######################################
        ######## sample data section  ########
        ######################################

        # init argument : question bank 전체(dict)
        self.example_q_from_bank = { 'qfrombank' : 
                            [ {'section' : 'experience',
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
                            'tag_lv0' : 'cvjd_based',
                            'tag_lv1' : 'skill'},
                            {'section' : 'experience',
                            'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'cvjd_based',
                            'tag_lv1' : 'experience'},
                            {'section' : 'experties',
                            'question' : 'You said you have studied reinforcement learning. What areas did you research in detail?',
                            'source' : 'cvjd',
                            'tag_lv0' : 'cvjd_based',
                            'tag_lv1' : 'experties'} ] }

        self.example_total_time = 20 #총 면접시간(분)
        self.example_timeperqa_bysection = [2, 2, 2, 2] #qa 소요시간(분)
        self.example_section_ratio = [40, 20, 40, 0] #평가항목별 비중(합계100)

        # (initial info) 면접평가표의 평가문항(optional한 부분이나 시나리오를 위해 필요할 것으로 생각됨)
        self.exampleSection = ['experience', 'knowledge', 'experties', 'relationship']
        # (initial info) 최초 context 계산 등에 필요한 cv, jd 정보 (format은 아래를 가정함)
        self.example_info_cv = [{'factor' : 'educate', 'contents' : 'graduate school'},
                {'factor' : 'skill', 'contents' : 'python, R, javascript, webprogramming'},
                {'factor' : 'experience', 'contents' : 'Big project'} ]
        self.example_info_jd = [{'factor' : 'Skills and Qualifications', 'contents' : 'Excellent understanding of machine learning techniques and algorithms, such as k-NN, Naive Bayes, SVM, Decision Forests, etc.'},
                {'factor' : 'Skills and Qualifications', 'contents' : 'Great communication skills'},
                {'factor' : 'Responsibilities', 'contents' : 'Enhancing data collection procedures to include information that is relevant for building analytic systems'} ]
        # (interaction) interviewer가 pick한 question 정보
        self.example_picked_q_info = { 'from' : 'interviewer',  
                      'info' : {'flag' : 23, 'question' : 'You only listed projects in school classes. Have you ever done any projects outside of classes?'}  }
        self.example_picked_q_info2 = { 'from' : 'interviewer',  
                      'info' : {'flag' : 25, 'question' : 'follow-up q1'}  }
        # (interaction) interviewee answer 정보
        self.example_answer_info = { 'from' : 'interviewee', 
                        'info' : {'flag' : 1, 'answer' : 'It was the matrix multiplication parallel project with MPI. It was challenging to me'} }
        self.example_answer_info2 = { 'from' : 'interviewee', 
                        'info' : {'flag' : 2, 'answer' : 'answer for the follow-up q1'} }


        # (interaction) question from model3 정보
        self.example_q_from_m3 = { 1: 'follow-up q1',  2: 'follow-up q2',  3: 'follow-up q3'}
        
        # { 'qfromm3' :  
        #                           [{'section' : 'experience',
        #                             'question' : 'Think back to a data project you have worked on where you encountered a problem or challenge. What was the situation, what was the obstacle, and how did you overcome it?',
        #                             'source' : 'model3',
        #                             'tag_lv0' : 'experience',
        #                             'tag_lv1' : 'project'} ] }

        ####################################################
        ######## initial argument variable section  ########
        ####################################################

        ### init argument variables section starts--------------------------------------
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

        self.section = list() #평가항목
        self.info_cv = list() #cv 정보
        self.info_jd = list() #jd 정보
        
        self.total_time = 20 #총 면접시간(분)
        self.time_left = 20 #남은 면접시간(분)
        self.timeperqa_bysection = list() #평가항목별 qa 예상소요시간(분)
        self.section_ratio = list() #평가항목별 비중(합계100)

        self.time_limit_by_section = list() #평가항목별 소요시간
        self.time_left_by_section = list() #평가항목별 소요시간
        self.possible_q_cnt_by_section = list() #남은시간을 고려한 section별 질문개수

        ### init argument variables section ends --------------------------------------


        ############################################
        ######## model and context section  ########
        ############################################

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


        ###########################################
        ######## question scoring section  ########
        ###########################################

        # the first scored q list (before interview start / all questions from bank or else)
        self.q_initial_scored = list()
        '''
         - list
         - q_initial_scoring 함수로 생성됨
         - model3으로부터 온 question은 append 됨
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


        ##################################################
        ######## qa interaction variable section  ########
        ##################################################



        # interviewer가 선택한 question list
        self.picked_q_history = list()
        # interviewee가 답변한 answer
        self.answer_history = list()
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

        self.follow_up_q = list() #q_remaining에 더해질 follow_up_q
        self.follow_up_q_mode = False #follow_up_mode가 되면 True가 된다.(Front에 q보내고 다시 False로 전환)
        self.follow_up_q_ready = False #follow_up_q가 준비되면 True가 된다.(Front에 q보내고 다시 False로 전환)



    # 초기 자료입력 셋팅 method 
    def set_initial_state(self, q_from_bank : dict, q_from_cvjd : dict, section : list, info_cv : list, info_jd : list, total_time : int, timeperqa_bysection : list, section_ratio : list ) :
        self.q_from_bank = q_from_bank
        self.q_from_cvjd = q_from_cvjd
        self.section = section #평가항목
        self.section_ratio = section_ratio #평가항목별 비중(합계100)
        self.info_cv = info_cv
        self.info_jd = info_jd
        self.total_time = total_time #총 면접시간(분)
        self.time_left = total_time #남은 면접시간(분)
        self.timeperqa_bysection = timeperqa_bysection #평가항목별 qa 예상소요시간(분)

        self.time_limit_by_section = [i * self.total_time / 100 for i in self.section_ratio]
        self.time_left_by_section = [i * self.total_time / 100 for i in self.section_ratio]
        self.possible_q_cnt_by_section = [ int( t / self.timeperqa_bysection[i] )  for i, t in enumerate(self.time_left_by_section)]

    # intial context 계산 with 초기자료 (***context 계산방법 세부적으로 implement해야함***)
    def set_initial_context(self) :
        '''
        - 기능 : initial context를 np.array vector로 계산한 뒤 self.initial_context에 입력
        - used variables : self.info_cv(list of dictionaries), self.info_jd(list of dictionaries)
        - context 계산방법 세부적으로 implement 해야함
        '''
        print('>> set_initial_context starts...')
        df_cv = pd.DataFrame(self.info_cv)
        df_jd = pd.DataFrame(self.info_jd)
        cv_embedding = self.embed_model.encode(df_cv['contents'].tolist()) 
        jd_embedding = self.embed_model.encode(df_jd['contents'].tolist()) 
        joined_embedding = cv_embedding.sum(axis=0) + jd_embedding.sum(axis=0)

        self.initial_context = joined_embedding  #calculate and set initial context
        self.current_context = joined_embedding #update current context
        self.context_history.append(self.initial_context.copy()) #update context history
        print('-------   done   -------\n')

    # current context 
    def get_current_context(self) : return self.current_context

    # update context (***context 계산방법 세부적으로 implement해야함*** / 현재 단순하게 (+) 하는 식으로 일단 구현 )
    def update_context(self, input_context : np.ndarray) :  
        '''
        - 기능 : middle로부터 온 Q 또는 A의 context를 이용하여 전체 context를 업데이트
        - args
            - input_context(np.ndarray) : embedmodel을 이용하여 vector로 변형된 context
        '''
        self.current_context += input_context
        self.context_history.append(self.current_context.copy())
        
    # score는 일단 dot product로 간단한게 구현함 ※세부구현해야함
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
        print('>> q_initial_scoring start...')
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
        print('-------   done   -------\n')

    def get_q_initial_scored(self) : return self.q_initial_scored

    def get_q_remaining(self) : return self.q_remaining

    # Front에 보낼 Q
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
        
        # convert q_remaining into DataFrame(follow_up Q 상황이면 준비된 q도 포함하여 다룬다.)
        if self.follow_up_q_ready :
            df = pd.DataFrame( self.get_q_remaining() + self.follow_up_q )
            self.follow_up_q_mode = False # 사용후 mode 꺼주기
            self.follow_up_q_ready = False # 사용후 mode 꺼주기
        else :
            df = pd.DataFrame( self.get_q_remaining() )

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


        if not ordering_section_first :
            return df[['order', 'section', 'question', 'source', 'score']][:num].to_dict(orient='records')
        else :
            df_new = pd.DataFrame(columns = df.columns)
            for i in range(len(self.section), 0, -1) :
                # df_new = pd.concat([df_new, df[ df['section_tmp_order']==i][:num] ], axis = 0)
                df_new = pd.concat([df_new, df[ df['section_tmp_order']==i][:self.possible_q_cnt_by_section[len(self.section)-i]] ], axis = 0) 
                df_new.reset_index(drop = True, inplace = True)
                df_new['order'] = df_new.index
            return df_new[['order', 'section', 'question', 'source', 'score']].to_dict(orient='records')

    # interviewer choosed q( middle로부터 받는 함수)
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

        # context 계산 후 업데이트 ※ 세부구현 필요 (Q만 가지고 update하는게 맞을지 의문, A와 조화를 이뤄야할듯)
        context = self.embed_model.encode(self.picked_q_now['question'])
        self.update_context(context)
        # Question rescoring까지 할 필요는 없을 듯.. - answer 받으면 하는 것으로


    # interviewee answer ( middle로부터 받는 함수) ★남은 시간(분)도 받을 수 있는지 체크하기
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


    
    def set_follow_up_q_mode(self) : self.follow_up_q_mode = True

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
        q_row = df[ df['question'] == self.picked_q_history[-1] ]
        result = {'question' : self.picked_q_history[-1], 'tag_lv0' : q_row['tag_lv0'].item(), 'tag_lv1' : q_row['tag_lv1'].item(), 'answer' : self.answer_history[-1] }
        self.provide_history_with_m3.append(result) # 제공 내역 기록해두기
        return result


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

        #최직근 Q 정보 가져와서 활용할 예정
        df = pd.DataFrame(self.q_initial_scored)
        q_row = df[ df['question'] == self.picked_q_history[-1] ]

        for col in tmp_df.columns :
            if col == 'question': pass #기입력하였음
            elif col == 'score' : #score는 상단에 위치할 수 있도록 부여
                for i in range(len(df_new[col])) :
                    df_new[col][i] = PRIORITYSCORE_FOR_FOLLOWUP + ( len(df_new[col]) - i ) #score는 상단에 위치할 수 있도록 부여
            elif col == 'source' : #source 표기
                df_new[col] = 'model3'
            else : #나머지는 original question의 format을 따르도록
                df_new[col] = q_row[col].item()
        self.q_initial_scored.append(df_new.to_dict(orient='records')) # follow-up question의 follow-up question을 대비하여...
        self.follow_up_q = df_new.to_dict(orient='records') # model3로부터 제공된 Q 리스트는 임시적인 성격이므로 self.q_remaining에는 보관하지 않고, front 보낼 function에서만 사용한다.
        self.follow_up_q_ready = True
        


    '''
    ※추가 구현해야할 사항 
    - cv jd specific question을 어떻게 다룰지 셋팅(최상단 위치 등) ->done
    - follow up question받아오는 logic ->done
    - time에 따른 문항수 setting
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
            print('\n[ (STEP1) set_initial_with_example starts ]')

            # 초기값 셋팅
            self.set_initial_state (q_from_bank=self.example_q_from_bank, q_from_cvjd=self.example_q_from_cvjd,
                                    section=self.exampleSection, info_cv=self.example_info_cv, info_jd=self.example_info_jd,
                                    total_time=self.example_total_time, timeperqa_bysection=self.example_timeperqa_bysection, section_ratio=self.example_section_ratio)

            # initial context 계산(cv, jd 정보 이용)
            self.set_initial_context()

            #context 계산 잘 되었나 check
            print('>> check current context / show 5 elements')
            print(self.get_current_context()[:5])
            print('-------   done   -------\n')

            # scoring
            self.q_initial_scoring()

            # scoring 잘 되었나 check
            print('>> check get_q_remaining')
            print(pd.DataFrame(self.get_q_remaining()))
            print('-------   done   -------\n')

            print('\n----------- (STEP1) ends with returns ------------\n')

            #return은 프론트에서 사용가능한 Q 목록임(dictionary)
            return self.makeQforFront(ordering_section_first = True, num = 2)

        # (STEP2) interviewer가 Q를 선택
        if (params['tx'] == 'pickq'):
            print('\n[ (STEP2) pickq starts ]')

            # params를 통해 question 내용 읽기
            # self.receive_q_choosed(params['question']) ##실제로는 middle에서 받아오나
            # self.receive_q_choosed(self.example_picked_q_info) ##일단 example로 구현

            # iter 는 테스트를 위한 temporal 변수 ★ 
            if (params['iter'] == 1):
                self.receive_q_choosed(self.example_picked_q_info) ##일단 example로 구현
            else :
                self.receive_q_choosed(self.example_picked_q_info2) ##일단 example로 구현

            
            print('>> check self.picked_q_now')
            print(self.picked_q_now)
            print('-------   done   -------\n')

            # picked_q_info에 따라 update
            self.update_with_picked_q()
    
            print('>> check self.picked_q_history')
            print(self.picked_q_history)
            print('-------   done   -------\n')

            print('>> check get_q_remaining')
            print(pd.DataFrame(self.get_q_remaining()))
            print('-------   done   -------\n')
            

            print('>> check current context / show 5 elements')
            print(self.get_current_context()[:5])
            print('-------   done   -------\n')

            print('>> check context history / show 5 elements')
            tmp = self.context_history
            for i in tmp :
                print(i[:5])
            print('-------   done   -------\n')

            print('\n----------- (STEP2) ends with returns ------------\n')
            return {'is_done' : True}

        # (STEP3) interviewee가 Answer
        if (params['tx'] == 'answerq'):
            print('\n[ (STEP3) answerq starts ]')
            # params를 통해 answer 내용 읽기
            # self.receive_answer(params['answer']) ##실제로는 middle에서 받아오나
            time_left = self.time_left 
            # self.receive_answer(answer_info=self.example_answer_info, time_left=time_left-2) ##일단 example로 구현 / ★일단2분 감소로 구현
            # iter 는 테스트를 위한 temporal 변수 ★ #남은시간 나중에 middle로부터 받아오기★
            if (params['iter'] == 1):
                self.receive_answer(answer_info=self.example_answer_info, time_left=time_left-2) ##일단 example로 구현
            else :
                self.receive_answer(answer_info=self.example_answer_info2, time_left=time_left-2) ##일단 example로 구현
            
            print('>> check self.answer_now')
            print(self.answer_now)
            print('-------   done   -------\n')

            # picked_q_info에 따라 update
            self.update_with_answer()
            
            print('>> check self.answer_history')
            print(self.answer_history)
            print('-------   done   -------\n')
            
            print('>> check current context / show 5 elements')
            print(self.get_current_context()[:5])
            print('-------   done   -------\n')

            print('>> check context history / show 5 elements')
            tmp = self.context_history
            for i in tmp :
                print(i[:5])
            print('-------   done   -------\n')

            # rescoring 잘 되었네 check
            print('>> check whether question re-scoring works by get_q_remaining')
            print(pd.DataFrame(self.get_q_remaining()))
            print('-------   done   -------\n')

            print('\n----------- (STEP3) ends with returns ------------\n')
            return self.makeQforFront(ordering_section_first = True, num = 2)
            

        # (STEP4) interviewer가 follow-up q를 요청
        if (params['tx'] == 'request_for_followup_q'):
            print('\n[ (STEP4) request_for_followup_q starts ]')
            print('\n----------- (STEP4) ends with returns ------------\n')
            return self.provide_latest_qa_to_m3()


        # (STEP5) model3이 choose한 q list  작헙 후 리턴하기
        if (params['tx'] == 'receive_followup_q'):
            print('\n[ (STEP5) receive_followup_q starts ]')
            # self.receive_q_from_m3(params['q_from_m3']) ##실제로는 middle에서 받아오나
            self.receive_q_from_m3(q_from_m3=self.example_q_from_m3)##일단 example로 구현
            print('\n----------- (STEP5) ends with returns ------------\n')
            return self.makeQforFront(ordering_section_first = True, num = 2)


    def __del__(self):
        pass

if __name__ == '__main__':


    model2 = Model2() 


    result1 = model2.get({'tx':'set_initial_with_example'})
    print('\n### STEP1 return check makeQforFront : consider section / 2 question per section')
    print(pd.DataFrame(result1))
    print('-------   done   -------\n')

    # iter 는 테스트를 위한 temporal 변수 ★
    result2 = model2.get({'tx':'pickq', 'iter' : 1})
    print('\n### STEP2 return check')
    print(result2)

    # iter 는 테스트를 위한 temporal 변수 ★
    result3 = model2.get({'tx':'answerq', 'iter' : 1})
    print('\n### STEP3 return check makeQforFront : consider section / 2 question per section')
    print(pd.DataFrame(result3))

    result4 = model2.get({'tx':'request_for_followup_q'})
    print('\n### STEP4 return check')
    print(result4)

    result5 = model2.get({'tx':'receive_followup_q'})
    print('\n### STEP5 return check')
    print(pd.DataFrame(result5))

    # iter 는 테스트를 위한 temporal 변수 ★
    result6 = model2.get({'tx':'pickq', 'iter' : 2})
    print('\n### STEP6(step2 again) return check')
    print(result6)

    # iter 는 테스트를 위한 temporal 변수 ★
    result7 = model2.get({'tx':'answerq', 'iter' : 2})
    print('\n### STEP7(step3 again) return check makeQforFront : consider section / 2 question per section')
    print(pd.DataFrame(result7))
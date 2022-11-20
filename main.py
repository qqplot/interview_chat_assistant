# TODO: mashalling responses
# TODO: user identifier
# TODO: cv & jd infomation retrieval from model 1
# TODO: middle-end logging
from flask import Flask
from flask_restx import Api, Resource, fields, inputs

from model1 import Model1
from model2 import Model2
from model3 import Model3

app = Flask(__name__)
app.config['RESTX_MASK_SWAGGER'] = False
# app.config['SWAGGER_UI_DOC_EXPANSION'] = 'full'
app.config['SWAGGER_UI_DOC_EXPANSION'] = 'list'
app.config['WTF_CSRF_ENABLED'] = False

api = Api(app, version='0.1', title='Interview Assistant',
    description='interview assistant service for interviewers',
)

ns_model = api.namespace('model', description='An integrated model of the Interview Assistant backend')
# ns_model1 = api.namespace('model1', description='Model 1 of the Interview Assistant backend')
# ns_model2 = api.namespace('model2', description='Model 2 of the Interview Assistant backend')
# ns_model3 = api.namespace('model3', description='Model 3 of the Interview Assistant backend')

model_ = api.model('Model1', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details')
})

STATE = {}
STATE_HIST = []
EVENT_HIST = []

# model1 = Model1()
# model2 = Model2()
# model3 = Model3()
model1 = model2 = model3 = None
# model3.get({'tx': 'follow'})

parser_get_interview_session = api.parser()
parser_get_interview_session.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
parser_get_interview_session.add_argument('interviewee_id', type=str, help='unique identifier for the interviewee (applicant)', required=True, default='elon_musk')
parser_get_interview_session.add_argument('tot_time', type=int, help='total time for the interfiew (minute)', required=True, default=30)

@ns_model.route('/interview_session/')
class InterviewSession(Resource):
    '''Shows ...'''
    # @ns.doc('list_...')
    # @ns.marshal_list_with(model_)
    # parser.add_argument('in_files', type=FileStorage, location='files')
    # @ns.marshal_with(model1, code=200, description='success')
    @ns_model.expect(parser_get_interview_session)
    def get(self):
        '''start or restart the interview session'''
        global STATE, model1, model2, model3

        args = parser_get_interview_session.parse_args()
        try:
            if STATE:
                STATE_HIST.append(STATE)
                # model1 = Model1()
                # model2 = Model2()
                # model3 = Model3()
                del model1, model2, model3
                model1, model2, model3 = Model1(), Model2(), Model3()
                model3.get({'tx': 'follow'})
                STATE = {}
            STATE['interview_id'] = args['interview_id']
            STATE['interviewee_id'] = args['interviewee_id']
            STATE['tot_time'] = args['tot_time']
            STATE['rem_time'] = STATE['tot_time']
            STATE['round'] = 0
            return {'msg': 'succeeded'}
        except Exception as e:
            return {'msg': 'failed', 'debug': str(e)}, 400

parser_get_question = api.parser()
parser_get_question.add_argument('question', type=str, help='what question is picked by the interviewer previously?')
parser_get_question.add_argument('answer', type=str, help='what answer is given by the interviewee previously?')
parser_get_question.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
# parser_get_question.add_argument('config_tot_time', type=int, help='total time for the interfiew (minute)', required=True, default=30)
# parser_get_question.add_argument('config_strategy', type=int, help='strategy on how to proceed the interview')
parser_get_question.add_argument('is_follow_up', type=inputs.boolean, help='whether it is follow-up or not', required=True, default='false')

@ns_model.route('/question/')
class Question(Resource):
    '''Shows ...'''
    # @ns.doc('list_...')
    # @ns.marshal_list_with(model_)
    # parser.add_argument('in_files', type=FileStorage, location='files')
    # @ns.marshal_with(model1, code=200, description='success')
    @ns_model.expect(parser_get_question)
    def get(self):
        '''get recommended questions from the models'''
        args = parser_get_question.parse_args()
        args_to_backend = {
            'interview_id': args['interview_id'], # DS001, ...
        }
        if args['interview_id'] == STATE.get('interview_id'):
            STATE['rem_time'] -= 2 # FIXME: decrement unit
            args_to_backend['interview_id'] = STATE['interview_id']
            args_to_backend['interviewee_id'] = STATE['interviewee_id']
            args_to_backend['tot_time'] = STATE['tot_time']
            args_to_backend['rem_time'] = STATE['rem_time']
            if STATE['round'] == 0:
                if args['is_follow_up']:
                    # return {'msg': 'at least one question should have been picked by the interviewer'}, 400
                    return {'msg': 'at least 2 questions should have been picked by the interviewer'}, 400 # FIXME: at least 2, right?
                args_to_backend['tx'] = 'set_initial_with_example'
                ret = model2.get(args_to_backend)

                STATE['round'] += 1
                return ret
            else:
                if not args['question'] or not args['answer']:
                    return {'msg': 'question and answer must be provided'}, 400
                if args['is_follow_up']:
                    if STATE['round'] <= 1:
                        # return {'msg': 'at least one question should have been picked by the interviewer'}, 400
                        return {'msg': 'at least 2 questions should have been picked by the interviewer'}, 400 # FIXME: at least 2, right?

                    args_to_backend['tx'] = 'pickq'
                    args_to_backend['from'] = 'interviewer'
                    args_to_backend['info'] = {'flag': 0, 'question': args['question']} # FIXME: flag
                    ret = model2.get(args_to_backend) # FIXME: pickq return message handling
                    if not ret['is_done']:
                        return {'msg': 'failed to record the picked question to the model'}, 400

                    args_to_backend['tx'] = 'answerq'
                    args_to_backend['from'] = 'interviewee'
                    args_to_backend['info'] = {'flag': 0, 'answer': args['answer']} # FIXME: flag
                    _ = model2.get(args_to_backend) # the result is not used (ignored)

                    args_to_backend['tx'] = 'request_for_followup_q'
                    ret = model2.get(args_to_backend)

                    args_to_backend['tx'] = 'answerq'
                    args_to_backend['from'] = 'interviewee'
                    args_to_backend['info'] = ret
                    args_to_backend['info']['flag'] = 0 # FIXME: flag
                    ret = model3.get(args_to_backend)

                    args_to_backend['tx'] = 'receive_followup_q'
                    del args_to_backend['from']
                    del args_to_backend['info']
                    args_to_backend.update({'fq': dict(zip(range(1, 3 + 1), ret))})
                    ret = model2.get(args_to_backend)

                    STATE['round'] += 1
                    return ret
                else:
                    args_to_backend['tx'] = 'pickq'
                    args_to_backend['from'] = 'interviewer'
                    args_to_backend['info'] = {'flag': 0, 'question': args['question']} # FIXME: flag
                    ret = model2.get(args_to_backend) # FIXME: pickq return message handling
                    if not ret['is_done']:
                        return {'msg': 'failed to record the picked question to the model'}, 400

                    args_to_backend['tx'] = 'answerq'
                    args_to_backend['from'] = 'interviewee'
                    args_to_backend['info'] = {'flag': 0, 'answer': args['answer']} # FIXME: flag
                    ret = model2.get(args_to_backend)

                    STATE['round'] += 1
                    return ret
        else:
            return {'msg': 'the interview session id is not active now'}, 400

parser_put_config = api.parser()
# parser_put_config.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
# parser_put_config.add_argument('tot_time', type=int, help='total time for the interfiew (minute)', required=True, default=30)

parser_get_config = api.parser()
# parser_get_config.add_argument('interviewee_id', type=str, help='unique identifier for the interviewee (applicant)', required=True, default='elon_musk')

@ns_model.route('/config/')
class Config(Resource):
    '''Shows ...'''
    # @ns.doc('list_...')
    # @ns.marshal_list_with(model_)
    # parser.add_argument('in_files', type=FileStorage, location='files')
    # @ns.marshal_with(model1, code=200, description='success')
    @ns_model.expect(parser_put_config)
    def put(self):
        '''(UNDER CONSTRUCTION) register all or some of configurations to the middle-end and model'''
        args = parser_put_config.parse_args()
        return {'msg': 'under construction'}, 404

    @ns_model.expect(parser_get_config)
    def get(self):
        '''retrieve configurations from the middle-end and model'''
        args = parser_get_config.parse_args()
        return STATE

parser_get_interviewee_analysis = api.parser()
# parser_put_config.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
# parser_put_config.add_argument('tot_time', type=int, help='total time for the interfiew (minute)', required=True, default=30)
@ns_model.route('/interviewee_analysis/')
class IntervieweeAnalysis(Resource):
    '''Shows ...'''
    # @ns.doc('list_...')
    # @ns.marshal_list_with(model_)
    # parser.add_argument('in_files', type=FileStorage, location='files')
    # @ns.marshal_with(model1, code=200, description='success')
    @ns_model.expect(parser_get_interviewee_analysis)
    def get(self):
        '''(UNDER CONSTRUCTION) get interviewee's (applicant's) analysis'''
        args = parser_get_interviewee_analysis.parse_args()
        return {'msg': 'under construction'}, 404

if __name__ == '__main__':
    app.run(debug=True)
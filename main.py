from flask import Flask
from flask_restx import Api, Resource, fields

kkk
# import sys
# sys.path.append('..')

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

model1 = Model1()
model2 = Model2()
model3 = Model3()

STATE = {}

parser_get_question = api.parser()
parser_get_question.add_argument('cnt', type=int, help='how many questions do you need?', default=3)
parser_get_question.add_argument('question_prev', type=str, help='what question is picked by the interviewer previously?')
parser_get_question.add_argument('answer_prev', type=str, help='what answer is given by the interviewee previously?')
parser_get_question.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
parser_get_question.add_argument('config_tot_time', type=int, help='total time for the interfiew (minute)', required=True, default=30)
parser_get_question.add_argument('config_strategy', type=int, help='strategy on how to proceed the interview')

parser_put_question = api.parser()
parser_put_question.add_argument('question_prev', type=str, help='what question is picked by the interviewer previously?')
parser_put_question.add_argument('answer_prev', type=str, help='what answer is given by the interviewee previously?', required=True, default='I tried to do my best, sir!')
parser_put_question.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
parser_put_question.add_argument('config_tot_time', type=int, help='total time for the interfiew (minute)', required=True, default=30)
parser_put_question.add_argument('config_strategy', type=int, help='strategy on how to proceed the interview')

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
            'cnt': args['cnt'], # 3, 5, ...
            'question_prev': args['question_prev'], # a single string
            'answer_prev': args['answer_prev'], # a single string
            'interview_id': args['interview_id'], # DS001, ...
            'config_tot_time': args['config_tot_time'], # 30
            'config_strategy': args['config_strategy'], # not determined yet
        }
        if args['interview_id'] not in STATE:
            args_to_backend['tx'] = 'set_initial_with_example'
            STATE[args['interview_id']] = {}
            STATE[args['interview_id']]['rem_time'] = args['config_tot_time']
            args_to_backend['rem_time'] = STATE[args['interview_id']]['rem_time']
            ret = model2.get(args_to_backend)
        else:
            args_to_backend['tx'] = 'answerq'
            STATE[args['interview_id']]['rem_time'] -= 2
            args_to_backend['rem_time'] = STATE[args['interview_id']]['rem_time']
            ret = model2.get(args_to_backend)
        print(STATE)
        return ret

    '''Shows ...'''
    # @ns.doc('list_...')
    # @ns.marshal_list_with(model_)
    # parser.add_argument('in_files', type=FileStorage, location='files')
    # @ns.marshal_with(model1, code=200, description='success')
    @ns_model.expect(parser_put_question)
    def put(self):
        '''put a question picked by the interviewer into the models'''
        args = parser_get_question.parse_args()
        if args['interview_id'] not in STATE:
            return {'msg': 'PUT question is allowed after GET question is performed at least once.'}, 400
        args_to_backend = {
            'tx': 'pickq',
            'answer_prev': args['answer_prev'], # a single string
            'interview_id': args['interview_id'], # DS001, ...
            'config_tot_time': args['config_tot_time'], # 30
            'config_strategy': args['config_strategy'], # not determined yet
        }
        ret = model2.get(args_to_backend)
        return ret

# parser_raw_text = api.parser()
# parser_raw_text.add_argument('cnt', type=int, help='how many raw data to see')
# @ns_model1.route('/raw_text/')
# class Model1_(Resource):
#     '''Shows ...'''
#     # @ns.doc('list_...')
#     # @ns.marshal_list_with(model_)
#     # parser.add_argument('in_files', type=FileStorage, location='files')
#     # @ns.marshal_with(model1, code=200, description='success')
#     @ns_model1.expect(parser_raw_text)
#     def get(self):
#         '''get raw text data'''
#         args = parser_raw_text.parse_args()
#         print(args)
#         ret = model1.get({'tx': 'get_raw_data', 'cnt': args['cnt']})
#         return ret

# parser = api.parser()
# parser.add_argument('txt', type=str, help='Some param')
# @ns_model2.route('/upper/')
# class Model2_(Resource):
#     '''Shows ...'''
#     # @ns.doc('list_...')
#     # @ns.marshal_list_with(model_)
#     # parser.add_argument('in_files', type=FileStorage, location='files')
#     # @ns.marshal_with(model1, code=200, description='success')
#     @ns_model2.expect(parser)
#     def get(self):
#         '''get upper-case text'''
#         args = parser.parse_args()
#         ret = model2.get({'tx': 'get_upper', 'txt': list(args['txt'].split('/'))})
#         return ret

# @ns_model3.route('/raw_upper/')
# class Model3_(Resource):
#     '''Shows ...'''
#     # @ns.doc('list_...')
#     # @ns.marshal_list_with(model_)
#     parser = api.parser()
#     parser.add_argument('txt', type=str, help='Some param')
#     # parser.add_argument('in_files', type=FileStorage, location='files')
#     # @ns.marshal_with(model1, code=200, description='success')
#     # @ns_model3.expect(parser)
#     def get(self):
#         '''get upper-case version of raw text data'''
#         args = parser.parse_args()
#         ret = model3.get({'tx': 'get_raw_text_upper'})
#         return ret

if __name__ == '__main__':
    app.run(debug=True)

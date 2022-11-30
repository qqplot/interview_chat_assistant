# TODO: mashalling responses
# logging: https://gist.github.com/alexaleluia12/e40f1dfa4ce598c2e958611f67d28966
# TODO: 20221120
# * (DONE) GET config (remaining time)
# * front-end에 추천했던 question들 중에만 pickq() 제공이 가능하도록 명시적으로 통제해야 하는지?
# * (DONE) SET interview_session (interviewee id)
# * (DONE) modelx not instantiated -> error handling
from flask import Flask, jsonify, make_response, request
from flask_restx import Api, Resource, fields, inputs
from waitress import serve
import os
import logging
# from time import strftime
import io
from contextlib import redirect_stdout, contextmanager
import contextlib
import pandas as pd

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

TIME_DEC_UNIT = 2

DEBUG = False

model1 = model2 = model3 = None

parser_put_interview_session = api.parser()
parser_put_interview_session.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
parser_put_interview_session.add_argument('interviewee_id', type=str, help='unique identifier for the interviewee (applicant)', required=True, default='Rachel_Lee')
parser_put_interview_session.add_argument('position', type=str, help='position to which the interviewee (applicant) apply', required=True, default='Data Scientist')
parser_put_interview_session.add_argument('tot_time', type=int, help='total time for the interview (minute)', required=True, default=30)
parser_put_interview_session.add_argument('sec_time_arr', type=str, help='time arrangement for sections (ordered)', required=False, default='intro:5;programmingskill:10;experience:20;personality:20;expertise:25;knowledge:20')
parser_put_interview_session.add_argument('cue', type=str, help='cue', default='')

@ns_model.route('/interview_session/')
class InterviewSession(Resource):
    '''Shows ...'''
    # @ns.doc('list_...')
    # @ns.marshal_list_with(model_)
    # parser.add_argument('in_files', type=FileStorage, location='files')
    # @ns.marshal_with(model1, code=200, description='success')
    @ns_model.expect(parser_put_interview_session)
    def put(self):
        '''start or restart the interview session'''
        global STATE, model1, model2, model3

        args = parser_put_interview_session.parse_args()
        try:
            if STATE:
                STATE_HIST.append(STATE)
                del model1, model2, model3
            model1, model2, model3 = Model1(), Model2(), Model3()
            with suppress():
                model3.get({'tx': 'follow'})
            STATE = {}
            STATE['interview_id'] = args['interview_id']
            STATE['interviewee_id'] = args['interviewee_id']
            STATE['tot_time'] = args['tot_time']
            STATE['rem_time'] = STATE['tot_time']
            STATE['round'] = 0
            STATE['cue'] = args['cue']
            STATE['position'] = args['position']
            if args.get('sec_time_arr'):
                STATE['sec_time_arr'] = args.get('sec_time_arr')
            else:
                STATE['sec_time_arr'] = 'intro:20;programmingskill:20;experience:20;personality:20;expertise:20;knowledge:20'
            STATE['sec_time_arr'] = [tuple(i.split(':')) for i in STATE['sec_time_arr'].split(';')]
            # return {'msg': 'succeeded'}
            response = make_response(jsonify({'msg': 'succeeded'}), 200)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response
        except Exception as e:
            # return {'msg': 'failed', 'debug': str(e)}, 400
            response = make_response(jsonify({'msg': 'failed', 'debug': str(e)}), 400)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

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
            args_to_backend['interview_id'] = STATE['interview_id']
            args_to_backend['interviewee_id'] = STATE['interviewee_id']
            args_to_backend['tot_time'] = STATE['tot_time']
            args_to_backend['rem_time'] = STATE['rem_time']
            args_to_backend['cue'] = STATE['cue']
            args_to_backend['position'] = STATE['position']
            args_to_backend['sec_time_arr'] = STATE['sec_time_arr']
            if STATE['round'] == 0:
                if args['is_follow_up']:
                    return {'msg': 'at least one question should have been picked by the interviewer'}, 400

                args_to_backend['tx'] = 'runm1'
                with suppress():
                    ret = model1.get(args_to_backend)

                args_to_backend['cvjdq'] = ret['qfromcvjd']
                args_to_backend['tx'] = 'set_initial_with_example'
                with suppress():
                    ret = model2.get(args_to_backend)
                    EVENT_HIST.append([ret])

                STATE['round'] += 1
                # return ret
                response = make_response(jsonify(ret), 200)
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response
            else:
                STATE['rem_time'] -= TIME_DEC_UNIT
                args_to_backend['rem_time'] = STATE['rem_time']
                if not args['question'] or not args['answer']:
                    # return {'msg': 'question and answer must be provided'}, 400
                    response = make_response(jsonify({'msg': 'question and answer must be provided'}), 400)
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
                if args['is_follow_up']:
                    args_to_backend['tx'] = 'pickq'
                    args_to_backend['from'] = 'interviewer'
                    args_to_backend['info'] = {'flag': 0, 'question': args['question']} # FIXME: flag
                    with suppress():
                        ret = model2.get(args_to_backend) # FIXME: pickq return message handling
                        # EVENT_HIST[-1].append(args_to_backend)
                    if not ret['is_done']:
                        # return {'msg': 'failed to record the picked question to the model'}, 400
                        response = make_response(jsonify({'msg': 'failed to record the picked question to the model'}), 400)
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response

                    args_to_backend['tx'] = 'answerq'
                    args_to_backend['from'] = 'interviewee'
                    args_to_backend['info'] = {'flag': 0, 'answer': args['answer']} # FIXME: flag
                    with suppress():
                        _ = model2.get(args_to_backend) # the result is not used (ignored)

                    args_to_backend['tx'] = 'request_for_followup_q'
                    with suppress():
                        ret = model2.get(args_to_backend)

                    args_to_backend['tx'] = 'answerq'
                    args_to_backend['from'] = 'interviewee'
                    args_to_backend['info'] = ret
                    args_to_backend['info']['flag'] = 0 # FIXME: flag
                    with suppress():
                        ret = model3.get(args_to_backend)

                    args_to_backend['tx'] = 'receive_followup_q'
                    del args_to_backend['from']
                    del args_to_backend['info']
                    args_to_backend.update({'fq': dict(zip(range(1, 3 + 1), ret))})
                    with suppress():
                        ret = model2.get(args_to_backend)
                        # EVENT_HIST[-1].append(args_to_backend)
                        EVENT_HIST[-1].append(args)
                        EVENT_HIST.append([ret])

                    STATE['round'] += 1
                    # return ret
                    response = make_response(jsonify(ret), 200)
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
                else:
                    args_to_backend['tx'] = 'pickq'
                    args_to_backend['from'] = 'interviewer'
                    args_to_backend['info'] = {'flag': 0, 'question': args['question']} # FIXME: flag
                    with suppress():
                        ret = model2.get(args_to_backend) # FIXME: pickq return message handling
                        # EVENT_HIST[-1].append(args_to_backend)
                    if not ret['is_done']:
                        # return {'msg': 'failed to record the picked question to the model'}, 400
                        response = make_response(jsonify({'msg': 'failed to record the picked question to the model'}), 400)
                        response.headers.add('Access-Control-Allow-Origin', '*')
                        return response

                    args_to_backend['tx'] = 'answerq'
                    args_to_backend['from'] = 'interviewee'
                    args_to_backend['info'] = {'flag': 0, 'answer': args['answer']} # FIXME: flag
                    with suppress():
                        ret = model2.get(args_to_backend)
                        # EVENT_HIST[-1].append(args_to_backend)
                        EVENT_HIST[-1].append(args)
                        EVENT_HIST.append([ret])

                    STATE['round'] += 1
                    # return ret
                    response = make_response(jsonify(ret), 200)
                    response.headers.add('Access-Control-Allow-Origin', '*')
                    return response
        else:
            # return {'msg': 'the interview session id is not active now'}, 400
            response = make_response(jsonify({'msg': 'the interview session id is not active now'}), 400)
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response

parser_put_config = api.parser()
# parser_put_config.add_argument('interview_id', type=str, help='unique identifier for a single interview', required=True, default='DS001')
# parser_put_config.add_argument('tot_time', type=int, help='total time for the interfiew (minute)', required=True, default=30)
parser_put_config.add_argument('cue', type=str, help='cue', default='')

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
        '''register all or some of configurations to the middle-end and model'''
        args = parser_put_config.parse_args()
        try:
            STATE['cue'] = args['cue']
            response = make_response(jsonify({'msg': 'succeeded'}), 200)
        except Exception:
            response = make_response(jsonify({'msg': 'error occurred'}), 400)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    @ns_model.expect(parser_get_config)
    def get(self):
        '''retrieve configurations from the middle-end and model'''
        args = parser_get_config.parse_args()
        # return STATE
        response = make_response(jsonify(STATE), 200)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

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
        # return {'msg': 'under construction'}, 404
        response = make_response(jsonify({'msg': 'under construction'}), 404)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

parser_get_summary = api.parser()
@ns_model.route('/summary/')
class Summary(Resource):
    '''Shows ...'''
    # @ns.doc('list_...')
    # @ns.marshal_list_with(model_)
    # parser.add_argument('in_files', type=FileStorage, location='files')
    # @ns.marshal_with(model1, code=200, description='success')
    @ns_model.expect(parser_get_summary)
    def get(self):
        '''get summary of questions and answers from the interview'''
        args = parser_get_summary.parse_args()
        # response = make_response(jsonify({'msg': 'under construction'}), 404)
        acc_qa = []
        for evt in EVENT_HIST:
            if len(evt) < 2: # in case of model errors, evt[1] can be non-existent
                continue
            q = evt[1]['question']
            # q = pd.DataFrame(evt[0]).query(f"question == '{q}'")[['question', 'score', 'section', 'source']].to_dict(orient='records')[0]
            df_q = pd.DataFrame(evt[0])
            q = df_q[df_q.question == q][['question', 'score', 'section', 'source']].to_dict(orient='records')[0]
            a = evt[1]['answer']
            a = {'answer': a}
            acc_qa.append(q)
            acc_qa.append(a)

        response = make_response(jsonify(acc_qa))
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

@app.after_request
def after_request(response):
    # timestamp = strftime('[%Y-%b-%d %H:%M]')
    # logger.info('%s %s %s %s %s %s %s', timestamp, request.remote_addr, request.method, request.scheme, request.full_path, response.status, response.data)
    if request.full_path.startswith(('/?', '/swagger')):
        logger.info('%s %s %s %s %s', request.remote_addr, request.method, request.scheme, request.full_path, response.status)
    else:
        logger.info('%s %s %s %s %s %s', request.remote_addr, request.method, request.scheme, request.full_path, response.status, response.data)
    return response

@contextmanager
def suppress():
    if not DEBUG:
        with open(os.devnull, "w") as null:
            with redirect_stdout(null):
                yield
    else:
        yield contextlib.nullcontext


if __name__ == '__main__':
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    file_handler = logging.FileHandler("./main.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    DEBUG = False
    if os.path.exists('debug'):
        DEBUG = True

    if DEBUG:
        app.run(debug=True)
    else:
        logger.info(" * Serving Flask app 'main'")
        logger.info('NOTICE: This is a production and test server.')
        logger.info(' * Running on http://127.0.0.1:5000')
        serve(app, host='127.0.0.1', port=5000)
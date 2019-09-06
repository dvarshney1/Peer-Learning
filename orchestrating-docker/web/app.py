# app.py
# import json
from flask import Flask, jsonify, json
from flask import request, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_restplus import Api, Namespace, abort, Resource, fields, marshal_with
from config import BaseConfig
from sqlalchemy import func, select, text, exists, and_
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, verify_jwt_in_request, get_jwt_identity, get_jwt_claims
from functools import wraps
from flask_cors import CORS, cross_origin
import psycopg2
import hashlib
import requests

app = Flask(__name__)
CORS(app)
app.config.from_object(BaseConfig)
db = SQLAlchemy(app)

import datetime

from models import *
from logger import *

logger = loggerStart()
from transaction import *
from piazza import *


authorizations = {
    'apikey': {
        'type' : 'apiKey',
        'in': 'header',
        'name': 'Authorization'
    }
}
api = Api(app, authorizations=authorizations, security='apikey')


app.config['JWT_SECRET_KEY'] = 'tD2npsUrdzwTmvHIVQ4m6bKNFSyWXgophaj3DOqxg2dEgPvYVpqk3BZKEsdpI1V'
jwt = JWTManager(app)
jwt._set_error_handler_callbacks(api)
#app.config['JWT_ACCESS_TOKEN_EXPIRES']=86400


s_api = Namespace('SessionInformation', description = 'question session information operations')
re_api = Namespace('EnrollmentInformation', description = 'Registration information operations')
en_api = Namespace('I-ClickerQuestions', description = 'Insert a question operation')
iclkres_api = Namespace('IclickerReponse', description = 'Insert a reponse operation')
q_api = Namespace('StudentQuestions', description = 'student question operations')
lg_api = Namespace('login', description='Authentication')
cu_api = Namespace('create_user', description = 'create/update user information')
co_api = Namespace('courses', description = 'get courses')
cd_api = Namespace('coding environment', description = 'coding environment')

#get_question_model = api.model('qid', {'qid': fields.String(description = 'Question ID to get')})
post_question_model = api.model('question', {'question': fields.String})
delete_question_model = api.model('delete_question', {'qid': fields.String})
get_session_model = api.model('session', {})
post_session_model = api.model('professor', {'course_number': fields.String})
delete_session_model = api.model('Session', {'course_number': fields.String})
get_enterquestion_model = api.model('iqid', {'QuestionNumber': fields.Integer(description = 'Question number to get')})
post_enterquestion_model = api.model('Question', {'Question': fields.String,
                                'optionA': fields.String,
                                'answer': fields.String,
                                'lecturenumber': fields.Integer
                                }
                                )
get_enrollment_model = api.model('enrollment', {'course_number': fields.String})
post_enrollment_model = api.model('Enrollment', {'course_number' : fields.String})
get_iclickerresponse_model = api.model('get_iclicker_response', {'iqid': fields.Integer(description = 'Question number to get'), 'sessionid':fields.String})
post_iclickerresponse_model = api.model('iClicker_post_responses', {'response': fields.Integer})
login_model = api.model('login', {
    'netid': fields.String(description='netid', required=True),
    'password': fields.String(description='Password', required=True)
    })
create_user_model = api.model('create_user', {
    'netid': fields.String(description='netid', required=True),
    'firstname': fields.String(description='firstname', required=True),
    'lastname': fields.String(description='lastname', required=True),
    'password': fields.String(description='Password', required=True)
})
#put_upvotes_model = api.model('upvotes', {})
get_iclickerquestion_model = api.model('iclicker_question_get',{})
post_iclickerquestion_model = api.model('iclicker_question_post', {'sessionid': fields.String,
                                                                   'question': fields.String,
                                                                   'optA': fields.String,
                                                                   'optB': fields.String,
                                                                   'optC': fields.String,
                                                                   'optD': fields.String,
                                                                   'answer': fields.String,
                                                                   'timelimit': fields.Integer
                                                                   })
get_courses_model = api.model('get courses', {})
post_coding_model = api.model('code to run', {'code': fields.String})

api.add_namespace(s_api)
api.add_namespace(re_api)
api.add_namespace(en_api)
api.add_namespace(q_api)
api.add_namespace(re_api)
api.add_namespace(iclkres_api)
api.add_namespace(lg_api)
api.add_namespace(cu_api)
api.add_namespace(co_api)
api.add_namespace(cd_api)


@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    while True:
        try:
            ts = startTransaction()
            instructor = text('SELECT * FROM faculty WHERE netid=:netid')
            response = db.engine.execute(instructor, netid=identity).fetchone()
            updatets = text('UPDATE faculty SET readts = :ts WHERE netid=:netid')
            db.engine.execute(updatets, ts=ts, netid=identity)
            endTransaction()
        except psycopg2.Error:
            rollBack()
        else:
            break
    if response is None:
        return {'role': 'student'}
    else:
        return {'role': 'instructor'}

def instructor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['role'] != 'instructor':
            return "Instructors only!", 403
        else:
            return fn(*args, **kwargs)
    return wrapper

def get_term():
    date = datetime.datetime.today()
    year = date.year
    def get_semester(month, day):
        if (month==8 and day>=27) or month>8:
            return "fa"
        if (month==5 and day>=13) or month>5:
            return "su"
        return "sp"
    semester = get_semester(date.month, date.day)
    return str(year)+"-"+semester

def get_sessionid_student(netid, ts):
    sessionid_query = text('SELECT session.sessionid FROM session JOIN enrollment ON session.course_number = enrollment.course_number AND session.term = enrollment.term WHERE enrollment.netid = :netid')
    sessionid_list = db.engine.execute(sessionid_query, netid=netid).fetchone()
    if sessionid_list is not None:
        sessionid = sessionid_list[0]
        updatets = text('UPDATE enrollment SET readts = :ts WHERE netid = :netid')
        db.engine.execute(updatets, ts=ts, netid=netid)
        updatets2 = text('UPDATE session SET readts = :ts WHERE sessionid = :sessionid')
        db.engine.execute(updatets2, ts=ts, sessionid=sessionid)
        return sessionid
    return None

def get_sessionid_student(netid, ts):
    sessionid_query = text('SELECT session.sessionid FROM session JOIN enrollment ON session.course_number = enrollment.course_number AND session.term = enrollment.term WHERE enrollment.netid = :netid')
    sessionid_list = db.engine.execute(sessionid_query, netid=netid).fetchone()
    if sessionid_list is not None:
        sessionid = sessionid_list[0]
        updatets = text('UPDATE enrollment SET readts = :ts WHERE netid = :netid')
        db.engine.execute(updatets, ts=ts, netid=netid)
        updatets2 = text('UPDATE session SET readts = :ts WHERE sessionid = :sessionid')
        db.engine.execute(updatets2, ts=ts, sessionid=sessionid)
        return sessionid
    return None

@cu_api.route('/')
class createuser(Resource):
    @api.expect(create_user_model)
    @api.doc(body=create_user_model)
    @api.response(200, 'Successful')
    @api.response(401, 'Authentication Failed')
    def post(self):
        params = api.payload
        netid = params.pop("netid")
        firstname = params.pop("firstname")
        lastname = params.pop("lastname")
        password = params.pop("password")

        while True:
            try:
                ts = startTransaction()
                instructor = text('SELECT * FROM faculty WHERE netid=:netid')
                response = db.engine.execute(instructor, netid=netid).fetchone()
                updatets = text('UPDATE faculty SET readts = :ts WHERE netid=:netid')
                db.engine.execute(updatets, ts=ts, netid=netid)

                if response is None:
                    student = text('SELECT * FROM students WHERE netid=:netid')
                    response = db.engine.execute(student, netid=netid).fetchone()
                    updatets = text('UPDATE students SET readts = :ts WHERE netid=:netid')
                    db.engine.execute(updatets, ts=ts, netid=netid)

                    if response is None:
                        if not piazzaLogin(netid, password):
                            endTransaction()
                            abort(401, 'Authentication Failed: Unknown User')
                        newStudent = text('INSERT INTO students (netid, firstname, lastname, writets) VALUES (:netid, :firstname, :lastname, :ts)')
                        db.engine.execute(newStudent, netid=netid, firstname=firstname, lastname=lastname, ts=ts)
                    else:
                        if not piazzaLogin(netid, password):
                            endTransaction()
                            abort(401, 'Authentication Failed: Student: Please use your Piazza login credentials')
                        updateStudent = text('UPDATE students SET firstname=:firstname, lastname=:lastname, writets=:ts WHERE netid=:netid')
                        db.engine.execute(updateStudent, netid=netid, firstname=firstname, lastname=lastname, ts=ts)
                else:
                    if not piazzaLogin(netid, password):
                        endTransaction()
                        abort(401, 'Authentication Failed: Professor: Please use your Piazza login credentials')
                    updateInstructor = text('UPDATE faculty SET firstname=:firstname, lastname=:lastname, writets=:ts WHERE netid=:netid')
                    db.engine.execute(updateInstructor, netid=netid, firstname=firstname, lastname=lastname, ts=ts)
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return "User information has been updated successfully", 200

@lg_api.route('/')
class login(Resource):
    @api.expect(login_model)
    @api.doc(body=login_model)
    @api.response(200, 'Login Successful')
    @api.response(401, 'Login Failed')
    def post(self):
        params = api.payload
        netid = params.pop("netid")
        password = params.pop("password")

        while True:
            try:
                ts = startTransaction()
                instructor = text('SELECT * FROM faculty WHERE netid=:netid')
                response = db.engine.execute(instructor, netid=netid).fetchone()
                updatets = text('UPDATE faculty SET readts = :ts WHERE netid=:netid')
                db.engine.execute(updatets, ts=ts, netid=netid)

                if response is None:
                    student = text('SELECT * FROM students WHERE netid=:netid')
                    response = db.engine.execute(student, netid=netid).fetchone()
                    updatets = text('UPDATE students SET readts = :ts WHERE netid=:netid')
                    db.engine.execute(updatets, ts=ts, netid=netid)
                    if response is None:
                        endTransaction()
                        abort(401, 'Login Failed: Unknown User')
                    else:
                        if not piazzaLogin(netid, password):
                            endTransaction()
                            abort(401, 'Login Failed: Student: Please use your Piazza login credentials')
                        # enter student's piazza login info if they are picked by any of their courses
                        enterPiazza = text('UPDATE courses SET piazza_passwd=:passwd, writets=:ts WHERE piazza_netid=:netid')
                        response = db.engine.execute(enterPiazza, passwd=password, ts=ts, netid=netid)
                else:
                    if not piazzaLogin(netid, password):
                        endTransaction()
                        abort(401, 'Login Failed: Professor: Please use your Piazza login credentials')
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        token = create_access_token(identity=netid)
        return {'token': token}, 200

@s_api.route('/')
class sessioninformation(Resource):
    @jwt_required
    def get(self):
        global response
        # response = None
        netid = get_jwt_identity()
        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid, ts)
                if sessionid is not None:
                    sessionInfo = text('SELECT * FROM session WHERE sessionid=:sessionid')
                    response = db.engine.execute(sessionInfo, sessionid=sessionid).fetchall()
                    updatets = text('UPDATE session SET readts = :ts WHERE sessionid=:sessionid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                    endTransaction()
                else:
                    response = "[]"
                    endTransaction()
                    return response
            except psycopg2.Error:
                rollBack()
            else:
                break
        return json.dumps([dict(row) for row in response])

    @api.expect(post_session_model)
    @api.doc(body=post_session_model)
    @instructor_required
    def post(self):
        params = api.payload
        term = get_term()
        course_number = params.pop("course_number")  # change this to be gotten from table
        while True:
            try:
                ts = startTransaction()
                date_key = str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)
                hash_key = date_key+term+course_number
                sessionid = hashlib.sha256(hash_key.encode('utf-8')).hexdigest()

                checkSession = text('SELECT * FROM session WHERE sessionid=:sessionid')
                sameSession = db.engine.execute(checkSession, sessionid=sessionid).fetchone()
                updatets = text('UPDATE session SET readts = :ts WHERE sessionid = :sessionid')
                db.engine.execute(updatets, ts=ts, sessionid=sessionid)

                checkCourseNumber = text('SELECT * FROM courses WHERE course_number=:course_number')
                courseExists = db.engine.execute(checkCourseNumber, course_number=course_number).fetchone()
                updatets = text('UPDATE courses SET readts = :ts WHERE course_number = :course_number')
                db.engine.execute(updatets, ts=ts, course_number=course_number)

                if sameSession is None and courseExists is not None:
                    newSession = text('INSERT INTO session (sessionid, date, term, course_number, writets) VALUES (:sessionid, :date, :term, :course_number, :ts)')
                    db.engine.execute(newSession, sessionid=sessionid, date=date_key, term=term, course_number=course_number, ts=ts)
                #pass this sessionid to every otehr table
                # student_question_sessionid = text('INSERT INTO ')
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return "Session information has been updated successfully", 200
    @api.expect(delete_session_model)
    @api.doc(body=delete_session_model)
    @instructor_required
    def delete(self):
        params = api.payload
        term = get_term()
        course_number = params.pop("course_number")  # change this to be gotten from table
        while True:
            try:
                ts = startTransaction()
                date_key = str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)
                hash_key = date_key+term+course_number
                sessionid = hashlib.sha256(hash_key.encode('utf-8')).hexdigest()
                checkSessionid = text('SELECT * FROM session WHERE sessionid = :sessionid')
                exists = db.engine.execute(checkSessionid, sessionid=sessionid).fetchone()


                if exists is not None:
                    # post to piazza, then delete questions
                    questionInfo = text('SELECT ques FROM student_question WHERE sessionid = :sessionid')
                    questions = db.engine.execute(questionInfo, sessionid=sessionid).fetchall()
                    updatets = text('UPDATE student_question SET readts = :ts WHERE sessionid = :sessionid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid)

                    # get networkid, netid and password of a student
                    courseInfo = text('SELECT piazza_nid, piazza_netid, piazza_passwd FROM courses WHERE course_number=:course_number AND term=:term')
                    piazzaTuple = db.engine.execute(courseInfo, course_number=course_number, term=term).fetchone()
                    if piazzaTuple is not None:
                        piazza_nid, piazza_netid, piazza_passwd = piazzaTuple[0], piazzaTuple[1], piazzaTuple[2]
                        updatets = text('UPDATE courses SET readts = :ts WHERE course_number = :course_number AND term = :term')
                        db.engine.execute(updatets, ts=ts, course_number=course_number, term=term)

                        piazzaMigration(questions, piazza_nid, piazza_netid, piazza_passwd)

                    # Purge everything
                    purgeQuestions = text('DELETE FROM student_question WHERE sessionid = :sessionid')
                    db.engine.execute(purgeQuestions, sessionid=sessionid)
                    purgeUpvotes = text('DELETE FROM upvotes WHERE sessionid = :sessionid')
                    db.engine.execute(purgeUpvotes, sessionid=sessionid)

                    #Grade responses for IClicker questions
                    total_questions_query = text('SELECT Count(*) FROM iclickerquestion WHERE sessionid = :sessionid')
                    total_questions = db.engine.execute(total_questions_query, sessionid=sessionid).scalar()
                    total_students_query = text('SELECT netid, Count(iclickerresponse.iqid) AS questions_answered FROM iclickerresponse, iclickerquestion WHERE iclickerresponse.sessionid = :sessionid AND iclickerquestion.sessionid = iclickerresponse.sessionid AND iclickerquestion.iqid = iclickerresponse.iqid AND iclickerresponse.responsetime BETWEEN iclickerquestion.starttime AND iclickerquestion.endtime GROUP BY netid')
                    total_students = db.engine.execute(total_students_query, sessionid=sessionid).fetchall()
                    for student in total_students:
                        netid = student[0]
                        answers = student[1]
                        answers = float(answers)
                        grade = answers/total_questions
                        enrollment_grade_query = text('UPDATE enrollment SET grade=:grade, writets=:ts WHERE course_number=:course_number AND term=:term AND netid=:netid')
                        db.engine.execute(enrollment_grade_query, grade=grade, course_number=course_number, term=term, netid=netid, ts=ts)

                    purgeIClickerQuestions = text('DELETE FROM iclickerquestion WHERE sessionid = :sessionid')
                    db.engine.execute(purgeIClickerQuestions, sessionid=sessionid)
                    purgeIClickerResponses = text('DELETE FROM iclickerresponse WHERE sessionid = :sessionid')
                    db.engine.execute(purgeIClickerResponses, sessionid=sessionid)

                    purgeSession = text('DELETE FROM session WHERE sessionid=:sessionid')
                    db.engine.execute(purgeSession, sessionid=sessionid)
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return "Session information has been updated successfully", 200

@en_api.route('/')
class Iclickerquestion(Resource):
    @jwt_required
    @cross_origin()
    def get(self):
        global response
        netid = get_jwt_identity()
        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid,ts)
                if sessionid is not None:
                    #print("session id not none")
                    questionInfo = text('SELECT ques, optiona, optionb, optionc, optiond FROM iclickerquestion WHERE sessionid = :sessionid')
                    response = db.engine.execute(questionInfo, sessionid=sessionid).fetchall()
                    updatets = text('UPDATE iclickerquestion SET readts = :ts WHERE sessionid = :sessionid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                    endTransaction()
                else:
                    #print("session id is none")
                    response = "[]"
                    endTransaction()
                    return response
            except psycopg2.Error:
                rollBack()
            else:
                break
        return json.dumps([dict(row) for row in response])

    @api.expect(post_iclickerquestion_model)
    @api.doc(body=post_iclickerquestion_model)
    def post(self):
        params = api.payload
        ques = params.pop("question")
        optiona = params.pop("optA")
        optionb = params.pop("optB")
        optionc = params.pop("optC")
        optiond = params.pop("optD")
        answer = params.pop("answer")
        sessionid = params.pop("sessionid")
        timelimit = params.pop("timelimit")
        while True:
            try:
                ts = startTransaction()
                #check if table si empty or not for iqid
                check_table_empty = text('SELECT * FROM iclickerquestion WHERE sessionid = :sessionid')
                table_entries = db.engine.execute(check_table_empty, sessionid=sessionid).fetchone()
                #update the timestamp
                updatets = text('UPDATE iclickerquestion SET readts = :ts WHERE sessionid = :sessionid')
                db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                if table_entries is None:
                    #table is empty
                    iqid = 1
                else:
                    get_latest_qid = text('SELECT MAX(iqid) FROM iclickerquestion WHERE sessionid = :sessionid')
                    latest_qid = db.engine.execute(get_latest_qid, sessionid=sessionid).scalar()
                    #update the timestamp
                    updatets = text('UPDATE iclickerquestion SET readts = :ts WHERE sessionid = :sessionid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                    iqid = latest_qid+1

                starttime = datetime.datetime.now()
                #timelimit is in minutes
                endtime = starttime + datetime.timedelta(minutes=timelimit)
                newQuestion = text('INSERT INTO iclickerquestion (iqid, ques, answer, optiona, optionb, optionc, optiond, sessionid, writets, starttime, endtime) VALUES (:iqid, :ques, :answer, :optiona, :optionb, :optionc, :optiond, :sessionid, :ts, :starttime, :endtime)')
                db.engine.execute(newQuestion, iqid=iqid, ques=ques, answer=answer, optiona=optiona, optionb=optionb, optionc=optionc, optiond=optiond, sessionid=sessionid, ts=ts, starttime=starttime, endtime=endtime)
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return "I-Clicker Question information has been updated successfully", 200


@re_api.route('/')
class StudentEnrollment(Resource):
    @jwt_required
    def get(self):
        netid = get_jwt_identity()
        global response
        while True:
            try:
                ts = startTransaction()
                enrollmentInfo = text('SELECT * FROM enrollment WHERE netid=:netid')
                response = db.engine.execute(enrollmentInfo, netid=netid).fetchall()
                updatets = text('UPDATE enrollment SET readts = :ts WHERE netid=:netid')
                db.engine.execute(updatets, ts=ts, netid=netid)
                if response is None:
                    response = "[]"
                    endTransaction()
                    return response
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return json.dumps([dict(row) for row in response])

    @api.expect(post_enrollment_model)
    @api.doc(body=post_enrollment_model)
    @jwt_required
    def post(self):
        params = api.payload
        netid = get_jwt_identity()
        course_number = params.pop("course_number")
        term = get_term()
        while True:
            try:
                ts = startTransaction()

                checkEnrollment = text('SELECT * FROM enrollment WHERE netid=:netid AND course_number=:course_number AND term=:term')
                alreadyEnrolled = db.engine.execute(checkEnrollment, netid=netid, course_number=course_number, term=term).fetchone()
                updatets = text('UPDATE enrollment SET readts = :ts WHERE netid=:netid AND course_number=:course_number AND term=:term')
                db.engine.execute(updatets, ts=ts, netid=netid, course_number=course_number, term=term)

                checkCourse = text('SELECT * FROM courses WHERE course_number=:course_number AND term=:term')
                courseExists = db.engine.execute(checkCourse, course_number=course_number, term=term).fetchone()
                updatets = text('UPDATE courses SET readts = :ts WHERE course_number=:course_number AND term=:term')
                db.engine.execute(updatets, ts=ts, course_number=course_number, term=term)

                if alreadyEnrolled is None and courseExists is not None:
                    newEnrollment = text('INSERT INTO enrollment (netid, course_number, term, grade, writets) VALUES (:netid, :course_number, :term, 0, :ts)')
                    db.engine.execute(newEnrollment, netid=netid, course_number=course_number, term=term, ts=ts)
                    # Sets piazza netid for this course only if it is null
                    updatePiazzaNetid = text('UPDATE courses SET piazza_netid=:netid, writets=:ts WHERE course_number=:course_number AND term=:term AND piazza_netid IS NULL')
                    db.engine.execute(updatePiazzaNetid, netid=netid, ts=ts, course_number=course_number, term=term)
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return "Enrollment information has been updated successfully", 200

@iclkres_api.route('/<iqid>')
class Iclickerresponseget(Resource):
    @jwt_required
    def get(self, iqid):  ###why do we have this?
        global response
        netid = get_jwt_identity()
        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid,ts)
                if sessionid is not None:
                    iclickerresponseInfo = text('SELECT * from iclickerresponse WHERE sessionid = :sessionid AND iqid = :iqid')
                    response = db.engine.execute(iclickerresponseInfo, sessionid=sessionid, iqid=iqid).fetchall()
                    updatets = text('UPDATE iclickerresponse SET readts = :ts WHERE sessionid = :sessionid AND iqid = :iqid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid, iqid=iqid)
                    endTransaction()
                else:
                    response = "[]"
                    endTransaction()
                    return response
            except psycopg2.Error:
                rollBack()
            else:
                break
        return json.dumps([dict(row) for row in response])

@iclkres_api.route('/')
class Iclickerresponseput(Resource):
    @api.expect(post_iclickerresponse_model)
    @api.doc(body=post_iclickerresponse_model)
    @jwt_required
    def post(self):
        params = api.payload
        netid = get_jwt_identity()
        response = params.pop("response")
        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid, ts)
                if sessionid is not None:
                    check_table_empty = text('SELECT * FROM iclickerresponse WHERE sessionid = :sessionid')
                    table_entries = db.engine.execute(check_table_empty, sessionid=sessionid).fetchone()
                    #update the timestamp
                    updatets = text('UPDATE iclickerresponse SET readts = :ts WHERE sessionid = :sessionid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                    if table_entries is None:
                        #table is empty
                        iqid = 1
                    else:
                        get_latest_qid = text('SELECT MAX(iqid) FROM iclickerresponse WHERE sessionid = :sessionid')
                        latest_qid = db.engine.execute(get_latest_qid, sessionid=sessionid).scalar()
                        #update the timestamp
                        updatets = text('UPDATE iclickerresponse SET readts = :ts WHERE sessionid = :sessionid')
                        db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                        iqid = latest_qid+1

                    responsetime = datetime.datetime.now()
                    newQuestion = text('INSERT INTO iclickerresponse (netid, sessionid, response, iqid, responsetime, writets) VALUES (:netid, :sessionid, :response, :iqid, :responsetime, :ts)')
                    db.engine.execute(newQuestion, netid=netid, sessionid=sessionid, response=response, iqid=iqid, responsetime=responsetime, ts=ts)
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return "I-Clicker Response information has been updated successfully", 200


@q_api.route('/')
class StudentQuestionPost(Resource):
    @jwt_required
    def get(self):
        netid = get_jwt_identity()
        global response
        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid,ts)
                if sessionid is not None:
                    questionInfo = text('SELECT * FROM student_question WHERE sessionid = :sessionid')
                    response = db.engine.execute(questionInfo, sessionid=sessionid).fetchall()
                    updatets = text('UPDATE student_question SET readts = :ts WHERE sessionid = :sessionid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                    endTransaction()
                else:
                    response = "[]"
                    endTransaction()
                    return response
            except psycopg2.Error:
                rollBack()
            else:
                break
        return json.dumps([dict(row) for row in response])

    @api.expect(post_question_model)
    @api.doc(body=post_question_model)
    @jwt_required
    def post(self):
        params = api.payload
        ques = params.pop("question")
        netid = get_jwt_identity()

        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid,ts)
                if sessionid is not None:
                    check_table_empty = text('SELECT * FROM student_question WHERE sessionid = :sessionid')
                    table_entries = db.engine.execute(check_table_empty, sessionid=sessionid).fetchone()
                    updatets = text('UPDATE student_question SET readts = :ts WHERE sessionid = :sessionid')
                    db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                    if table_entries is None:
                        #table is empty
                        qid = 1
                    else:
                        get_latest_qid = text('SELECT MAX(qid) FROM student_question WHERE sessionid = :sessionid')
                        latest_qid = db.engine.execute(get_latest_qid, sessionid=sessionid).scalar()
                        #update the timestamp
                        updatets = text('UPDATE student_question SET readts = :ts WHERE sessionid = :sessionid')
                        db.engine.execute(updatets, ts=ts, sessionid=sessionid)
                        qid = latest_qid+1

                    date_posted = datetime.datetime.now()
                    newQuestion = text('INSERT INTO student_question (qid, ques, sessionid, upvotes, date_posted, writets) VALUES (:qid, :ques, :sessionid, :upvotes, :date_posted, :ts)')
                    db.engine.execute(newQuestion, qid=qid, ques=ques, sessionid=sessionid, upvotes=0, date_posted=date_posted, ts=ts)
                endTransaction()

            except psycopg2.Error:
                rollBack()
            else:
                break
            return "Student Question has been updated successfully", 200

    @api.expect(delete_question_model)
    @api.doc(body=delete_question_model)
    @jwt_required
    #instructor_requrired
    def delete(self):
        params = api.payload
        qid = params.pop("qid")
        netid = get_jwt_identity()
        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid, ts)
                if sessionid is not None:
                    question_info_query = text('DELETE FROM student_question WHERE qid=:qid AND sessionid=:sessionid')
                    db.engine.execute(question_info_query, qid=qid, sessionid=sessionid)
                endTransaction()

            except psycopg2.Error:
                rollBack()

            else:
                break
            return "Deleted Question Successfully"

@q_api.route('/<qid>')
class UpvotesPost(Resource):
    #@api.doc(body=put_upvotes_model)
    @jwt_required
    def put(self, qid):
        netid = get_jwt_identity()
        qid = qid
        while True:
            try:
                ts = startTransaction()
                sessionid = get_sessionid_student(netid,ts)
                if sessionid is not None:
                    votesInfo = text('SELECT upvotes FROM student_question WHERE qid = :qid AND sessionid = :sessionid')
                    response = db.engine.execute(votesInfo, qid=qid, sessionid=sessionid).scalar()
                    updatets = text('UPDATE student_question SET readts = :ts WHERE qid = :qid AND sessionid = :sessionid')
                    db.engine.execute(updatets, ts=ts, qid=qid, sessionid=sessionid)
                    new_votes = 0
                    exists_query = text('SELECT netid FROM upvotes WHERE EXISTS (SELECT netid FROM upvotes WHERE netid = :netid AND qid = :qid AND sessionid = :sessionid)')
                    existing = db.engine.execute(exists_query, netid = netid, qid = qid, sessionid=sessionid).fetchall()
                    updatets = text('UPDATE upvotes SET readts = :ts WHERE EXISTS (SELECT netid FROM upvotes WHERE netid = :netid AND qid = :qid AND sessionid = :sessionid)')
                    db.engine.execute(updatets, ts=ts, netid=netid, qid=qid, sessionid=sessionid)
                    already_upvoted = (len(existing) > 0)
                    if (not already_upvoted):
                        new_votes = response + 1
                        newUpvote = text('INSERT INTO upvotes (netid, qid, sessionid, writets) VALUES (:netid, :qid, :sessionid, :ts)')
                        db.engine.execute(newUpvote, netid=netid, qid=qid, sessionid=sessionid, ts=ts)
                    else:
                        new_votes = response - 1
                        deleteUpvote = text('DELETE FROM upvotes WHERE netid = :netid AND qid = :qid AND sessionid = :sessionid')
                        db.engine.execute(deleteUpvote, netid = netid, qid=qid, sessionid=sessionid)

                    update_query = text('UPDATE student_question SET upvotes = :upvotes, writets=:ts  WHERE qid=:qid AND sessionid=:sessionid')
                    db.engine.execute(update_query, upvotes = new_votes, ts=ts, qid = qid, sessionid=sessionid)
                else:
                    response = "[]"
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break

@co_api.route('/<term>')
class Courses(Resource):
    @jwt_required
    def get(self, term):
        while True:
            try:
                ts = startTransaction()
                courseInfo = text('SELECT * FROM courses WHERE term=:term ORDER BY term')
                response = db.engine.execute(courseInfo, term=term).fetchall()
                updatets = text('UPDATE courses SET readts = :ts WHERE term=:term')
                db.engine.execute(updatets, ts=ts, term=term)
                if response is None:
                    response = "[]"
                    endTransaction()
                    return response
                endTransaction()
            except psycopg2.Error:
                rollBack()
            else:
                break
        return json.dumps([dict(row) for row in response])

@cd_api.route('/')
class CodingEnvironment(Resource):
    @api.expect(post_coding_model)
    @api.doc(body=post_coding_model)
    @jwt_required
    def post(self):
        params = api.payload
        code = params.pop('code')
        #netid = get_jwt_identity()


        dictToSend = {'code': code}
        url = 'http://coding:5002/run_code'
        res = requests.post(url, json=dictToSend)
        dictFromServer = res.json()
        return dictFromServer

if __name__ == '__main__':
    app.run(debug=True)

# models.py


from flask_sqlalchemy import SQLAlchemy
from config import BaseConfig

# from sqlalchemy import func, select, text
# app = Flask(__name__)
import datetime
from app import db
# db = SQLAlchemy(app)

class Session(db.Model):
    __tablename__ = 'session'

    sessionid = db.Column(db.String, primary_key=True)
    date = db.Column(db.String, nullable=False)
    # status = db.Column(db.String, nullable = False, default='Scheduled')
    course_number = db.Column(db.String, nullable=False)
    term  = db.Column(db.String, nullable=False)
    readts = db.Column(db.Integer, nullable=True, default = 0)
    writets = db.Column(db.Integer, nullable=True, default = 0)

    def __init__(self, sessionid, course_number, term, readts, writets):
        self.course_number = course_number
        '''change this later to be date time input by user!!!'''
        self.date = str(datetime.datetime.now().month)+"-"+str(datetime.datetime.now().day)
        self.sessionid = sessionid
        self.term = term
        # self.status = status
        self.readts = readts
        self.writets = writets

#refers to questions asked by students
class Question(db.Model):
    __tablename__ = 'student_question'

    qid = db.Column(db.Integer, primary_key = True)
    # netid = db.Column(db.String, nullable = False)
    sessionid = db.Column(db.String, db.ForeignKey('session.sessionid'), primary_key = True)
    ques = db.Column(db.String, nullable = True)
    upvotes = db.Column(db.Integer, nullable = False, default = 0)
    date_posted = db.Column(db.DateTime, nullable = True)
    readts = db.Column(db.Integer, nullable=True, default = 0)
    writets = db.Column(db.Integer, nullable=True, default = 0)

    def __init__(self, ques, upvotes, readts, writets):
        self.ques = ques
        # self.netid = netid
        self.sessionid = sessionid
        self.date_posted = datetime.datetime.now()
        self.upvotes = upvotes
        self.readts = readts
        self.writets = writets


class Upvotes(db.Model):
    __tablename__ = 'upvotes'

    netid = db.Column(db.String, primary_key = True)
    qid = db.Column(db.Integer, primary_key = True)
    sessionid = db.Column(db.String, db.ForeignKey('session.sessionid'), primary_key = True)
    readts = db.Column(db.Integer, nullable=True, default = 0)
    writets = db.Column(db.Integer, nullable=True, default = 0)

    def __init__(self, netid, qid, sessionid, readts, writets):
        self.netid = netid
        self.qid = qid
        self.sessionid = sessionid
        self.readts = readts
        self.writets = writets

class IClickerReponse(db.Model):
    __tablename__ = 'iclickerresponse'

    response = db.Column(db.Integer)
    netid = db.Column(db.String, primary_key=True)
    sessionid = db.Column(db.String, db.ForeignKey('session.sessionid'), primary_key=True)
    iqid = db.Column(db.Integer, primary_key=True)
    # studentreponse = db.Column(db.String, nullable = True)
    responsetime = db.Column(db.DateTime, nullable = False)
    readts = db.Column(db.Integer, nullable=True, default = 0)
    writets = db.Column(db.Integer, nullable=True, default = 0)

    def __init__(self, netid, sessionid, iqid, response, readts, writets):
        self.netid = netid
        self.sessionid = sessionid
        self.iqid = iqid
        # self.studentreponse = studentreponse
        self.responsetimes = datetime.datetime.now()
        self.readts = readts
        self.writets = writets

class Enrollment(db.Model):
    __tablename__ = 'enrollment'

    netid = db.Column(db.String, primary_key=True)
    course_number = db.Column(db.String, primary_key=True)
    term = db.Column(db.String, primary_key=True)
    grade = db.Column(db.Float, nullable = False, default = 0.0)
    readts = db.Column(db.Integer, nullable=True, default = 0)
    writets = db.Column(db.Integer, nullable=True, default = 0)

    def __init__(self, netid, course_number, grade, term, readts, writets):
        self.netid = netid
        self.course_number = course_number
        self.term = term
        self.readts = readts
        self.writets = writets
        self.grade = grade


class IClickerQuestion(db.Model):
    __tablename__ = 'iclickerquestion'

    iqid = db.Column(db.Integer, primary_key = True)
    ques = db.Column(db.String, nullable = False)
    optiona = db.Column(db.String, nullable = False)
    optionb = db.Column(db.String, nullable = False)
    optionc = db.Column(db.String, nullable = True)
    optiond = db.Column(db.String, nullable = True)
    answer = db.Column(db.String, nullable = False)
    #sessionId number between 1 - 41, total number of lecture in semester
    sessionid = db.Column(db.String, db.ForeignKey('session.sessionid'), primary_key = True)
    starttime = db.Column(db.DateTime, nullable = False)
    endtime = db.Column(db.DateTime, nullable=False)
    readts = db.Column(db.Integer, nullable=True, default = 0)
    writets = db.Column(db.Integer, nullable=True, default = 0)

    def __init__(self, ques, answer, optiona, sessionid, optionb, optionc, optiond, starttime, endtime, readts, writets):
        self.ques = ques
        self.optiona = optiona
        self.optionb = optionb
        self.optionc = optionc
        self.optiond = optiond
        self.answer = answer
        self.sessionid = sessionid
        self.starttime = starttime
        self.endtime = endtime
        self.readts = readts
        self.writets = writets

class Timestamp(db.Model):
    __tablename__ = 'timestamp'

    nextavailable = db.Column(db.Integer, primary_key = True, default = 0)

    def __init__(self, nextavailable):
        self.nextavailable = nextavailable

class TimestampTest(db.Model):
    __tablename__ = 'timestamptest'

    key = db.Column(db.Integer, primary_key = True)
    value = db.Column(db.String, nullable=True)
    readts = db.Column(db.Integer, nullable=True, default = 0)
    writets = db.Column(db.Integer, nullable=True, default = 0)

    def __init__(self, key, value, readts, writets):
        self.key = key
        self.value = value
        self.readts = readts
        self.writets = writets

# piazza.py


from piazza_api import Piazza
from io import StringIO
from app import logger
import datetime, sys

p = Piazza()

def piazzaLogin(netid, passwd=""):
    # return True
    try:
        p.user_login(netid+"@illinois.edu", passwd)
    except:
        return False
    return True

def piazzaMigration(unpackedQuestions, networkid, netid, passwd):
    if unpackedQuestions is None or not networkid or not netid or not passwd:
        logger.debug("piazzaMigration failure: one of the fields is empty")
        return

    try:
        # unpack question tuple
        questions = []
        for item in unpackedQuestions:
            questions.append(item[0])

        sys.stdout = mystdout = StringIO()
        for i, item in enumerate(questions,1):
            print(i, '. ' + item, sep='',end='\n')

        folders = ('project','other') # 'other')
        subject = 'Lecture Question Overflow: '+str(datetime.datetime.now().month)+'/'+str(datetime.datetime.now().day)
        content = mystdout.getvalue()

        logger.info("Posting to piazza this content:")
        logger.info(content)

        p.user_login(netid+"@illinois.edu", passwd)
        course = p.network(networkid)
        course.create_post('question', folders, subject, content, False, False, False)


        # test
        #p.user_login()
        #course = p.network("jvl5vt2p49j72t")
        #course.create_post('question', ('project', 'other'), 'IGNORE: wasted potentials piazza api test', "post body", False, False, False)
    except:
        logger.error("Piazza migration went wrong somewhere")
    finally:
        sys.stdout = sys.__stdout__

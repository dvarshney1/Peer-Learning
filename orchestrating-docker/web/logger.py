# logger.py


import logging

LOGGING = True
FILELOGGING = True

def loggerStart():
    gunicorn_error_handlers = logging.getLogger('gunicorn.error').handlers
    logger = logging.getLogger(__name__)
    if LOGGING:
        logger.handlers.extend(gunicorn_error_handlers)
    logger.setLevel(logging.DEBUG)
    if FILELOGGING:
        f_formatter = logging.Formatter('%(asctime)s - %(name)s %(levelname)s : %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        f_handler = logging.FileHandler('./logs/app.log')
        f_handler.setFormatter(f_formatter)
        if LOGGING:
            logger.addHandler(f_handler)
        logger.info("-------------------")
        logger.info("File logging is on.")
    else:
        c_formatter = logging.Formatter('%(name)s %(levelname)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
        c_handler = logging.StreamHandler()
        c_handler.setFormatter(c_formatter)
        if LOGGING:
            logger.addHandler(c_handler)
        logger.info("Console logging is on.")
    return logger

FROM python:3.7-slim

RUN apt-get update -y && \
    apt-get install -y python-pip python-dev

COPY PythonBuddy /PythonBuddy

WORKDIR /PythonBuddy

COPY ./PythonBuddy/requirements.txt /PythonBuddy/requirements.txt

EXPOSE 5000

RUN python -m pip install -r requirements.txt

CMD ["flask", "run", "--host=0.0.0.0"]

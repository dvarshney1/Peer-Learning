FROM python:3.7-slim

RUN python -m pip install --upgrade pip
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/requirements.txt
RUN python -m pip install -r requirements.txt

COPY . /code/
RUN mkdir -p /code/logs
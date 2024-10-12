FROM python:3.8-alpine

ENV PYTHONUNBUFFERED=1

RUN apk update && \
    apk add libffi-dev zlib-dev jpeg-dev postgresql-dev gcc python3-dev musl-dev

WORKDIR /weekend_chef_django

COPY requirements.txt requirements.txt

RUN pip3 install -r requirements.txt

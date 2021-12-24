# pull official base image
FROM python:3.9-alpine

# set work directory
WORKDIR /usr/src/app
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev libffi-dev
# build-essential
# libssl-dev

COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# copy project
COPY . .
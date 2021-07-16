FROM python:3.9-alpine

RUN ["pip", "install", "awscli", "boto3"]

WORKDIR /usr/src/app

COPY app.py .

CMD [ "python", "app.py" ]

FROM docker.io/python:3.12-slim

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

WORKDIR /fslc_stream

COPY ./schema.sql ./schema.sql
COPY ./fslc_stream/ ./fslc_stream

EXPOSE 5000

CMD gunicorn -w 4 -b '0.0.0.0:5000' -c '/etc/gunicorn.conf.py' 'fslc_stream.fslc_stream:app'

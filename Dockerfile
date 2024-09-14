FROM docker.io/python:3.12-slim

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY ./fslc_stream/ /fslc_stream

EXPOSE 5000

CMD gunicorn -w 4 -b '0.0.0.0:5000' 'fslc_stream.fslc_stream:app'

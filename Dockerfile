FROM python:3.11.8-slim
COPY . /opt/app
WORKDIR /opt/app
CMD python appendmail.py samples/

FROM python:3.10.4-slim-bullseye
COPY . /opt/app
WORKDIR /opt/app
CMD python appendmail.py samples/

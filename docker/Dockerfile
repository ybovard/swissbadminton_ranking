FROM python:alpine3.9
MAINTAINER Yves Bovard <can.github@bovard.family>

# Select entrypoint
WORKDIR /root/ranking

# Install code
COPY code/requirements.txt /root/ranking/requirements.txt
COPY code/ranking.py /root/ranking/ranking.py

# Environment
ENV TZ=Europe/Zurich

# Install dependencies and sources
RUN apk update && apk upgrade \
    && cd /root/ranking \
    && pip3 install --upgrade pip \
    && pip3 install -r /root/ranking/requirements.txt

ENTRYPOINT ["/usr/local/bin/python3", "/root/ranking/ranking.py"]
CMD ["--playerid=1234567"]

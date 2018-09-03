FROM alpine:latest
MAINTAINER Yves Bovard <ybovard@gmail.com>

# Select entrypoint
WORKDIR /root/ranking
CMD ["/usr/bin/python3.6", "ranking.py", "--url=$SWISSBADMINTON", "--players=$PLAYERLIST" ]

# Environment
ENV TZ=Europe/Zurich

COPY code/requirements.txt /root/ranking/requirements.txt
COPY code/ranking.py /root/ranking/ranking.py

# Install dependencies and sources
RUN echo "http://nl.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories \
    && apk update && apk upgrade \
    && apk add tzdata \
    && cp /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apk add python3-dev \
    && cd /root/ranking \
    && pip3.6 install --upgrade pip \
    && pip3.6 install -r /root/ranking/requirements.txt

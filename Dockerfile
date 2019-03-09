# Route 53 updater for DDNS-like home network access.
#
FROM alpine:latest
MAINTAINER Chris Barrett <chris@codesaru.com>

RUN apk --update add py2-pip \
	&& pip install awscli \
	&& rm -rf /var/cache/apk/*

#RUN rm -rf /etc/nginx/conf.d/*
#COPY nginx.conf /etc/nginx/nginx.conf
#COPY conf.d /etc/nginx/conf.d
COPY aws /root/.aws
COPY main.py /

#CMD ["/bin/sh"]  # for debugging
CMD [ "python", "./main.py" ]
#CMD cron && tail -f /var/log/cron.log


# Route 53 updater for DDNS-like home network access.
#
FROM alpine:latest
MAINTAINER Chris Barrett <chris@codesaru.com>

RUN apk --update add py2-pip \
	&& pip install awscli \
	&& rm -rf /var/cache/apk/*

RUN addgroup -S route53 \
    && adduser -G route53 -S -D route53
USER route53:route53

#COPY aws /root/.aws
COPY main.py /

#CMD ["/bin/sh"]  # for debugging
CMD [ "python", "./main.py" ]
#CMD cron && tail -f /var/log/cron.log


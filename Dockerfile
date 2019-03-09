# Route 53 updater for DDNS-like home network access.
#
FROM alpine:latest
MAINTAINER Chris Barrett <chris@codesaru.com>

RUN apk --update add py2-pip \
	&& pip install awscli \
	&& rm -rf /var/cache/apk/*

RUN groupadd -r route53 \
    && useradd --no-log-init -r -m -g route53 route53
USER route53:route53

#COPY aws /root/.aws
COPY main.py /home/route53/

RUN chmod -R o+rx /home/route53
#CMD ["/bin/sh"]  # for debugging
CMD [ "python", "./main.py" ]
#CMD cron && tail -f /var/log/cron.log


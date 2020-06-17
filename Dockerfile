# Route 53 updater for DDNS-like home network access.
#
FROM alpine:latest
MAINTAINER Chris Barrett <chris@codesaru.com>

RUN apk --update add py3-pip \
	&& pip install awscli \
        && pip install iplookup \
	&& rm -rf /var/cache/apk/*

RUN addgroup -S route53 \
    && adduser -G route53 -S -D route53
USER route53:route53

COPY main.py /

CMD [ "/usr/bin/python3", "-u", "/main.py" ]

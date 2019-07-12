# route53-updater-docker

Run this container to update a Route53 entry with your public IP address.  Think DuckDNS, but with Route53.

- If using locally, pay attention to the "credentials" and "Makefile" files.
- If using in unRaid, ignore those files.  The template will take everything in its variables.

Docker Hub: https://hub.docker.com/r/codesaru/route53-updater


## How to use

Built with UnraidOS in mind, but can be used elsewhere. Will just update a Route53 entry with your public IP, sleep 300 seconds, and repeat.

If running in UnraidOS, its template will take the variables in for you.

If running outside UnraidOS, use it this way:

```
docker run -d --rm \
    --env R53_HOSTED_ZONE_ID=A01BCD2EF3GHIJ \
    --env DNS_NAME=your.domain.com \
    --env AWS_SHARED_CREDENTIALS_FILE=/credentials \
    --mount type=bind,source=$(PWD)/credentials,destination=/credentials,readonly=true \
    --name route53-updater \
    codesaru/route53-updater
```

R53_HOSTED_ZONE_ID and DNS_NAME come from looking at your Route53 domain. The credentials file is an AWS credentials file, such as one that contains access key/secret pair. Be sure the user you're using via these credentials can interact with Route53, but also limit it to not have much more access than that.

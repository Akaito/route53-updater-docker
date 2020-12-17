build:
	@-sudo docker stop route53-updater
	@-sudo docker rm route53-updater
	@sudo docker build -t codesaru/route53-updater .

# To continually update DNS, create then "sudo crontab -e" to "docker start codesaru/route53-updater".
create:
	sudo docker create \
		--name=route53-updater \
		codesaru/route53-updater

run:
	sudo docker run -d --rm \
		--env R53_HOSTED_ZONE_ID=A01BCD2EF3GHIJ \
		--env='DNS_NAME=your.domain.com;*.your.domain.com' \
		--env AWS_SHARED_CREDENTIALS_FILE=/credentials \
		--mount type=bind,source=$(PWD)/credentials,destination=/credentials,readonly=true \
		--name route53-updater \
		codesaru/route53-updater

run-interactive:
	sudo docker run -ti --rm \
		--env R53_HOSTED_ZONE_ID=A01BCD2EF3GHIJ \
		--env='DNS_NAME=your.domain.com;*.your.domain.com' \
		--env AWS_SHARED_CREDENTIALS_FILE=/credentials \
		--mount type=bind,source=$(PWD)/credentials,destination=/credentials,readonly=true \
		--name route53-updater \
		codesaru/route53-updater

stop:
	@sudo docker stop route53-updater
	@sudo docker rm route53-updater

attach:
	@sudo docker exec -ti route53-updater sh


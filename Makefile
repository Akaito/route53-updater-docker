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
	@# -p format: host:container
	sudo docker run -d \
		--name route53-updater \
		codesaru/route53-updater

run-interactive:
	@# -p format: host:container
	sudo docker run -ti \
		--name route53-updater \
		codesaru/route53-updater

stop:
	@sudo docker stop route53-updater
	@sudo docker rm route53-updater

attach:
	@sudo docker exec -ti route53-updater sh


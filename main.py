#!/bin/env python3

from os import getenv
from sys import exit
import time
import requests
import socket
from datetime import datetime

import botocore
import botocore.session

from iplookup import iplookup


def logit(level, message):
    print(f'[{level.upper()}] {getdate()}: {message}')


def getdate():
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


# required env vars
R53_HOSTED_ZONE_ID = getenv('R53_HOSTED_ZONE_ID', None)
DNS_NAME = getenv('DNS_NAME', None)

# optional env vars
PUBLIC_IP_URL = getenv('PUBLIC_IP_URL', 'http://checkip.amazonaws.com')
TTL_SECONDS = int(getenv('TTL_SECONDS', '300'))
RETRY_SECONDS = TTL_SECONDS // 2


if not R53_HOSTED_ZONE_ID:
    logit("ERROR", "Route53's Hosted Zone ID should be set to env var R53_HOSTED_ZONE_ID.")
    exit(1)
if not DNS_NAME:
    logit("ERROR", "The DNS name to update A records for should be set to env var DNS_NAME.")
    exit(1)


# it's expected that you've volume-mounted a file with only the creds this container should use
session = botocore.session.get_session()
route53_client = session.create_client('route53')


def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True


def update_ip():
    logit("INFO", "IP Update Check Started")
    # Get current DNS IP
    ip = iplookup.iplookup
    current_ip = ip(DNS_NAME)[0]
    # get WAN IP
    r = requests.get(PUBLIC_IP_URL)
    public_ip = r.text.strip()
    if not r.status_code == 200:
        logit("WARN", f'Request to {PUBLIC_IP_URL} failed')
        return
    if not is_valid_ipv4_address(public_ip):
        logit("WARN", f'Failed to receive valid IP: {public_ip}')
        return

    logit("INFO", f'Current DNS IP:\t{current_ip}')
    logit("INFO", f'Current Public IP:\t{public_ip}')
    # See if they're different
    if public_ip == current_ip:
        logit("INFO", 'No IP Change Required')
        return
    logit("WARN", "Updating DNS...")

    # update Route 53
    response = route53_client.change_resource_record_sets(
        HostedZoneId=R53_HOSTED_ZONE_ID,
        ChangeBatch={
            'Comment': 'Update public IP address from Docker container.',
            'Changes': [
                {
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': str(DNS_NAME),
                        'Type': 'A',
                        'TTL': int(TTL_SECONDS),
                        'ResourceRecords': [
                            {'Value': public_ip}
                        ]
                    }
                }
            ]
        }
    )

    print(response['ChangeInfo']['Status'])


if __name__ == '__main__':
    update_ip()

    while getenv('KEEP_CONTAINER_ALIVE', 'True').lower() == 'true':
        logit("INFO", f'Sleeping for {TTL_SECONDS} seconds')
        time.sleep(int(TTL_SECONDS))
        update_ip()

#!/bin/env python3

import os
import time
import requests
import socket
from datetime import datetime

import botocore
import botocore.session

from iplookup import iplookup

# required env vars
R53_HOSTED_ZONE_ID = os.getenv('R53_HOSTED_ZONE_ID', None)
DNS_NAME = os.getenv('DNS_NAME', None)

# optional env vars
PUBLIC_IP_URL = os.getenv('PUBLIC_IP_URL', 'http://checkip.amazonaws.com')
TTL_SECONDS = int(os.getenv('TTL_SECONDS', '300'))
RETRY_SECONDS = TTL_SECONDS // 2


if not R53_HOSTED_ZONE_ID:
    logit("ERROR", "Route53's Hosted Zone ID should be set to env var R53_HOSTED_ZONE_ID.")
if not DNS_NAME:
    logit("ERROR", "The DNS name to update A records for should be set to env var DNS_NAME.")


# it's expected that you've volume-mounted a file with only the creds this container should use
session = botocore.session.get_session()
route53_client = session.create_client('route53')


def getdate():
    return datetime.now().strftime('%d/%m/%Y %H:%M:%S')


def logit(level, message):
    print(f'[{level.upper()}] {getdate()}: {message}')


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
    # Get current DNS IP
    ip = iplookup.iplookup
    current_ip = ip(DNS_NAME)[0]
    # get WAN IP
    r = requests.get(PUBLIC_IP_URL)
    public_ip = r.text.strip()
    if not r.status_code == 200:
        logit("WARN", f'Request to {PUBLIC_IP_URL} failed')
    if not is_valid_ipv4_address(public_ip):
        logit("WARN", f'Failed to receive valid IP: {public_ip}')

    logit("INFO", f'Current DNS IP:\t{current_ip}')
    logit("INFO", f'Current Public IP:\t{public_ip}')
    # See if they're different
    if public_ip == current_ip:
        logit("INFO", f'No IP Change, skipping...')
        return
    logit("INFO", "Updating DNS...")

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

    while os.getenv('KEEP_CONTAINER_ALIVE', 'False').lower() == 'true':
        time.sleep(int(TTL_SECONDS))
        update_ip()

#!/usr/bin/env python3

import logging
import os
import socket
import time
from datetime import datetime
from sys import exit

import boto3
import requests
from iplookup import iplookup


class Route53updater():
    def __init__(self, hostedZoneId, dnsName, publicIpUrl, ttl=30):
        """Class to check/update a Route53 A Record, based on an external IP lookup (eg. for Dynamic IPs on a home network)

        Args:
            hostedZoneId (string): AWS Route53 Hosted Zone ID
            dnsName (string): Domain (FQDN) to maintain in Route53
            publicIpUrl (string): Domain to use to check our current external IP
            ttl (int): TTL value to apply to the DNS record.
        """
        # it's expected that you've volume-mounted a file with only the creds this container should use
        self.route53_client = boto3.client('route53')
        self.hostedZoneId = hostedZoneId
        self.dnsName = dnsName
        self.publicIpUrl = publicIpUrl
        self.ttl = ttl

    def is_valid_ipv4_address(self, address):
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

    def update_ip(self):
        try:
            logging.info("IP Update Check Started")
            # Get current DNS A record (IP)
            ip = iplookup.iplookup
            try:
                current_ip = ip(self.dnsName)[0]
            except IndexError as err:
                logging.warning(f'Failed to lookup {self.dnsName} - assuming it doesn\'t exist yet, and continuing!')
                current_ip = "1.2.3.4"
            # get WAN IP
            r = requests.get(self.publicIpUrl)
            public_ip = r.text.strip()
            if not r.status_code == 200:
                logging.warning(f'Request to {self.publicIpUrl} failed')
                return
            if not self.is_valid_ipv4_address(public_ip):
                logging.warning(f'Failed to receive valid IP: {public_ip}')
                return

            logging.info(f'Current DNS IP:\t{current_ip}')
            logging.info(f'Current Public IP:\t{public_ip}')
            # See if they're different
            if public_ip == current_ip:
                logging.info('No IP Change Required')
                return
            logging.warning("Updating DNS...")

            # update Route 53
            response = self.route53_client.change_resource_record_sets(
                HostedZoneId=self.hostedZoneId,
                ChangeBatch={
                    'Comment': 'Update public IP address from Docker container.',
                    'Changes': [
                        {
                            'Action': 'UPSERT',
                            'ResourceRecordSet': {
                                'Name': str(self.dnsName),
                                'Type': 'A',
                                'TTL': int(self.ttl),
                                'ResourceRecords': [
                                    {'Value': public_ip}
                                ]
                            }
                        }
                    ]
                }
            )
        except Exception as err:
            # Catch all, so the container continues running/retrying if a failure occurs
            logging.error(f'An error occured whilst running the UpdateIP method:\n{err}')


if __name__ == '__main__':
    # Setup logging how we want it
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')

    # required env vars
    try:
        R53_HOSTED_ZONE_ID = os.environ['R53_HOSTED_ZONE_ID']
        DNS_NAME = os.environ['DNS_NAME']
    except KeyError as err:
        logging.error(f"Missing required variable: {err.args[0]}")
        exit(1)

    # optional env vars
    PUBLIC_IP_URL = os.getenv('PUBLIC_IP_URL', 'http://checkip.amazonaws.com')
    TTL_SECONDS = int(os.getenv('TTL_SECONDS', '300'))

    # Instantiate the class
    r53 = Route53updater(
        hostedZoneId=R53_HOSTED_ZONE_ID,
        dnsName=DNS_NAME,
        publicIpUrl=PUBLIC_IP_URL
    )

    # Run the updater (once)
    r53.update_ip()

    # If KEEP_CONTAINER_ALIVE, run periodically every TTL_SECONDS
    while os.getenv('KEEP_CONTAINER_ALIVE', 'True').lower() == 'true':
        logging.info(f'Sleeping for {TTL_SECONDS} seconds')
        time.sleep(TTL_SECONDS)
        r53.update_ip()

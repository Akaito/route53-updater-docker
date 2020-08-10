#!/usr/bin/env python3

import logging
import os
import socket
import time
from datetime import datetime
from sys import exit
import threading

import boto3
import requests


def get_ipv4(hostname):
    if hostname.startswith('*.'):
        # We want to be able to update a wildcard DNS record like
        # '*.example.com', but we can't lookup that record by hostname.  So
        # just do this as an easy 'good-enough' solution.
        hostname = hostname.replace('*', 'wildcard')
    return socket.gethostbyname(hostname)


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
            logging.info('IP Update Check Started')
            # Get current DNS A record (IP)
            try:
                current_ip = get_ipv4(self.dnsName)
            except:
                logging.warning("Failed to lookup {} - assuming it doesn't exist yet, and continuing!".format(self.dnsName))
                current_ip = 'UNKNOWN'
            # get WAN IP
            r = requests.get(self.publicIpUrl)
            public_ip = r.text.strip()
            if not r.status_code == 200:
                logging.warning('Request to {} failed'.format(self.publicIpUrl))
                return
            if not self.is_valid_ipv4_address(public_ip):
                logging.warning('Failed to receive valid IP: {}'.format(public_ip))
                return

            logging.info('Current DNS IP:\t{}'.format(current_ip))
            logging.info('Current Public IP:\t{}'.format(public_ip))
            # See if they're different
            if public_ip == current_ip:
                logging.info('No IP Change Required')
                return
            logging.warning('Updating DNS...')

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
            logging.error('An error occured whilst running the UpdateIP method:\n{}'.format(err))


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
        logging.error('Missing required variable: {}'.format(err.args[0]))
        exit(1)

    # optional env vars
    PUBLIC_IP_URL = os.getenv('PUBLIC_IP_URL', 'http://checkip.amazonaws.com')
    TTL_SECONDS = int(os.getenv('TTL_SECONDS', '300'))

    # Instantiate the class
    r53_updaters = []
    for dns_name in DNS_NAME.split(';'):
        r53_updaters.append(Route53updater(
            hostedZoneId=R53_HOSTED_ZONE_ID,
            dnsName=dns_name,
            publicIpUrl=PUBLIC_IP_URL
        ))

    def updater_thread_func (r53_updater):
        # Run the updater (once)
        r53_updater.update_ip()

        # If KEEP_CONTAINER_ALIVE, run periodically every TTL_SECONDS
        while os.getenv('KEEP_CONTAINER_ALIVE', 'True').lower() == 'true':
            logging.info('Sleeping for {} seconds'.format(TTL_SECONDS))
            time.sleep(TTL_SECONDS)
            r53_updater.update_ip()

    threads = [threading.Thread(target=updater_thread_func, args=(r53,)) for r53 in r53_updaters]
    # start running the updates
    logging.info('Starting {} updater threads.'.format(len(threads)))
    for thread in threads:
        thread.start()
    # quit once they're all done
    logging.info('Waiting for updater threads to complete.')
    for thread in threads:
        thread.join()


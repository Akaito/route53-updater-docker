#!/usr/bin/python

import os
import urllib

import botocore
import botocore.session

# required env vars
HOSTED_ZONE_ID = os.getenv('R53_HOSTED_ZONE_ID', None)  # TODO get config'd zone ID string (such as for codesaru.com)
DNS_NAME       = os.getenv('R53_DNS_NAME', None)  # TODO get from config (such as 'home.codesaru.com')

# optional env vars
PUBLIC_IP_URL = os.getenv('PUBLIC_IP_URL', 'http://checkip.amazonaws.com')
TTL_SECONDS   = os.getenv('R53_TTL_SECONDS', 300)


# it's expected that you've volume-mounted a file with only the creds this container should use
session = botocore.session.get_session()
route53_client = session.create_client('route53')


def update_ip():
    # get WAN IP
    f = urllib.urlopen(PUBLIC_IP_URL)
    assert f.getcode() == 200, 'Failed to get public IP'
    public_ip = f.read().strip()


    # update Route 53
    response = route53_client.change_resource_record_sets(
            HostedZoneId=HOSTED_ZONE_ID,
            ChangeBatch={
                'Comment': 'Update public IP address from Docker container.',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': DNS_NAME,
                            'Type': 'A',
                            'TTL': TTL_SECONDS,
                            'ResourceRecords': [
                                { 'Value': public_ip }
                            ]
                        }
                    },
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': '*.' + str(DNS_NAME),
                            'Type': 'A',
                            'TTL': TTL_SECONDS,
                            'ResourceRecords': [
                                { 'Value': public_ip }
                            ]
                        }
                    }
                ]})

    print(response['ChangeInfo']['Status'])


if __name__ == '__main__':
    update_ip()


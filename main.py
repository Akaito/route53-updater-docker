#!/usr/bin/python

import urllib

import botocore
import botocore.session


session = botocore.session.get_session()  # TODO get access key/secret (or profile name?)
route53_client = session.create_client('route53')

ttl = 300
HOSTED_ZONE_ID = None  # TODO get config'd zone ID string (such as for codesaru.com)
DNS_NAME = None  # TODO get from config (such as 'home.codesaru.com')


def update_ip():
    # get WAN IP
    f = urllib.urlopen('http://checkip.amazonaws.com')
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
                            'TTL': ttl,
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
                            'TTL': ttl,
                            'ResourceRecords': [
                                { 'Value': public_ip }
                            ]
                        }
                    }
                ]})

    print(response['ChangeInfo']['Status'])


if __name__ == '__main__':
    update_ip()


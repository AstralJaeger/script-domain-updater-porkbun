import os
import sys
import json
import socket
import requests

CREDENTIALS_FILE = 'credentials.json'
credentials = None

if not os.path.exists(CREDENTIALS_FILE):
    print('Could not locate credentials.json!')
    sys.exit(1)

with open(CREDENTIALS_FILE, 'r') as file:
    credentials = json.load(file)


def ping_porkbun():
    """Tests if connection to porkbun is successful"""
    response = requests.post('https://porkbun.com/api/json/v3/ping', json=credentials['registrar'])
    if response.status_code in [200, 201, 202]:
        print(f'> Status: {response.json()["status"]}')
        print(f'> IP: {response.json()["yourIp"]}')
    else:
        print('Error communicating with Porkbun! Please check your internet connection!')
        sys.exit(1)


def get_hostname() -> str:
    """Retrieves hostname for system"""
    return socket.gethostname().strip()


def get_ip():
    """Retrieves public IP address for system"""
    return requests.get('https://checkip.amazonaws.com/').text.strip()


def get_records(domain: str):
    """"Retrieves existing, registered subdomains"""
    response = requests.post(f'https://porkbun.com/api/json/v3/dns/retrieve/{domain}', json=credentials['registrar'])
    if response.status_code in [200, 201, 202]:
        return response.json()
    else:
        print('Error fetching domain information! Make sure domain API access is enabled!')
        sys.exit(1)


def update_record(domain, subdomain, response):
    """Updates an existing record"""
    body = {
        'apikey': credentials['registrar']['apikey'],
        'secretapikey': credentials['registrar']['secretapikey'],
        'content': response,
        'ttl': '600'
    }
    response = requests.post(f'https://porkbun.com/api/json/v3/dns/editByNameType/{domain}/A/{subdomain}', json=body)
    if response.status_code in [200, 201, 202] and response.json()['status'] == 'SUCCESS':
        print(f'> Updated: {subdomain}.{domain}')
    else:
        print(f'> Error updating: {subdomain}.{domain}')
        sys.exit(1)


def create_record(domain, subdomain, response):
    """Creates a new record"""
    body = {
        'apikey': credentials['registrar']['apikey'],
        'secretapikey': credentials['registrar']['secretapikey'],
        'name': subdomain,
        'type': 'A',
        'content': response,
        'ttl': '600'
    }

    response = requests.post(f'https://porkbun.com/api/json/v3/dns/create/{domain}', json=body)
    if response.status_code in [200, 201, 202] and response.json()['status'] == 'SUCCESS':
        print(f'> Created: {subdomain}.{domain}')
    else:
        print(f'> Error creating: {subdomain}.{domain}')
        print(f'> Status: {response.json()["status"]}')
        sys.exit(1)


def main():
    print(('=' * 5) + ' AstralJaeger\'s domain update tool')
    ping_porkbun()
    hostname = get_hostname()
    print(f'> Hostname: {hostname}')
    ip = get_ip()

    if len(sys.argv) != 2:
        print('Application requires exactly one argument!')
        sys.exit(1)

    domain = sys.argv[1]

    print(f'Found the following records for {domain}:')
    current_record = None
    records = get_records(domain)

    header = f' {"Index":>5s} | {"Id":>9s} | {"Name":>32s} | {"Type":>5s} | {"TTL":>3s} | {"Content":>16s}'
    print(header)
    print('-'*len(header))
    for index, record in enumerate(records['records'], 1):
        print(f' {index:>5d} | {record["id"]:>9s} | {record["name"]:>32s} | {record["type"]:>5s} | {record["ttl"]:>3s} | {record["content"]:>16s}')
        if record['type'] == 'A' and hostname in record['name'].split('.'):
            exists = True
            current_record = record
    print('-' * len(header))

    if current_record is not None:
        if ip == current_record['content']:
            print('IP on record already up to date!')
            print('Done.')
            sys.exit(0)

        print('Record already exists, updating existing record')
        update_record(domain, hostname, ip)

    else:
        print('Record does not exist, creating new record')
        create_record(domain, hostname, ip)

    print('Done.')
    sys.exit(0)


if __name__ == '__main__':
    main()

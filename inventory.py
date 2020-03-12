#!/usr/bin/env python
import requests
import urllib3
import json
import sys


def get_devices(session):
    '''Calls the D42 API and returns the entire JSON payload to parse in the device_parser function'''
    get = session.get('https://your_d42_server.com/api/1.0/devices/all/')
    if get.status_code == requests.codes.ok:
        data = get.json()
        return data
    else:
        sys.exit()


def custom_fields_parser(data, string):
    '''Requires a list of dictionaries and a string to match the key required to get the value
        The value from the key "key" will match the string and then return the value from the key "value"
        Example:
        custom_fields:[{"key": "Environment","value": "Production"},{"key": "AvailabilityZone","value": "z3"}]'''

    for d in data:
        if d['key'] == string:
            try:
                value = d['value'].lower()
            except:
                value = d['value']

    return value


def ip_parser(data):
    '''Loops through ip_addresses list from device42 and looks for the label "management". This field is mandatory in D42 so no additional conditional checks are required. '''
    if len(data) == 0:
        ip = None
    else:
        for i in data:
            if i['label'] == 'management':
                ip = i['ip']

    return ip


def all_inventory(inventory, name):
    '''Requires the inventory dictionary as well as the name var created in device_parser. 
    Creates the all group structure which contains all hosts, will be merged into original inventory dictionary'''

    if 'all' in inventory:
        if 'hosts' in inventory['all']:
            inventory['all']['hosts'].append(name)
        else:
            inventory['all'] = {}
            inventory['all']['hosts'] = []
            inventory['all']['hosts'].append(name)
    else:
        inventory['all'] = {}
        inventory['all']['hosts'] = []
        inventory['all']['hosts'].append(name)

    return inventory


def os_inventory(inventory, name, os):
    '''Requires the inventory dictionary as well as the os var created in device_parser. 
    Creates the OS group structure which contains all hosts belonging to a certain OS (NXOS, F5)'''

    if os in inventory:
        if 'hosts' in inventory[os]:
            inventory[os]['hosts'].append(name)
        else:
            inventory[os] = {}
            inventory[os]['hosts'] = []
            inventory[os]['hosts'].append(name)
    else:
        inventory[os] = {}
        inventory[os]['hosts'] = []
        inventory[os]['hosts'].append(name)

    return inventory


def zone_inventory(inventory, site, name, zone):
    '''Requires the inventory dictionary as well as the site, name and zone vars created in device_parser. 
    Creates the Zone group structure which contains all hosts belonging to a certain Zone (Z0, Z1, etc)'''

    if zone in inventory[site]:
        if 'hosts' in inventory[site][zone]:
            inventory[site][zone]['hosts'].append(name)
        else:
            inventory[site][zone] = {}
            inventory[site][zone]['hosts'] = []
            inventory[site][zone]['hosts'].append(name)
    else:
        inventory[site][zone] = {}
        inventory[site][zone]['hosts'] = []
        inventory[site][zone]['hosts'].append(name)

    return inventory


def site_inventory(inventory, name, site):
    '''Requires the inventory dictionary, the name variable and the site variable created in device_parser. 
    Creates the Site(S1,S2,D1) group structure, will be merged into original inventory dictionary'''

    if site in inventory:
        if 'hosts' in inventory[site]:
            inventory[site]['hosts'].append(name)
        else:
            inventory[site]['hosts'] = []
            inventory[site]['hosts'].append(name)
    else:
        inventory[site] = {}
        inventory[site]['hosts'] = []
        inventory[site]['hosts'].append(name)

    return inventory


def meta_inventory(inventory, name, hostvars):
    '''Requires the inventory dictionary, the name variable and the hostvars dictionary created in device_parser. 
    Creates the host variables structure, will be merged into original inventory dictionary'''

    if '_meta' in inventory:
        if 'hostvars' in inventory['_meta']:
            inventory['_meta']['hostvars'][name] = hostvars
        else:
            inventory['_meta']['hostvars'] = {}
            inventory['_meta']['hostvars'][name] = hostvars
    else:
        inventory['_meta'] = {}
        inventory['_meta']['hostvars'] = {}

        inventory['_meta']['hostvars'][name] = hostvars

    return inventory


def device_parser(data):
    '''Master function to parse data, will call various other functions to parse the data returned from the D42 API'''

    inventory = {}
    for device in data['Devices']:
        try:
            ip = ip_parser(device['ip_addresses'])

            # Calls the custom_fields_parser function to loop through dictionaries.
            custom_fields = device['custom_fields']
            zone = custom_fields_parser(custom_fields, 'AvailabilityZone')
            environment = custom_fields_parser(custom_fields, 'Environment')
            subdomain = custom_fields_parser(custom_fields, 'SubDomain')
            physical_name = custom_fields_parser(custom_fields, 'PhysicalName')
            peer_node = custom_fields_parser(custom_fields, 'PeerNode')

            # This is in device42 building name property = site
            site = device['building'].lower()
            name = device['name'].lower()
            # Ansible doesn't differentiate between IOS and IOS-XE so we convert the OS type to ios for ASR routers
            if device['os'] == 'ios-xe' and 'asr' in device['hw_model'].lower():
                os = 'ios'
            else:
                os = device['os']
            vendor = device['manufacturer'].lower()
            model_number = device['hw_model'].lower()
            serial_number = device['serial_no']
        except KeyError:
            pass

        # This will build the top level site-specific group
        site_inv = site_inventory(inventory, name, site)
        inventory.update(site_inv)

        # Ansible requires all hosts be included in the "all" group
        all_inv = all_inventory(inventory, name)
        inventory.update(all_inv)

        # Create OS specific group structure
        os_inv = os_inventory(inventory, name, os)
        inventory.update(os_inv)

        # Create Zone specific group structure
        zone_inv = zone_inventory(inventory, site, name, zone)
        inventory.update(zone_inv)

        # Meta is for grouping host variables for Ansible
        host_vars = {'ansible_host': ip, 'ansible_network_os': os,'subdomain': subdomain, 
                     'environment': environment, 'zone': zone, 'model_number': model_number, 'serial_number': serial_number, 
                     'vendor': vendor, 'physical_name': physical_name, 'peer_node': peer_node, 'site': site}
        
        meta_inv = meta_inventory(inventory, name, host_vars)
        inventory.update(meta_inv)

    return json.dumps(inventory, indent=3)


def main():
    urllib3.disable_warnings()
    session = requests.session()
    session.auth = ('user', 'vault_password')
    session.verify = False #Change this once cert is installed or if external!
    session.headers = {'Content-Type': 'application/json',
                       'Accept': 'application/json'}
    data = get_devices(session)
    inventory = device_parser(data)
    print(inventory)


if __name__ == "__main__":
    main()

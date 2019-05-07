#!/usr/bin/python
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_system

short_description: This module sets system settings on an NFVIS host

version_added: "n/a"

description:
    - "This module sets system settings on an NFVIS host"

options:
    hostname:
        description:
            - The hostname of the NFVIS host
        required: false
    trusted_source:
        description:
            - A list of trusted sources in CIDR notation
        required: false

author:
    - Steven Carter
'''

EXAMPLES = '''
# Pass in a message
- name: Test with a message
  my_new_test_module:
    name: hello world

# pass in a message and have changed true
- name: Test with a message and changed output
  my_new_test_module:
    name: hello world
    new: true

# fail the module
- name: Test failure of the module
  my_new_test_module:
    name: fail me
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils._text import to_native
from ansible.module_utils.nfvis import nfvisModule, nfvis_argument_spec

try:
    import netaddr
    HAS_NETADDR = True
except:
    HAS_NETADDR = False


def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = nfvis_argument_spec()
    argument_spec.update(hostname=dict(type='str', required=True),
                         trusted_source=dict(type='list'),
                         dpdk=dict(type='bool'),
                         mgmt=dict(type='str', required=True),
                         default_gw=dict(type='str')
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
    )
    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )

    if not HAS_NETADDR:
        module.fail_json(msg='Could not import the python library netaddr required by this module')

    nfvis = nfvisModule(module)



    payload = None
    port = None
    nfvis.result['changed'] = False
    # Make sure that we have a righteous mgmt IP address
    try:
        mgmt_ip = netaddr.IPNetwork(nfvis.params['mgmt'])
    except ValueError:
        module.fail_json(msg="mgmt address/netmask is invalid: {0}".format(nfvis.params['mgmt']))

    # Get the list of existing vlans
    response = nfvis.request('/config/system/settings')
    nfvis.result['current'] = response
    nfvis.result['what_changed'] = []

    payload = {'settings':response['system:settings']}
    if nfvis.params['hostname'] and nfvis.params['hostname'].split('.')[0] != payload['settings']['hostname']:
        payload['settings']['hostname'] = nfvis.params['hostname'].split('.')[0]
        nfvis.result['what_changed'].append('hostname')
    if nfvis.params['trusted_source'] and (('trusted-source' in payload['settings'] and nfvis.params['trusted_source'] != payload['settings']['trusted-source']) or ('trusted-source' not in payload['settings'])):
        payload['settings']['trusted-source'] = nfvis.params['trusted_source']
        nfvis.result['what_changed'].append('trusted_source')
    if nfvis.params['dpdk'] and (('dpdk' in payload['settings'] and nfvis.params['dpdk'] != payload['settings']['dpdk']) or ('dpdk' not in payload['settings'])):
        payload['settings']['dpdk'] = ['disable', 'enable'][nfvis.params['dpdk'] == True]
        nfvis.result['what_changed'].append('dpdk')
    if 'mgmt' in payload['settings']:
        if nfvis.params['mgmt'] == 'dhcp' and 'dhcp' not in payload['settings']['mgmt']:
            payload['settings']['mgmt']['dhcp'] = None
            nfvis.result['what_changed'].append('mgmt')
        else:
            if 'address' not in payload['settings']['mgmt']['ip'] or payload['settings']['mgmt']['ip']['address'] != str(mgmt_ip.ip) or 'netmask' not in payload['settings']['mgmt']['ip'] or payload['settings']['mgmt']['ip']['netmask'] != str(mgmt_ip.netmask):
                payload['settings']['mgmt']['ip'] = {'address': str(mgmt_ip.ip), 'netmask': str(mgmt_ip.netmask)}
                nfvis.result['what_changed'].append('mgmt')
    else:
            payload['settings']['mgmt'] = {}
            payload['settings']['mgmt']['ip'] = {'address': str(mgmt_ip.ip), 'netmask': str(mgmt_ip.netmask)}
            nfvis.result['what_changed'].append('mgmt')
    if nfvis.params['default_gw'] and nfvis.params['default_gw'] != payload['settings']['default-gw']:
        payload['settings']['default-gw'] = nfvis.params['default_gw']
        nfvis.result['what_changed'].append('default_gw')
    if nfvis.result['what_changed']:
        nfvis.result['changed'] = True
        url_path = '/config/system/settings'
        if not module.check_mode:
            response = nfvis.request(url_path, method='PUT', payload=json.dumps(payload))

    nfvis.exit_json(**nfvis.result)


if __name__ == '__main__':
    main()
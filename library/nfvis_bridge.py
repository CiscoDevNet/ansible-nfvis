#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_bridge

short_description: Configure bridges in an NFVIS host

version_added: "n/a"

description:
    - "Configure bridges in an NFVIS host"

options:
    name:
        description:
            - Name of the bridge
        required: true
    state:
        description:
            - The state if the bridge ('present' or 'absent') (Default: 'present')
        required: false
    ports:
        description:
            - List of ports to which the bridge is attached
    ip:
        description:
            - IP address and netmask of the bridge
    vlan:
        description:
            - VLAN tag
    dhcp:
        description:
            - Flag to specify DHCP configuration

author:
    - Steven Carter
'''

EXAMPLES = '''
# Create a service chain bridge
- nfvis_bridge:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: service-br
    state: present

# Create a service chain bridge
- nfvis_bridge:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: service-br
    state: absent
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

def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = nfvis_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         name=dict(type='str', aliases=['bridge']),
                         ports=dict(type='list'),
                         ip=dict(type='list'),
                         vlan=dict(type='int'),
                         purge=dict(type='bool', default=False),
                         dhcp=dict(type='bool')
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
    nfvis = nfvisModule(module, function='bridge')

    payload = None
    port = None
    nfvis.result['changed'] = False

    # Get the list of existing bridges
    url = 'https://{0}/api/config/bridges?deep'.format(nfvis.params['host'])
    response = nfvis.request(url, method='GET')
    nfvis.result['data'] = response
    
    # Turn the list of dictionaries returned in the call into a dictionary of dictionaries hashed by the bridge name
    bridge_dict = {}
    try:
        for item in response['network:bridges']['bridge']:
            name = item['name']
            bridge_dict[name] = item
        nfvis.result['debug'] = bridge_dict
    except TypeError:
        pass
    except KeyError:
        pass

    if nfvis.params['state'] == 'present':

        if nfvis.params['name'] not in bridge_dict or nfvis.params['purge'] == True:
            # If the
            # Construct the payload
            payload = {'bridge': {}}
            payload['bridge']['name'] = nfvis.params['name']

            if nfvis.params['dhcp'] == True:
                payload['bridge']['dhcp'] = [ None ]

            payload['bridge']['port'] = []
            if nfvis.params['ports']:
                for port in nfvis.params['ports']:
                    payload['bridge']['port'].append( {'name': port} )

            payload['bridge']['vlan'] = None
            if nfvis.params['vlan']:
                payload['bridge']['vlan'] = nfvis.params['vlan']

            if nfvis.params['ip']:
                payload['bridge']['ip'] = {}
                if 'address' in nfvis.params['ip']:
                    payload['bridge']['ip']['address'] = nfvis.params['ip']['address']
                else:
                    module.fail_json(msg="address must be specified for ip")
                if 'netmask' in nfvis.params['ip']:
                    payload['bridge']['ip']['netmask'] = nfvis.params['ip']['netmask']
                else:
                    module.fail_json(msg="netmask must be specified for ip")


            if nfvis.params['name'] in bridge_dict:
                # We are overwritting (purging) what is on the NFVIS host
                url = 'https://{0}/api/config/bridges/bridge/{1}'.format(nfvis.params['host'], nfvis.params['name'])
                response = nfvis.request(url, method='PUT', payload=json.dumps(payload))
            else:
                url = 'https://{0}/api/config/bridges'.format(nfvis.params['host'])
                response = nfvis.request(url, method='POST', payload=json.dumps(payload))

            nfvis.result['changed'] = True
        else:
            # The bridge exists on the device, so let's start with the original payload and see if anything changed
            payload = {'bridge': bridge_dict[nfvis.params['name']]}

            if nfvis.params['ports']:
                # Check ports
                if 'port' not in payload['bridge']:
                    payload['bridge']['port'] = []
                    # No ports are on the NFVIS host, so add them all
                    for port in nfvis.params['ports']:
                        payload['bridge']['port'].append({'name': port})
                    nfvis.result['changed'] = True
                else:
                    # Add the ports that are not already on the NFVIS host
                    existing_ports = []
                    for item in payload['bridge']['port']:
                        existing_ports.append(item['name'])
                    for port in nfvis.params['ports']:
                        if port not in existing_ports:
                            payload['bridge']['port'].append({'name': port})
                            nfvis.result['changed'] = True

            if nfvis.params['vlan']:
                if 'vlan' not in payload['bridge'] or nfvis.params['vlan'] != payload['bridge']['vlan']:
                    payload['bridge']['vlan'] = nfvis.params['vlan']
                    nfvis.result['changed'] = True

            if nfvis.params['dhcp']:
                if nfvis.params['dhcp'] == True and 'dhcp' not in payload['bridge']:
                    payload['bridge']['dhcp'] = [ nfvis.params['dhcp'] ]
                    nfvis.result['changed'] = True
                elif nfvis.params['dhcp'] == False and 'dhcp' in payload['bridge']:
                    payload['bridge']['dhcp'] = None
                    nfvis.result['changed'] = True

            if nfvis.params['ip']:
                if 'ip' not in payload['bridge']:
                    # No ip on the NFVIS host, so add the entire dict
                    payload['bridge']['ip'] = nfvis.params['ip']
                    nfvis.result['changed'] = True
                else:
                    if 'address' in nfvis.params['ip']:
                        if payload['bridge']['ip']['address'] != nfvis.params['ip']['address']:
                            payload['bridge']['ip']['address'] = nfvis.params['ip']['address']
                            nfvis.result['changed'] = True
                    else:
                        module.fail_json(msg="address must be specified for ip")

                    if 'netmask' in nfvis.params['ip']:
                        if payload['bridge']['ip']['netmask'] != nfvis.params['ip']['netmask']:
                            payload['bridge']['ip']['netmask'] = nfvis.params['ip']['netmask']
                            nfvis.result['changed'] = True
                    else:
                        module.fail_json(msg="netmask must be specified for ip")

            if nfvis.result['changed'] == True:
                url = 'https://{0}/api/config/bridges/bridge/{1}'.format(nfvis.params['host'], nfvis.params['name'])
                response = nfvis.request(url, method='PUT', payload=json.dumps(payload))

    else:
        if nfvis.params['name'] in bridge_dict:
            url = 'https://{0}/api/config/bridges/bridge/{1}'.format(nfvis.params['host'], nfvis.params['name'])
            response = nfvis.request(url, 'DELETE')
            nfvis.result['changed'] = True


    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with nfvis so they can implement a check mode
    if module.check_mode:
        nfvis.exit_json(**nfvis.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    nfvis.exit_json(**nfvis.result)


if __name__ == '__main__':
    main()
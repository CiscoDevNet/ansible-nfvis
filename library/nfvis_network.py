#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_network

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - Name of the network
        required: true
    state:
        description:
            - The state if the network ('present' or 'absent')
        required: false
    bridge:
        description:
            - Name of the bridge to which the network is attached 
        required: false
    trunk:
        description:
            - Set network to trunk mode
        required: false
    sriov:
        description:
            - SR-IOV supported on the network
        required: false
    native_tagged:
        description:
            - Specifies if the netowrk is tagged or not
        required: false
    native_vlan:
        description:
            - Specifies a native VLAN. It sets the native characteristics when the interface is in trunk mode. If you do not configure a native VLAN, the default VLAN 1 is used as the native VLAN
        required: false
    vlan:
        description:
            - Specifies the VLAN ID when the network is in access mode (i.e NOT a trunk)
        required: false
        

author:
    - Steven Carter
'''

EXAMPLES = '''
# Create a network in access mode with VLAN ID
- nfvis_network:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: new-network
    bridge: net-bridge
    trunk: no
    vlan: 100
    state: present

# Delete a network
- nfvis_network:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: new-network
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
                         name=dict(type='str', required=True, aliases=['network']),
                         bridge=dict(type='str', required=True),
                         trunk=dict(type='bool', default=True),
                         sriov=dict(type='bool', default=False),
                         native_tagged=dict(type='bool'),
                         native_vlan=dict(type='str'),
                         vlan=dict(type='str'),
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
    nfvis = nfvisModule(module, function='network')

    payload = None
    port = None
    nfvis.result['changed'] = False

    # Get the list of existing networks
    url_path = '/config/networks?deep'
    response = nfvis.request(url_path, method='GET')
    nfvis.result['current'] = response
    nfvis.result['what_changed'] = []
    
    # Turn the list of dictionaries returned in the call into a dictionary of dictionaries hashed by the network name
    network_dict = {}
    try:
        for item in response['network:networks']['network']:
            name = item['name']
            network_dict[name] = item
        # nfvis.result['debug'] = network_dict
    except TypeError:
        pass
    except KeyError:
        pass

    if nfvis.params['state'] == 'present':

        if nfvis.params['name'] not in network_dict:

            # Construct the payload
            payload = {'network': {}}
            payload['network']['name'] = nfvis.params['name']
            payload['network']['bridge'] = nfvis.params['bridge']
            if nfvis.params['trunk'] == False:
                payload['network']['trunk'] = nfvis.params['trunk']
                if nfvis.params['vlan']:
                    payload['network']['vlan'] = nfvis.params['vlan']

            if nfvis.params['sriov']:
                payload['network']['sriov'] = nfvis.params['sriov']
            if nfvis.params['native_vlan']:
                payload['network']['native-vlan'] = nfvis.params['native_vlan']

            # The network does not exist on the device, so add it
            url_path = '/config/networks'
            response = nfvis.request(url_path, method='POST', payload=json.dumps(payload))
            nfvis.result['changed'] = True

        else:
            # The bridge exists on the device, so let's start with the original payload and see if anything changed
            payload = {'network': network_dict[nfvis.params['name']]}

            if payload['network']['bridge'] != nfvis.params['bridge']:
                payload['network']['bridge'] = nfvis.params['bridge']
                nfvis.result['what_changed'].append('bridge')

            if nfvis.params['trunk'] == False:
                if 'trunk' not in payload['network'] or payload['network']['trunk'] == True:
                    payload['network']['trunk'] = False
                    nfvis.result['what_changed'].append('trunk')
                if nfvis.params['vlan']:
                    if 'vlan' not in payload['network'] or nfvis.params['vlan'] not in payload['network']['vlan']:
                        payload['network']['vlan'] = nfvis.params['vlan']
                        nfvis.result['what_changed'].append('vlan')

            if nfvis.params['sriov']:
                if 'sriov' not in payload['network'] or nfvis.params['sriov'] != payload['network']['sriov']:
                    payload['network']['sriov'] = nfvis.params['sriov']
                    nfvis.result['what_changed'].append('sriov')

            if nfvis.params['native_tagged']:
                if 'native_tagged' not in payload['network'] or nfvis.params['native_tagged'] != payload['network']['native_tagged']:
                    payload['network']['native_tagged'] = nfvis.params['native_tagged']
                    nfvis.result['what_changed'].append('native_tagged')

            if nfvis.params['native_vlan']:
                if 'native_vlan' not in payload['network'] or nfvis.params['native_vlan'] != payload['network']['native_vlan']:
                    payload['network']['native_vlan'] = nfvis.params['native_vlan']
                    nfvis.result['what_changed'].append('native_vlan')

            if nfvis.result['what_changed']:
                url_path = '/config/networks/network/{0}'.format(nfvis.params['name'])
                nfvis.result['changed'] = True
                if not module.check_mode:
                    response = nfvis.request(url_path, method='PUT', payload=json.dumps(payload))

    else:
        if nfvis.params['name'] in network_dict:
            url_path = '/config/networks/network/{0}'.format(nfvis.params['name'])
            nfvis.result['changed'] = True
            if not module.check_mode:
                response = nfvis.request(url_path, 'DELETE')

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    nfvis.exit_json(**nfvis.result)


if __name__ == '__main__':
    main()
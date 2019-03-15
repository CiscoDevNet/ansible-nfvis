#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_upload

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - This is the message to send to the sample module
        required: true
    new:
        description:
            - Control to demo if the result of this module is changed or not
        required: false

extends_documentation_fragment:
    - azure

author:
    - Your Name (@yourhandle)
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

def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = nfvis_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         name=dict(type='str', aliases=['network']),
                         bridge=dict(type='str', required=True),
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
    url = 'https://{0}/api/config/networks?deep'.format(nfvis.params['host'])
    response = nfvis.request(url, method='GET')
    nfvis.result['data'] = response
    
    # Turn the list of dictionaries returned in the call into a dictionary of dictionaries hashed by the network name
    network_dict = {}
    try:
        for item in response['network:networks']['network']:
            name = item['name']
            network_dict[name] = item
        nfvis.result['debug'] = network_dict
    except TypeError:
        pass
    except KeyError:
        pass

    if nfvis.params['state'] == 'present':
        # Construct the payload
        payload = {'network':{}}
        payload['network']['name'] = nfvis.params['name']
        payload['network']['bridge'] = nfvis.params['bridge']

        if nfvis.params['name'] in network_dict:
            # The network exists on the device, so check to see if it is the same configuration
            network_entry = network_dict[nfvis.params['name']]
            nfvis.result['debug'] = network_entry
            # Check to see if the ports are different
            if nfvis.params['bridge'] != network_entry['bridge']:
                url = 'https://{0}/api/config/networks/network/{1}'.format(nfvis.params['host'], nfvis.params['name'])
                response = nfvis.request(url, method='PUT', payload=json.dumps(payload))
                nfvis.result['changed'] = True
        else:
            # The network does not exist on the device, so add it
            url = 'https://{0}/api/config/networks'.format(nfvis.params['host'])
            response = nfvis.request(url, method='POST', payload=json.dumps(payload))
            nfvis.result['changed'] = True
    else:
        if nfvis.params['name'] in network_dict:
            url = 'https://{0}/api/config/networks/network/{1}'.format(nfvis.params['host'], nfvis.params['name'])
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
#!/usr/bin/python

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

def main():
    # define the available arguments/parameters that a user can pass to
    # the module

    argument_spec = nfvis_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         hostname=dict(type='str'),
                         trusted_source=dict(type='list')
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
    nfvis = nfvisModule(module, function='system')

    payload = None
    port = None
    nfvis.result['changed'] = False

    # Get the list of existing vlans
    url_path = '/config/system/settings'
    response = nfvis.request(url_path, method='GET')
    nfvis.result['data'] = response

    if nfvis.params['state'] == 'present':
        payload = {'settings':response['system:settings']}
        if nfvis.params['hostname'] and nfvis.params['hostname'] != payload['settings']['hostname']:
            payload['settings']['hostname'] = nfvis.params['hostname']
            nfvis.result['changed'] = True
        if nfvis.params['trusted_source'] and (('trusted-source' in payload['settings'] and nfvis.params['trusted_source'] != payload['settings']['trusted-source']) or ('trusted-source' not in payload['settings'])):
            payload['settings']['trusted-source'] = nfvis.params['trusted_source']
            nfvis.result['changed'] = True
        if nfvis.result['changed'] == True:
            url_path = '/config/system/settings'
            response = nfvis.request(url_path, method='PUT', payload=json.dumps(payload))


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
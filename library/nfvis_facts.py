#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_vlan

short_description: This is my sample module

version_added: "2.4"

description:
    - "Create a VLAN on an NFVIS host"

options:
    vlan_id:
        description:
            - The VLAN ID of the VLAN.
        required: true
    state:
        description:
            - The state of the VLAN (i.e. `present` or `absent`)
        required: false

author:
    - Your Name (@yourhandle)
'''

EXAMPLES = '''
# Create VLAN 10
- nfvis_vlan:
    host: 1.2.3.4
    user: admin
    password: cisco
    state: present
    vlan_id: 100

# Delete VLAN 10
- nfvis_vlan:
    host: 1.2.3.4
    user: admin
    password: cisco
    state: absent
    vlan_id: 100
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
    # argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
    #                      vlan_id=dict(type='int', required=True))

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
                           supports_check_mode=True)
    nfvis = nfvisModule(module)

    payload = None

    # Get the platform details
    response = nfvis.request('/operational/platform-detail')
    if 'platform_info:platform-detail' in response:
        nfvis.result['platform-detail'] = response['platform_info:platform-detail']
    else:
        nfvis.result['platform-detail'] = []

        # Get CPU allocation information
    response = nfvis.request('/operational/resources/cpu-info/allocation')
    if 'resources:allocation' in response:
        nfvis.result['cpu-info'] = response['resources:allocation']
    else:
        nfvis.result['cpu-info'] = []

        # Get deployment information
    response = nfvis.request('/config/vm_lifecycle/tenants/tenant/admin/deployments?deep')
    if isinstance(response, dict) and 'vmlc:deployments' in response:
        nfvis.result['deployments'] = response['vmlc:deployments']
    else:
        nfvis.result['deployments'] = []

        # Get the bridge information
    response = nfvis.request('/config/bridges?deep')
    if 'network:bridges' in response:
        nfvis.result['bridges'] = response['network:bridges']
    else:
        nfvis.result['bridges'] = []

        # Get the network information
    response = nfvis.request('/config/networks?deep')
    if 'network:networks' in response:
        nfvis.result['networks'] = response['network:networks']
    else:
        nfvis.result['networks'] = []

    # Check Mode makes to sense with a facts module, just ignore
    if module.check_mode:
        nfvis.exit_json(**nfvis.result)

    nfvis.exit_json(**nfvis.result)


if __name__ == '__main__':
    main()
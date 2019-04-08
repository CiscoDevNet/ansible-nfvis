#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_deployment

short_description: Deploys a VNF onto an NFVIS host

version_added: "n/a"

description:
    - "TDeploys a VNF onto an NFVIS host"

options:
    name:
        description:
            - Name of the deployment
        required: true
    state:
        description:
            - The state if the bridge ('present' or 'absent') (Default: 'present')
        required: false
    image:
        description:
            - The name of the image to use for the deployment
        required: true
    flavor:
        description:
            - The name of the flavor to use for the deployment
        required: true
    interfaces:
        description:
            - A list of dictionaries specifying the interfaces to create for the VNF
        required: false
    bootup_time:
        description:
            - The time to allow the VNF to boot before starting monitoring
        required: false
    port_forwarding:
        description:
            - A list of dictionaries specifying which ports to proxy to the VNF (_Note: monitoring must be enabled_)
        required: false
    config_data:
        description:
            - A list of dictionaries defining the configuration data to feed to the deployment via cloud-init
        required: false

author:
    - Steven Carter
'''

EXAMPLES = '''
# Create a new deployment
- nfvis_deployment:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: isrv1
    state: present
    image: isrv
    flavor: isrv-small
    interfaces:
      - network: int-mgmt-net
      - network: wan-net
      - network: lan-net
    bootup_time: 600
    port_forwarding:
      - proxy_port: 20001
        source_bridge: 'wan-br'
    config_data:
      - dst: iosxe_config.txt
        data: "{{ lookup('template', 'iosxe_config.txt.j2') }}"

# Delete a deployment
- nfvis_deployment:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: isrv1
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
                         name=dict(type='str', aliases=['deployment']),
                         image=dict(type='str', required=True),
                         flavor=dict(type='str', required=True),
                         bootup_time=dict(type='int', default=-1),
                         recovery_wait_time=dict(type='int', default=0),
                         kpi_data=dict(type='bool', default=False),
                         scaling=dict(type='bool', default=False),
                         scaling_min_active=dict(type='int', default=1),
                         scaling_max_active=dict(type='int', default=1),
                         placement_type=dict(type='str', default='zone_host'),
                         placement_enforcement=dict(type='str', default='strict'),
                         placement_host=dict(type='str', default='datastore1'),
                         recovery_type=dict(type='str', default='AUTO'),
                         action_on_recovery=dict(type='str', default='REBOOT_ONLY'),
                         interfaces=dict(type='list'),
                         port_forwarding=dict(type='list'),
                         config_data=dict(type='list'),
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
    nfvis = nfvisModule(module, function='deployment')

    payload = None
    port = None
    response = {}

    # Get the list of existing deployments
    url_path = '/config/vm_lifecycle/tenants/tenant/admin/deployments?deep'
    response = nfvis.request(url_path, method='GET')
    nfvis.result['current'] = response
    
    # Turn the list of dictionaries returned in the call into a dictionary of dictionaries hashed by the deployment name
    deployment_dict = {}
    try:
        for item in response['vmlc:deployments']['deployment']:
            name = item['name']
            deployment_dict[name] = item
    except TypeError:
        pass
    except KeyError:
        pass

    if nfvis.params['state'] == 'present':
        if nfvis.params['name'] in deployment_dict:
            # The deployment exists on the device, so check to see if it is the same configuration
            nfvis.result['changed'] = False
        else:
            # The deployment does not exist on the device, so add it
            # Construct the payload
            payload = {'deployment': {}}
            payload['deployment']['name'] = nfvis.params['name']
            payload['deployment']['vm_group'] = {}
            payload['deployment']['vm_group']['name'] = nfvis.params['name']
            payload['deployment']['vm_group']['image'] = nfvis.params['image']
            payload['deployment']['vm_group']['flavor'] = nfvis.params['flavor']
            payload['deployment']['vm_group']['bootup_time'] = nfvis.params['bootup_time']
            payload['deployment']['vm_group']['recovery_wait_time'] = nfvis.params['recovery_wait_time']
            payload['deployment']['vm_group']['kpi_data'] = {}
            payload['deployment']['vm_group']['kpi_data']['enabled'] = nfvis.params['kpi_data']
            payload['deployment']['vm_group']['scaling'] = {}
            payload['deployment']['vm_group']['scaling']['min_active'] = nfvis.params['scaling_min_active']
            payload['deployment']['vm_group']['scaling']['max_active'] = nfvis.params['scaling_max_active']
            payload['deployment']['vm_group']['scaling']['elastic'] = nfvis.params['scaling']
            payload['deployment']['vm_group']['placement'] = {}
            payload['deployment']['vm_group']['placement']['type'] = nfvis.params['placement_type']
            payload['deployment']['vm_group']['placement']['enforcement'] = nfvis.params['placement_enforcement']
            payload['deployment']['vm_group']['placement']['host'] = nfvis.params['placement_host']
            payload['deployment']['vm_group']['recovery_policy'] = {}
            payload['deployment']['vm_group']['recovery_policy']['recovery_type'] = nfvis.params['recovery_type']
            payload['deployment']['vm_group']['recovery_policy']['action_on_recovery'] = nfvis.params['action_on_recovery']

            port_forwarding = {}
            if nfvis.params['port_forwarding']:
               for item in nfvis.params['port_forwarding']:
                   port_forwarding['port'] = {}
                   port_forwarding['port']['type'] = item.get('type', 'ssh')
                   port_forwarding['port']['vnf_port'] = item.get('vnf_port', 22)
                   port_forwarding['port']['external_port_range'] = {}
                   if 'proxy_port' in item:
                       port_forwarding['port']['external_port_range']['start'] = item['proxy_port']
                       port_forwarding['port']['external_port_range']['end'] = item['proxy_port']
                   else:
                       module.fail_json(msg="proxy_port must be specified for port_forwarding")
                   port_forwarding['port']['protocol'] = item.get('protocol', 'tcp')
                   port_forwarding['port']['source_bridge'] = item.get('source_bridge', 'MGMT')

            if nfvis.params['interfaces']:
                payload['deployment']['vm_group']['interfaces'] = []
                for index, item in enumerate(nfvis.params['interfaces']):
                    entry = {}
                    entry['interface'] = {}
                    entry['interface']['nicid'] = item.get('nicid', index)
                    if 'network' in item:
                       entry['interface']['network'] = item['network']
                    else:
                        module.fail_json(msg="network must be specified for interface")
                    entry['interface']['model'] = item.get('model', 'virtio')
                    if index == 0 and 'port' in port_forwarding:
                       entry['interface']['port_forwarding'] = port_forwarding
                    payload['deployment']['vm_group']['interfaces'].append(entry)

            if nfvis.params['config_data']:
                payload['deployment']['vm_group']['config_data'] = []
                for item in nfvis.params['config_data']:
                    entry = {'configuration': {}}
                    if 'dst' in item:
                       entry['configuration']['dst'] = item['dst']
                    else:
                       module.fail_json(msg="dst must be specified for config_data")
                    if 'data' in item:
                        if isinstance(item['data'], str):
                            entry['configuration']['data'] = item['data']
                        else:
                            entry['configuration']['data'] = json.dumps(item['data'])
                    else:
                       module.fail_json(msg="data must be specified for config_data")
                    payload['deployment']['vm_group']['config_data'].append(entry)

            if nfvis.params['kpi_data'] == True or nfvis.params['bootup_time'] > 0:
                payload['deployment']['vm_group']['kpi_data']['kpi'] = {}
                payload['deployment']['vm_group']['kpi_data']['kpi']['event_name'] = 'VM_ALIVE'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_value'] = 1
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_cond'] = 'GT'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_type'] = 'UINT32'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector'] = {}
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['type'] = 'ICMPPing'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['nicid'] = 0
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['poll_frequency'] = 3
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['polling_unit'] = 'seconds'
                payload['deployment']['vm_group']['kpi_data']['kpi']['metric_collector']['continuous_alarm'] = False
                payload['deployment']['vm_group']['rules'] = {}
                payload['deployment']['vm_group']['rules']['admin_rules'] = {}
                payload['deployment']['vm_group']['rules']['admin_rules']['rule'] = {}
                payload['deployment']['vm_group']['rules']['admin_rules']['rule']['event_name'] = 'VM_ALIVE'
                payload['deployment']['vm_group']['rules']['admin_rules']['rule']['action'] = [ "ALWAYS log", "FALSE recover autohealing", "TRUE servicebooted.sh" ]



            nfvis.result['payload'] = payload
            url_path = '/config/vm_lifecycle/tenants/tenant/admin/deployments'
            response = nfvis.request(url_path, method='POST', payload=json.dumps(payload))
            nfvis.result['changed'] = True
    else:
        if nfvis.params['name'] in deployment_dict:
            url_path = '/config/vm_lifecycle/tenants/tenant/admin/deployments/deployment/{0}'.format(nfvis.params['name'])
            response = nfvis.request(url_path, 'DELETE')
            nfvis.result['changed'] = True


    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    # FIXME: Work with nfvis so they can implement a check mode
    if module.check_mode:
        module.exit_json(**nfvis.result)

    # execute checks for argument completeness

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**nfvis.result)


if __name__ == '__main__':
    main()
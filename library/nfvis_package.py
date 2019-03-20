#!/usr/bin/python

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: nfvis_package

short_description: This is my sample module

version_added: "2.4"

description:
    - "This is my longer description explaining my sample module"

options:
    name:
        description:
            - The name of the package
        required: true
    state:
        description:
            - The state if the bridge ('present' or 'absent') (Default: 'present')
        required: false
    file:
        description:
            - The file name of the package
        required: false

author:
    - Steven Carter
'''

EXAMPLES = '''
# Upload and register a package
- name: Package
  nfvis_package:
    host: 1.2.3.4
    user: admin
    password: cisco
    file: asav.tar.gz
    name: asav
    state: present

# Deregister a package
- name: Package
  nfvis_package:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: asav
    state: absent
'''

RETURN = '''
original_message:
    description: The original name param that was passed in
    type: str
message:
    description: The output message that the sample module generates
'''

# import requests
import os.path
# from requests.auth import HTTPBasicAuth
# from paramiko import SSHClient
# from scp import SCPClient
from ansible.module_utils.basic import AnsibleModule, json
from ansible.module_utils.nfvis import nfvisModule, nfvis_argument_spec

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False

try:
    from scp import SCPClient
    HAS_SCP = True
except ImportError:
    HAS_SCP = False

def run_module():
    # define available arguments/parameters a user can pass to the module
    argument_spec = nfvis_argument_spec()
    argument_spec.update(state=dict(type='str', choices=['absent', 'present'], default='present'),
                         name=dict(type='str', required=True),
                         file=dict(type='str', required=True),
                         dest=dict(type='str', default='/data/intdatastore/uploads'),
                         )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        changed=False,
        original_message='',
        message=''
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True,
                           )
    nfvis = nfvisModule(module, function='package')

    if not HAS_PARAMIKO:
        module.fail_json(
            msg='library paramiko is required when file_pull is False but does not appear to be '
                'installed. It can be installed using `pip install paramiko`'
        )

    if not HAS_SCP:
        module.fail_json(
            msg='library scp is required when file_pull is False but does not appear to be '
                'installed. It can be installed using `pip install scp`'
        )

    # if the user is working with this module in only check mode we do not
    # want to make any changes to the environment, just return the current
    # state with no modifications
    if module.check_mode:
        return result

    # manipulate or modify the state as needed (this is going to be the
    # part where your module will do what it needs to do)
    # result['original_message'] = module.params['name']

    # use whatever logic you need to determine whether or not this module
    # made any modifications to your target
    # if module.params['new']:
    #     result['changed'] = True

    # Login
    # session = requests.Session()
    # data = {"login": module.params['user'], "password": module.params['password']}
    # url = 'https://{0}/#/login'.format(module.params['host'])
    # try:
    #     response = response = session.post(url, data=data, verify=module.params['validate_certs'])
    # except requests.exceptions.RequestException as e:  # This is the correct syntax
    #     module.fail_json(msg=e, **result)
    # result['cookies'] = session.cookies

    # Get the list of images

    # url = 'https://{0}/api/config/vm_lifecycle/images?deep'.format(module.params['host'])
    # headers = {'Accept': 'application/json'}
    # try:
    #     response = requests.get(url, auth=(module.params['user'], module.params['password']), verify=module.params['validate_certs'],
    #             headers=headers)
    # except requests.exceptions.RequestException as e:  # This is the correct syntax
    #     module.fail_json(msg=e, **result)

    # url = 'https://{0}/v2/upload'.format(module.params['host'])
    # files = {'file': (os.path.basename(module.params['file']), open(module.params['file'], 'rb'), 'application/x-gzip', {'Expires': '0'})}
    # data = {'datastore':'datastore1'}
    # try:
    #     response = requests.post(url, verify=module.params['validate_certs'], auth=(module.params['user'], module.params['password']),
    #             files=files, data=data)
    #     response.raise_for_status()
    # except requests.exceptions.RequestException as e:
    #     module.fail_json(msg=e)
    #
    # if response.status_code not in [200]:
    #     module.fail_json(msg=(response.status_code, response.content))


    # Get the list of existing deployments
    url = 'https://{0}/api/config/vm_lifecycle/images?deep'.format(nfvis.params['host'])
    response = nfvis.request(url, method='GET')
    nfvis.result['data'] = response

    # Turn the list of dictionaries returned in the call into a dictionary of dictionaries hashed by the deployment name
    images_dict = {}
    try:
        for item in response['vmlc:images']['image']:
            name = item['name']
            images_dict[name] = item
    except TypeError:
        pass
    except KeyError:
        pass

    if nfvis.params['state'] == 'present':
        if nfvis.params['name'] not in images_dict:
            try:
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.load_system_host_keys()
                ssh.connect(hostname=module.params['host'], port=22222, username=module.params['user'],
                            password=module.params['password'], look_for_keys=False)
            except paramiko.AuthenticationException:
                module.fail_json(msg = 'Authentication failed, please verify your credentials')
            except paramiko.SSHException as sshException:
                module.fail_json(msg = 'Unable to establish SSH connection: %s' % sshException)
            except paramiko.BadHostKeyException as badHostKeyException:
                module.fail_json(msg='Unable to verify servers host key: %s' % badHostKeyException)
            except Exception as e:
                module.fail_json(msg=e.args)

            try:
                with SCPClient(ssh.get_transport()) as scp:
                    scp.put(module.params['file'], '/data/intdatastore/uploads')
            except scp.SCPException as e:
                module.fail_json(msg="Operation error: %s" % e)

            scp.close()

            payload = {'image': {}}
            payload['image']['name'] = nfvis.params['name']
            payload['image']['src'] = 'file://{0}/{1}.tar.gz'.format(nfvis.params['dest'], nfvis.params['name'])

            url = 'https://{0}/api/config/vm_lifecycle/images'.format(nfvis.params['host'])
            response = nfvis.request(url, method='POST', payload=json.dumps(payload))
            nfvis.result['changed'] = True
    else:
        if nfvis.params['name'] in images_dict:
            # Delete the image
            url = 'https://{0}/api/config/vm_lifecycle/images/image/{1}'.format(nfvis.params['host'], nfvis.params['name'])
            response = nfvis.request(url, 'DELETE')
            nfvis.result['changed'] = True
        else:
            nfvis.result['changed'] = False
        # Delete the file
        # payload = {
        #     'image': { 'name': '{0}.tar.gz'.format(nfvis.params['name']) }
        # }
        #
        # url = 'https://{0}/api/operations/system/file-delete/file'.format(nfvis.params['host'], nfvis.params['name'])
        # response = nfvis.request(url, method='POST', payload=json.dumps(payload))
        #
        # if nfvis.status == 204:
        #     nfvis.result['changed'] = True


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

def main():
    run_module()

if __name__ == '__main__':
    main()
from __future__ import absolute_import, division, print_function
__metaclass__ = type
import os
from ansible.module_utils.basic import AnsibleModule, json, env_fallback
from ansible.module_utils.urls import fetch_url
from ansible.module_utils._text import to_native, to_bytes, to_text

def nfvis_argument_spec():
    return dict(host=dict(type='str', required=True, fallback=(env_fallback, ['NFVIS_HOST'])),
            user=dict(type='str', required=True, fallback=(env_fallback, ['NFVIS_USER'])),
            password=dict(type='str', required=True, fallback=(env_fallback, ['NFVIS_PASSWORD'])),
            validate_certs=dict(type='bool', required=False, default=False),
            timeout=dict(type='int', default=60)
    )


class nfvisModule(object):

    def __init__(self, module, function=None):
        self.module = module
        self.params = module.params
        self.result = dict(changed=False)
        self.headers = dict()
        self.function = function
        self.orgs = None
        self.nets = None
        self.org_id = None
        self.net_id = None

        # normal output
        self.existing = None

        # info output
        self.config = dict()
        self.original = None
        self.proposed = dict()
        self.merged = None

        # debug output
        self.filter_string = ''
        self.method = None
        self.path = None
        self.response = None
        self.status = None
        self.url = None
        self.params['force_basic_auth'] = True
        self.params['url_username'] = self.params['user']
        self.params['url_password'] = self.params['password']
        self.host = self.params['host']
        self.modifiable_methods = ['POST', 'PUT', 'DELETE']

    def _fallback(self, value, fallback):
        if value is None:
            return fallback
        return value

    def request(self, url_path, method='GET', payload=None, operation=None):
        """Generic HTTP method for nfvis requests."""


        if operation in ['get_vlan', 'get_files']:
            self.headers = {'Content-Type': 'application/vnd.yang.data+json',
                            'Accept': 'application/vnd.yang.collection+json'}
        else:
            self.headers = {'Content-Type': 'application/vnd.yang.data+json',
                            'Accept': 'application/vnd.yang.data+json'}

        if method is not None:
            self.method = method
        self.url = 'https://{0}/api{1}'.format(self.host, url_path)
        self.method = method
        self.payload = payload

        resp, info = fetch_url(self.module, self.url,
                               headers=self.headers,
                               data=payload,
                               method=self.method,
                               timeout=self.params['timeout'],
                               )
        self.response = info['msg']
        self.status = info['status']

        if self.status >= 300 or self.status < 0:
            try:
                self.fail_json(msg='Request failed for {url}: {status} - {msg}'.format(**info),
                                  body=json.loads(to_native(info['body'])))
            except Exception:
                pass

            self.fail_json(msg='Request failed for {url}: {status} - {msg}'.format(**info))

        try:
            return json.loads(to_native(resp.read()))
        except Exception:
            pass
        
    def exit_json(self, **kwargs):
        """Custom written method to exit from module."""
        self.result['response'] = self.response
        self.result['status'] = self.status
        self.result['url'] = self.url
        if hasattr(self, 'payload'):
            self.result['payload'] = self.payload
        self.result['method'] = self.method

        self.result.update(**kwargs)
        self.module.exit_json(**self.result)

    def fail_json(self, msg, **kwargs):
        """Custom written method to return info on failure."""
        self.result['response'] = self.response
        self.result['status'] = self.status
        self.result['url'] = self.url
        if hasattr(self, 'payload'):
            self.result['payload'] = self.payload
        self.result['method'] = self.method

        self.result.update(**kwargs)
        self.module.fail_json(msg=msg, **self.result)
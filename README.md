# ansible-nfvis

An Ansible Role for automating Cisco NFVIS

This is a hybrid role that contains the following modules:

- nfvis_system
- nfvis_network
- nfvis_vlan
- nfvis_depoloyment
- nfvis_package

In addition the role can be called to help create packages:

```yaml
- name: Build packages
  include_role:
    name: ansible-nfvis
    tasks_from: build-package
  vars:
    package_name: asav
    package_version: 9.10.1
    package_image: asav9101.qcow2
    package_template: centos.image_properties.xml.j2
```

* `package_name`: The name of the package as referecned in deployments
* `package_version`: The version of the package
* `package_image`: The image with which to build the package
* `package_template`: The template from which the image_properties is derived

>Note: Since nfvis_deployment inject the config into the deployments, this task does not include any configuration.

## Module Examples

All modules requite authentication information for the NFVIS host:
* `host`: The address of the NFVIS device in which the API can be reached
* `user`: The username with which to authenticate to the NFVIS API
* `password`: The username with which to authenticate to the NFVIS API

#### Configure System:
```yaml
- name: Configure system
  nfvis_system:
    host: 1.2.3.4
    user: admin
    password: cisco
    hostname: "{{ inventory_hostname }}"
    trusted_source:
      - 0.0.0.0/0
    state: present
```

* `hostname`: The hostname of the NFVIS host
* `trusted_source`: A list of trusted sources in CIDR notation

#### Configure VLANs:

The `nfvis_vlan` module maintains vlans on the switch (i.e. requires ENCS):
```yaml
- nfvis_vlan:
    host: 1.2.3.4
    user: admin
    password: cisco
    state: present
    vlan_id: 100
```

* `vlan_id`: The VLAN ID to add to the switch
* `state`: The state of the VLAN.  Can be `present` to add the VLAN or `absent` to delete the VLAN. (default: `present`)

#### Configure Networks:
```yaml
- nfvis_network:
    host: 1.2.3.4
    user: admin
    password: cisco
    name: new-network
    bridge: net-bridge
    trunk: no
    vlan: 100
    state: present
```

* `name`: Name of the network
* `bridge`: The bride to which the network is associated

#### Deploy VNF:
```yaml
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
```

* `name`: Name of the deployment (required)
* `image`: The name of the image to use for the deployment (required)
* `flavor`: The name of the image to use for the deployment (required)
* `interfaces`: A list of dictionaries specifying the interfaces to create for the VNF
    * `network`: The name of the network to attach the interface (required)
    * `nicid`: The nic id of the interface.  (Default: the index of that element in the list)
    * `model`: The model of the deriver to use (default `vitio`)
* `bootup_time`: The time to allow the VNF to boot before starting monitoring
* `port_forwarding`: A list of dictionaries specifying which ports to proxy to the VNF (_Note: monitoring must be enabled_)
    * `proxy_port`: The port on the NFVIS device to be proxied to the VNF (required)
    * `vnf_port`: The destination port on the VNF (Default: 22)
    * `source_bridge`: The bridge on the NFVIS device to attach the proxy (Default: MGMT)
    * `protocol`: The protocol of the port to be proxied (default `tcp`)
    * `type`: The type of proxy (default `ssh`)
* `state`: The state of the VLAN.  Can be `present` to add the VLAN or `absent` to delete the VLAN. (default: `present`)

#### Upload Packages
```yaml
- name: Package
  nfvis_package:
    host: 1.2.3.4
    user: admin
    password: cisco
    file: asav.tar.gz
    name: asav
    state: present
```

* `name`: The name of the package
* `file`: The file name of the package
* `state`: The state of the VLAN.  Can be `present` to add package or `absent` to delete the package. (default: `present`)

License
-------

CISCO SAMPLE CODE LICENSE
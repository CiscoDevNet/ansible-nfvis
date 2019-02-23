# ansible-nfvis


An Ansible Role for automating Cisco NFVIS

This role can perform the following functions:
- Configure Network
- Configure VLANs
- Deploy VNFs


## Examples


Configure Networks:
```yaml
    - name: Configure Network
      include_role:
        name: ansible-nfvis
        tasks_from: networks
```

Configure VLANs:
```yaml
    - name: Configure VLANs
      include_role:
        name: ansible-nfvis
        tasks_from: vlans
```

Deploy VNF:
```yaml
    - name: Deploy VNFs
      include_role:
        name: ansible-nfvis
        tasks_from: deploy
```

License
-------

CISCO SAMPLE CODE LICENSE
#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2019, Mikhail Yohman (@FragmentedPacket) <mikhail.yohman@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
module: netbox_circuit
short_description: Create, update or delete circuits within Netbox
description:
  - Creates, updates or removes circuits from Netbox
notes:
  - Tags should be defined as a YAML list
  - This should be ran with connection C(local) and hosts C(localhost)
author:
  - Mikhail Yohman (@FragmentedPacket)
requirements:
  - pynetbox
version_added: '0.1.0'
options:
  netbox_url:
    description:
      - URL of the Netbox instance resolvable by Ansible control host
    required: true
  netbox_token:
    description:
      - The token created within Netbox to authorize API access
    required: true
  data:
    description:
      - Defines the circuit configuration
    suboptions:
      cid:
        description:
          - The circuit id of the circuit
        required: true
      provider:
        description:
          - The provider of the circuit
        required: true
      circuit_type:
        description:
          - The circuit type of the circuit
      status:
        description:
          - The status of the circuit
        choices:
          - Active
          - Offline
          - Planned
          - Provisioning
          - Deprovisioning
          - Decommissioned
      tenant:
        description:
          - The tenant assigned to the circuit
      install_date:
        description:
          - The date the circuit was installed. e.g. YYYY-MM-DD
      commit_rate:
        description:
          - Commit rate of the circuit (Kbps)
      description:
        description:
          - Description of the circuit
      comments:
        description:
          - Comments related to circuit
      tags:
        description:
          - Any tags that the device may need to be associated with
      custom_fields:
        description:
          - must exist in Netbox
  state:
    description:
      - Use C(present) or C(absent) for adding or removing.
    choices: [ absent, present ]
    default: present
  validate_certs:
    description:
      - If C(no), SSL certificates will not be validated. This should only be used on personally controlled sites using self-signed certificates.
    default: 'yes'
    type: bool
"""

EXAMPLES = r"""
- name: "Test Netbox modules"
  connection: local
  hosts: localhost
  gather_facts: False

  tasks:
    - name: Create circuit within Netbox with only required information
      netbox_circuit:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          cid: Test Circuit
          provider: Test Provider
          circuit_type: Test Circuit Type
        state: present

    - name: Update circuit with other fields
      netbox_circuit:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          cid: Test-Circuit-1000
          provider: Test Provider
          circuit_type: Test Circuit Type
          status: Active
          tenant: Test Tenant
          install_date: "2018-12-25"
          commit_rate: 10000
          description: Test circuit
          comments: "FAST CIRCUIT"
        state: present

    - name: Delete circuit within netbox
      netbox_circuit:
        netbox_url: http://netbox.local
        netbox_token: thisIsMyToken
        data:
          cid: Test-Circuit-1000
        state: absent
"""

RETURN = r"""
circuit:
  description: Serialized object as created or already existent within Netbox
  returned: success (when I(state=present))
  type: dict
msg:
  description: Message indicating failure or info about what has been achieved
  returned: always
  type: str
"""

from ansible_collections.netbox_community.ansible_modules.plugins.module_utils.netbox_utils import (
    NetboxAnsibleModule,
    NETBOX_ARG_SPEC,
)
from ansible_collections.netbox_community.ansible_modules.plugins.module_utils.netbox_circuits import (
    NetboxCircuitsModule,
    NB_CIRCUITS,
)


def main():
    """
    Main entry point for module execution
    """
    argument_spec = NETBOX_ARG_SPEC
    argument_spec.update(
        dict(
            data=dict(
                type="dict",
                required=True,
                options=dict(
                    cid=dict(required=True, type="str"),
                    provider=dict(required=False, type="raw"),
                    circuit_type=dict(required=False, type="raw"),
                    # Will uncomment other status dict once slugs are the only option (Netbox 2.8)
                    status=dict(required=False, type="raw"),
                    # status=dict(
                    #    required=False,
                    #    choices=[
                    #        "Active",
                    #        "Offline",
                    #        "Planned",
                    #        "Provisioning",
                    #        "Deprovisioning",
                    #        "Decommissioned",
                    #    ],
                    # ),
                    tenant=dict(required=False, type="raw"),
                    install_date=dict(required=False, type="str"),
                    commit_rate=dict(required=False, type="int"),
                    description=dict(required=False, type="str"),
                    comments=dict(required=False, type="str"),
                    tags=dict(required=False, type=list),
                    custom_fields=dict(required=False, type=dict),
                ),
            ),
        )
    )

    required_if = [("state", "present", ["cid"]), ("state", "absent", ["cid"])]

    module = NetboxAnsibleModule(
        argument_spec=argument_spec, supports_check_mode=True, required_if=required_if
    )

    netbox_circuit = NetboxCircuitsModule(module, NB_CIRCUITS)
    netbox_circuit.run()


if __name__ == "__main__":
    main()

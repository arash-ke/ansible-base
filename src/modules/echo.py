#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec = dict(
            msg = dict(required=True, alias=["message"]),
        ),
        supports_check_mode=True
    )

    module.exit_json(changed=False, echo=module.params['msg'])


if __name__ == '__main__':
    main()
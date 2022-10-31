#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec = dict(
            user_groups = dict(type="list", default=[]),
            user_roles = dict(type="list", default=[]),
            system_roles = dict(type="dict", default=[]),
            host_roles = dict(type="list", default=[]),
            current_groups = dict(type="list", default=None)
        ),
        supports_check_mode=True
    )
    result = dict(changed=False)
    groups = []
    for g in module.params['user_groups']:
        if g != "":
            groups.append(g)

    system_roles = module.params['system_roles']
    host_roles = module.params['host_roles']
    user_roles = module.params['user_roles']

    for r in user_roles:
        if r in system_roles:
            sr = system_roles[r]
            if 'role' in sr:
                if sr['role'] != '*' and sr['role'] not in  host_roles:
                    continue
            if type(sr['groups']) == str:
                if sr['groups'] != "":
                    groups.append(sr['groups'])
            elif type(sr['groups']) == list:
                for g in sr['groups']:
                    if g != "":
                        groups.append(g)
    
    result['groups'] = groups
    result['msg'] = "User groups should be: %s" % ",".join(groups)
    # if module.params['current_groups'] != None:
    #     result['diff'] = dict()
    #     cg = module.params['current_groups']
    #     result['diff']['before'] = ','.join(cg.sort()) + ', test'
    #     result['diff']['after'] = ','.join(groups.sort())

    module.exit_json(**result)


if __name__ == '__main__':
    main()
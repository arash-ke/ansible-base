from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
# from ansible.errors import AnsibleFilterError, AnsibleFilterTypeError

add_formtas = {
    "comment": "comment \"{value}\"",
    "timeout": "timeout {value}",
    "counters": "counter {value}",
    "packets": "packets {value}",
    "bytes": "bytes {value}",
    "skbinfo": "skbinfo  {value}",
    "skbmark": "skbmark {value}",
    "skbprio": "skbprio {value}",
    "skbqueue": "skbqueue {value}",
}

create_formats = {
    "family": "family {value}",
    "hashsize": "hashsize {value}",
    "maxelem": "maxelem {value}",
    "comment": "comment",
    "timeout": "timeout",
    "counters": "counters",
    "packets": "packets",
    "bytes": "bytes",
    "skbinfo": "skbinfo",
    "skbmark": "skbmark",
    "skbprio": "skbprio",
    "skbqueue": "skbqueue",
    "nomatch": "nomatch",
    "forceadd": "forceadd"
}

class IpsetFormater():
    ''' Ipset formater '''
    def __init__(self, f=add_formtas):
        self.format_map = f

    def __apply_format(self, f, **args):
        return f.format(**args)

    def __format(self, k, v):
        if k in self.format_map:
            f = self.format_map[k]
            return f.format(value=v)
        return None

    def parse(self, k, v):
        result = self.__format(k, v)
        return result
        
def make_ipset_rule(rule_options, list_name):
    formater = IpsetFormater()
    
    action = 'add'
    if 'action' in rule_options:
        action = rule_options['action']
    
    rule = [action, list_name, rule_options['addr']]
    for k in rule_options:
        a = formater.parse(k, rule_options[k])
        if a != None:
            rule.append(a)
    return ' '.join(rule)

def make_ipset_set(set_options, list_name):
    formater = IpsetFormater(create_formats)

    action = 'create'
    if 'action' in set_options:
        action = set_options['action']
    rule = [action, list_name, set_options['type']]
    for k in set_options:
        a = formater.parse(k, set_options[k])
        if a != None:
            rule.append(a)
    return ' '.join(rule)

class FilterModule(object):
    ''' Ansible ipsets filter '''

    def filters(self):
        filters = {
            'make_ipset_rule': make_ipset_rule,
            'make_ipset_set': make_ipset_set,
        }

        return filters
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
# from ansible.errors import AnsibleFilterError, AnsibleFilterTypeError

ifcfg_formats = {
    "type": "TYPE={value}",
    "mac": "HWADDR={value}",
    "mode": "BOOTPROTO={value}",
    "ipaddr": "IPADDR={value}",
    "netmask": "NETMASK={value}",
    "aliases": "IPADDR{index}={ipaddr}\nPREFIX{index}={prefix}",
    "prefix": "PREFIX={value}",
    "gateway": "GATEWAY={value}",
    "dns": "DNS{index}={value}",
    "domain": "DOMAIN={value}",
    "auto_up": "ONBOOT={value}",
}

class IfcfgFormater():
    ''' Ipset formater '''
    def __init__(self, f=ifcfg_formats):
        self.format_map = f

    def __apply_format(self, f, **args):
        return f.format(**args)

    def __format(self, k, v):
        if k in self.format_map:
            f = self.format_map[k]
            r = []
            if type(v) is list:
                for i, val in enumerate(v):
                    if type(val) is dict:
                        r.append(f.format(index=i+1, **val))
                    else:
                        r.append(f.format(index=i+1, value=val))
            else:
                r.append(f.format(value=v))
            return "\n".join(r)
        return "# %s = %s" % (k, v)

    def parse(self, k, v):
        return self.__format(k, v)
        
def make_centos_net_config(option_name, option_value):
    formater = IfcfgFormater()
    
    return formater.parse(option_name, option_value)

class FilterModule(object):
    ''' Ansible centos network filter '''

    def filters(self):
        filters = {
            'make_ifcfg_config': make_centos_net_config,
        }

        return filters
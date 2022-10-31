from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json
# from ansible.errors import AnsibleFilterError, AnsibleFilterTypeError

class IptableFormater:
    __ipt_spec_targets = {
        "ACCEPT",
        "DROP",
        "QUEUE",
        "RETURN"
    }

    __formats = {
        "proto": "{negate}-p {value}",
        "dport": "{negate}--dport {value}",
        "dports": "-m multiport {negate}--dports {value}",
        "sport": "{negate}--sport {value}",
        "sports": "-m multiport {negate}--sports {value}",
        "src": "{negate}-s {value}",
        "dst": "{negate}-d {value}",
        "in": "{negate}-i {value}",
        "out": "{negate}-o {value}",
        "ctstate": "-m conntrack {negate}--ctstate {value}",
        "state": "-m state {negate}--state {value}",
        "icmp": "-m icmp {negate}--icmp-type {value}",
        "icmpv6": "-m ipv6-icmp {negate}--icmpv6-type {value}",
        "tcp": "-m tcp --tcp-flags {value}",
        "clamp": "-j TCPMSS --set-mss {value}",
        "clamp_pmtu": "-j TCPMSS --clamp-mss-to-pmtu",
        "src_list": "-m set {negate}--match-set {value} src",
        "dst_list": "-m set {negate}--match-set {value} dst",
        "action": "{action} {value}",
        "goto": "-g {value}",
        "jump": "-j {value}",
        "to": "--to {value}",
        "snat": "-j SNAT --to {value}",
        "dnat": "-j DNAT --to {value}",
        "log": "-j LOG --log-prefix {value}",
        "masquerade": "-j MASQUERADE",
        "comment": "-m comment --comment \"{value}\"",
        "chain": "-A {value}",
        "set_recent": "-m recent --set --name {value}",
        "update_recent": "-m recent --update --name {value}",
        "check_recent": "-m recent --rcheck --name {value}",
        "check_reap_recent": "-m recent --rcheck --reap --name {value}",
        "rsource": "--rsource",
        "rdest": "--rdest",
        "add_ipset": "-j SET {value}",
        "mask": "{negate}--mask {value}",
        "hitcount": "--hitcount {value}",
        "rttl": "--rttl",
        "limit": "-m limit --limit {value}",
        "limit_burst": "--limit-burst {value}",
        "seconds": "--seconds {value}",
        "p_marked": "-m mark {negate}--mark {value}",
        "p_mark": "-j MARK --set-mark {value}",
        "p_xmark": "-j MARK --set-xmark {value}",
        "p_and_mark": "-j MARK --and-mark {value}",
        "p_or_mark": "-j MARK --or-mark {value}",
        "p_xor_mark": "-j MARK --xor-mark {value}",
        "p_save_mark": "-j MARK --save-mark {value}",
        "p_restore_mark": "-j MARK --restore-mark {value}",
        "c_marked": "-m connmark {negate}--mark {value}",
        "c_mark": "-j CONNMARK --set-mark {value}",
        "c_xmark": "-j MARK --set-mark {value}",
        "c_and_mark": "-j MARK --set-mark {value}",
        "c_or_mark": "-j MARK --set-mark {value}",
        "c_xor_mark": "-j MARK --set-mark {value}",
        "c_save_mark": "-j CONNMARK --save-mark",
        "c_restore_mark": "-j CONNMARK --restore-mark",
        "tls_host": "-m tls --tls-host \"{value}\"",
        "tls_hostset": "-m tls --tls-hostset \"{value}\"",
        "http_host": "-m string --string \"HOST: {value}\\n\"",
        "string_bm": "-m string --string \"{value}\" --algo bm",
        "algo": "--algo {value}",
        "redirect": "-j REDIRECT",
        "reset": "-m reset -j RESET",
        "reject": "-j reject {value}",
        "raw": "{value}"
    }

    def __init__(self):
        self.action = "-j"

    def __apply_format(self, f, **args):
        return f.format(**args)

    def __format(self, k, v, negate=False):
        if v == None:
            return None
        if v == True:
            v = ""
        n = ""
        if negate:
            n = "! "
        if k.lower() in self.__formats:
            f = self.__formats[k.lower()]
            return f.format(value=v, negate=n, action=self.action)
        return None
        
    def parse(self, k, v):
        lk = k
        negate = False

        if lk.startswith('not_'):
            lk = k.lstrip('not_')
            negate = True

        if lk == 'action' and not v:
            return None
        elif lk == 'action' and v in self.__ipt_spec_targets:
            self.action = "-j"
        result = self.__format(lk, v, negate)
        # if result == None:
        #     result = ""
        
        return result
        
def make_iptable_rule(rule_options):
    formater = IptableFormater()
    passthrough = True
    if 'passthrough' in rule_options:
        passthrough = rule_options['passthrough']
    action = "-j"
    if not passthrough:
        action = "-g"
    
    formater.action = action
    rule=[]
    for k in rule_options:
        r = formater.parse(k, rule_options[k])
        if not r == None:
            rule.append(r)
    
    if not passthrough:
        pr = rule.copy()
        raction = None
        for b in pr:
            if b.startswith('-j'):
                raction = b
                break
        if not raction == None:
            pr.remove(raction)
            pr.append('-j RETURN')
            rule.append('\n')
            rule.extend(pr)

    return ' '.join(rule)

class FilterModule(object):
    ''' Ansible iptables filter '''

    def filters(self):
        filters = {
            'make_iptable_rule': make_iptable_rule,
        }

        return filters
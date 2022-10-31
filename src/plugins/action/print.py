from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleUndefinedVariable
from ansible.module_utils.six import string_types
from ansible.module_utils._text import to_text
from ansible.plugins.action import ActionBase
from ansible.plugins.action.debug import ActionModule as BaseAction

class ActionModule(BaseAction):
  ''' Print custom messages '''
  TRANSFERS_FILES = False
  _VALID_ARGS = frozenset(('msg', 'var', 'verbosity', 'title'))

  def run(self, tmp=None, task_vars=None):
    result = super().run(tmp=tmp, task_vars=task_vars)
    if 'title' in self._task.args and 'msg' in self._task.args:
          result[self._task.args["title"]] = result.pop("msg")
    return result
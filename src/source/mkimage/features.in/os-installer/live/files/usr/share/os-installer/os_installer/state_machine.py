# SPDX-License-Identifier: GPL-3.0-or-later

from .config import config
from .installation_scripting import installation_scripting


page_order = [
    'language',
    'welcome',
    # required pre-install info
    'keyboard-overview',
    'internet',
    'disk',
    'partition',
    'encrypt',
    'desktop',
    'confirm',
    # configuration
    'user',
    'locale',
    'software',
    'feature',
    # fixed block towards end
    'summary',
    'install',
    'done',
    'restart']


class StateMachine:
    def __init__(self):
        self.latest_page = 0
        if not config.get('internet_connection_required'):
            installation_scripting.can_run_prepare()

    def transition(self, prev_page, reached_page):
        ret_val = None

        if prev_page == 'language':
            ret_val = 'retranslate'

        new_index = page_order.index(reached_page)
        if self.latest_page >= new_index:
            return ret_val

        for page in page_order[self.latest_page+1:new_index+1]:
            match page:
                case 'disk':
                    installation_scripting.can_run_prepare()
                case 'user':
                    if prev_page == 'confirm':
                        installation_scripting.can_run_install()
                        ret_val = 'no_return'
                case 'install':
                    installation_scripting.can_run_configure()
                    ret_val = 'no_return'
                case 'done' | 'failed' | 'restart' | 'summary':
                    ret_val = 'no_return'
        self.latest_page = new_index

        return ret_val


state_machine = StateMachine()

# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config
from .installation_scripting import installation_scripting


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/install.ui')
class InstallPage(Gtk.Box):
    __gtype_name__ = __qualname__

    terminal_box = Gtk.Template.Child()
    stack = Gtk.Template.Child()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        # UI element states
        self.terminal_box.append(installation_scripting.terminal)
        self.stack.set_visible_child_name('spinner')
        config.subscribe('installation_running', self._installation_done, delayed=True)

    def _installation_done(self, running):
        if not running:
            self.terminal_box.remove(installation_scripting.terminal)

    ### callbacks ###

    @Gtk.Template.Callback('terminal_button_toggled')
    def _terminal_button_toggled(self, toggle_button):
        if self.stack.get_visible_child_name() == 'spinner':
            self.stack.set_visible_child_name('terminal')
        else:
            self.stack.set_visible_child_name('spinner')

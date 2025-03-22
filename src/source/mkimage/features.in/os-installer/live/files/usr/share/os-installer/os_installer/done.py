# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config
from .installation_scripting import installation_scripting


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/done.ui')
class DonePage(Gtk.Box):
    __gtype_name__ = __qualname__

    stack = Gtk.Template.Child()
    terminal_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)
        self.terminal_box.append(installation_scripting.terminal)

    ### callbacks ###

    @Gtk.Template.Callback('restart_button_clicked')
    def _restart_button_clicked(self, button):
        self.terminal_box.remove(installation_scripting.terminal)
        config.set_next_page(self)

    @Gtk.Template.Callback('terminal_button_toggled')
    def _terminal_button_toggled(self, toggle_button):
        if self.stack.get_visible_child_name() == "buttons":
            self.stack.set_visible_child_name("terminal")
        else:
            self.stack.set_visible_child_name("buttons")

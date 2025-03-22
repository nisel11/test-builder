# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .installation_scripting import installation_scripting
from .system_calls import open_internet_search


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/failed.ui')
class FailedPage(Gtk.Box):
    __gtype_name__ = __qualname__

    terminal_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)
        self.terminal_box.append(installation_scripting.terminal)

    ### callbacks ###

    @Gtk.Template.Callback('search_button_clicked')
    def _search_button_clicked(self, button):
        open_internet_search()

# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .system_calls import reboot_system


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/restart.ui')
class RestartPage(Gtk.Box):
    __gtype_name__ = __qualname__

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)
        reboot_system()

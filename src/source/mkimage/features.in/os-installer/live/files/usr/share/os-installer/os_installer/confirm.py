# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/confirm.ui')
class ConfirmPage(Gtk.Box):
    __gtype_name__ = __qualname__

    disk_row = Gtk.Template.Child()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        config.subscribe('disk', self._update_disk_row)

    ### callbacks ###

    def _update_disk_row(self, disk):
        name, path = disk
        self.disk_row.set_title(name)
        self.disk_row.set_subtitle(path)

    @Gtk.Template.Callback('confirmed')
    def _confirmed(self, button):
        config.set_next_page(self)

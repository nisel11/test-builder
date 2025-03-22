# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/locale.ui')
class LocalePage(Gtk.Box):
    __gtype_name__ = __qualname__

    formats_label = Gtk.Template.Child()
    timezone_label = Gtk.Template.Child()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        config.subscribe('formats', self._update_formats)
        config.subscribe('timezone', self._update_timezone)

    ### callbacks ###

    def _update_formats(self, formats):
        self.formats_label.set_label(formats[1])

    def _update_timezone(self, timezone):
        self.timezone_label.set_label(timezone)

    @Gtk.Template.Callback('continue')
    def _continue(self, button):
        config.set_next_page(self)

    @Gtk.Template.Callback('overview_row_activated')
    def _overview_row_activated(self, list_box, row):
        config.set('displayed-page', row.get_name())

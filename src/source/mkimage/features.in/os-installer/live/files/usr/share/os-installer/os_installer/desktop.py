# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config
from .desktop_provider import desktop_provider
from .widgets import DesktopEntry


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/desktop.ui')
class DesktopPage(Gtk.Box):
    __gtype_name__ = __qualname__

    grid = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    selected_description = Gtk.Template.Child()
    selected_image = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.button_label = self.continue_button.get_label()
        self.selected_entry = None

        number = 0
        for desktop in desktop_provider.get_desktops():
            entry = DesktopEntry(desktop)
            entry.connect('clicked', self._desktop_activated)
            if number == 0:
                self._set_selected_desktop(entry)
            self.grid.attach(entry, number % 3, int(number/3), 1, 1)
            number += 1

    def _set_selected_desktop(self, entry):
        desktop = entry.desktop
        self.continue_button.set_label(self.button_label.format(desktop.name))
        self.selected_image.set_paintable(None)
        self.selected_image.set_paintable(desktop.texture)
        self.selected_description.set_label(desktop.description)

        if self.selected_entry:
            self.selected_entry.remove_css_class('selected-card')
            self.selected_entry.remove_css_class('suggested-action')
        entry.add_css_class('selected-card')
        entry.add_css_class('suggested-action')
        self.selected_entry = entry

        config.set('desktop_chosen', desktop.keyword)

    ### callbacks ###

    def _desktop_activated(self, button):
        self._set_selected_desktop(button)

    @Gtk.Template.Callback('continue')
    def _continue(self, object):
        if self.continue_button.is_sensitive():
            config.set_next_page(self)

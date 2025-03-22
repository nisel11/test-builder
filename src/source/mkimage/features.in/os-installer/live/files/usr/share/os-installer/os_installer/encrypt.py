# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config
from .widgets import EntryErrorEnhancer


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/encrypt.ui')
class EncryptPage(Gtk.Box):
    __gtype_name__ = __qualname__

    switch_row = Gtk.Template.Child()
    pin_row = Gtk.Template.Child()
    pin_confirm_row = Gtk.Template.Child()
    info_revealer = Gtk.Template.Child()

    continue_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        encryption_setting = config.get('disk_encryption')
        self.min_pin_length = max(1, encryption_setting['min_length'])
        self.use_confirmation = encryption_setting['confirmation']

        if encryption_setting['forced']:
            self.switch_row.set_visible(False)
            self.active = True
        else:
            self.active = config.get('use_encryption')
            self.switch_row.set_active(self.active)
        self._adjust_pin_state()

        self.pin = EntryErrorEnhancer(
            self.pin_row, lambda text: len(text) > self.min_pin_length)
        self.pin_row.set_text(config.get('encryption_pin'))

        self.pin_confirm_row.set_visible(self.use_confirmation)
        if self.use_confirmation:
            self.confirmation = EntryErrorEnhancer(
                self.pin_confirm_row, lambda text: text == self.pin_row.get_text())
            self.pin_confirm_row.set_text(config.get('encryption_pin'))
        else:
             self.confirmation = True

    def _adjust_pin_state(self):
        self.pin_row.set_sensitive(self.active)
        self.pin_confirm_row.set_sensitive(self.active)
        self.info_revealer.set_reveal_child(self.active)
        self._set_continue_button()

    def _set_continue_button(self):
        self.continue_button.set_sensitive(not self.active or (self.pin and self.confirmation))

    ### callbacks ###

    @ Gtk.Template.Callback('switch_row_clicked')
    def _switch_row_clicked(self, row, state):
        self.active = self.switch_row.get_active()
        config.set('use_encryption', self.active)
        self._adjust_pin_state()

        if self.active:
            self.pin_row.grab_focus()
        else:
            config.set('encryption_pin', '')

    @Gtk.Template.Callback('pin_changed')
    def _pin_changed(self, editable):
        pin = editable.get_text()
        if self.pin.update_row(pin):
            config.set('encryption_pin', pin)
        self._pin_confirm_changed(self.pin_confirm_row)

    @Gtk.Template.Callback('pin_confirm_changed')
    def _pin_confirm_changed(self, editable):
        pin = editable.get_text()
        self.confirmation.update_row(pin)
        self._set_continue_button()

    @Gtk.Template.Callback('pin_activated')
    def _pin_activated(self, object):
        if self.use_confirmation:
            self.pin_confirm_row.grab_focus()
        else:
            self._continue(None)

    @Gtk.Template.Callback('continue')
    def _continue(self, object):
        if self.continue_button.is_sensitive():
            config.set_next_page(self)

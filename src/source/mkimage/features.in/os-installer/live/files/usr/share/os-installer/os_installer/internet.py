# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Lock, Thread

from gi.repository import Gtk

from .config import config
from .system_calls import open_wifi_settings, start_system_timesync


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/internet.ui')
class InternetPage(Gtk.Stack):
    __gtype_name__ = __qualname__
    image = 'network-wireless-disabled-symbolic'

    def __init__(self, **kwargs):
        Gtk.Stack.__init__(self, **kwargs)

        self.update_lock = Lock()
        self.has_advanced = False

        config.subscribe('internet_connection', self._connection_state_changed)

    ### callbacks ###

    @Gtk.Template.Callback('clicked_settings_button')
    def _clicked_settings_button(self, button):
        open_wifi_settings()

    def _connection_state_changed(self, connected):
        with self.update_lock:
            if connected:
                self.set_visible_child_name('connected')
                config.set('internet_page_image',
                           'network-wireless-symbolic')
                start_system_timesync()
                if not self.has_advanced:
                    self.has_advanced = True
                    Thread(target=config.set_next_page, args=[self]).start()
            else:
                self.set_visible_child_name('not-connected')
                config.set('internet_page_image',
                           'network-wireless-disabled-symbolic')

    @Gtk.Template.Callback('continue')
    def _continue(self, object):
        config.set_next_page(self)

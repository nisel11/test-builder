# SPDX-License-Identifier: GPL-3.0-or-later

import sys

import gi
# set versions for all used submodules
gi.require_version('Gio', '2.0')           # noqa: E402
gi.require_version('GLib', '2.0')          # noqa: E402
gi.require_version('Gdk', '4.0')           # noqa: E402
gi.require_version('Gtk', '4.0')           # noqa: E402
gi.require_version('GnomeDesktop', '4.0')  # noqa: E402
gi.require_version('GWeather', '4.0')      # noqa: E402
gi.require_version('Adw', '1')             # noqa: E402
gi.require_version('Vte', '3.91')          # noqa: E402
from gi.repository import Adw, Gio, GLib, Gtk

# local, import order is important
from .config import config
from .preload_manager import preload_manager
from .window import OsInstallerWindow

APP_ID = 'com.github.p3732.OS-Installer'


class Application(Adw.Application):
    window = None

    def __init__(self, version):
        super().__init__(application_id=APP_ID,
                         flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE)

        # Connect app shutdown signal
        self.connect('shutdown', self._on_quit)

        # Additional command line options
        self.add_main_option('demo-mode', b'd', GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Run in demo mode. Does not alter the system", None)
        self.add_main_option('test-mode', b't', GLib.OptionFlags.NONE,
                             GLib.OptionArg.NONE, "Run in testing mode. Does not alter the system, but runs scripts.", None)

        config.set('version', version)
        config.set('send_notification', None)
        config.subscribe('send_notification', self._send_notification)

    def _setup_icons(self):
        icon_theme = Gtk.IconTheme.get_for_display(self.window.get_display())
        icon_theme.add_resource_path('/com/github/p3732/os-installer/')
        icon_theme.add_resource_path('/com/github/p3732/os-installer/icon')

    ### parent functions ###

    def do_activate(self):
        preload_manager.start()
        # create window if not existing
        if window := self.props.active_window:
            window.present()
        else:
            self.window = OsInstallerWindow(application=self)
            self._setup_icons()
            self.window.present()

    def do_command_line(self, command_line):
        options = command_line.get_options_dict()
        options = options.end().unpack()

        if 'demo-mode' in options:
            if 'test-mode' in options:
                print("Only one of demo and test mode can be set at a time! "
                      "Using demo mode.")
            config.set('demo_mode', True)
        elif 'test-mode' in options:
            config.set('test_mode', True)

        self.activate()
        return 0

    def do_startup(self):
        # Startup application
        self.set_resource_base_path('/com/github/p3732/os-installer')
        Adw.Application.do_startup(self)

    ### callbacks ###

    def _on_quit(self, action, param=None):
        self.window.close()
        return True

    def _send_notification(self, title):
        if not title:
            return
        n = Gio.Notification()
        n.set_title(title)
        self.send_notification(APP_ID, n)


def main(version):
    app = Application(version)
    return app.run(sys.argv)

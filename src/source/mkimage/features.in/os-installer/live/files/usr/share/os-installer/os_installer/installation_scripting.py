# SPDX-License-Identifier: GPL-3.0-or-later

from locale import gettext as _
from threading import Lock
import os

from gi.repository import Gio, GLib, Vte

from .config import config
from .envvar_creator import create_envs
from .installation_step import InstallationStep


class InstallationScripting():
    '''
    Handles all calls to scripts for installation. The installation process consists of 3 steps:
    * Preparation. Used e.g. for updating mirrors.
    * Installation. Installs an OS onto a disk.
    * Configuration. Configures an OS according to user's choices.
    '''

    def __init__(self):
        self.terminal = self._setup_terminal()
        self.cancel = Gio.Cancellable()

        self.lock = Lock()
        self.ready_step = InstallationStep.none
        self.running_step = InstallationStep.none
        self.finished_step = InstallationStep.none

    def _setup_terminal(self):
        terminal = Vte.Terminal()
        terminal.set_input_enabled(False)
        terminal.set_scroll_on_output(True)
        terminal.set_hexpand(True)
        terminal.set_vexpand(True)
        terminal.connect('child-exited', self._on_child_exited)
        return terminal

    def _fail_installation(self):
        config.set('installation_running', False)
        config.set('displayed-page', 'failed')
        # Translators: Notification text
        config.set('send_notification', _("Finished Installation"))

    def _try_start_next_script(self):
        if self.running_step != InstallationStep.none:
            return

        if self.finished_step.value >= self.ready_step.value:
            return

        next_step = InstallationStep(self.finished_step.value + 1)
        print(f'Starting step "{next_step.name}"...')
        if next_step != InstallationStep.prepare:
            config.set('installation_running', True)

        envs = create_envs(next_step)

        # start script
        file_name = f'/etc/os-installer/scripts/{next_step.name}.sh'
        if os.path.exists(file_name):
            started_script, _ = self.terminal.spawn_sync(
                Vte.PtyFlags.DEFAULT, '/', ['sh', file_name],
                envs, GLib.SpawnFlags.DEFAULT, None, None, self.cancel)
            if not started_script:
                print(f'Could not start {self.finished_step.name} script! '
                      'Ignoring.')
                self._try_start_next_script()
            else:
                self.running_step = next_step
        else:
            print(f'No script for step {next_step.name} exists.')
            self.finished_step = next_step
            self._try_start_next_script()

    ### callbacks ###

    def _on_child_exited(self, terminal, status):
        with self.lock:
            self.finished_step = self.running_step
            self.running_step = InstallationStep.none

            if not status == 0 and not config.get('demo_mode'):
                print(f'Failure during step "{self.finished_step.name}"')
                self._fail_installation()
                return

            print(f'Finished step "{self.finished_step.name}".')

            if self.finished_step is InstallationStep.configure:
                config.set('installation_running', False)
                # Translators: Notification text
                config.set('send_notification', _("Finished Installation"))
                config.set_next_page(None)
            else:
                self._try_start_next_script()

    def _set_ok_to_start_step(self, step: InstallationStep):
        with self.lock:
            if self.ready_step.value < step.value:
                self.ready_step = step
                self._try_start_next_script()

    ### public methods ###

    def can_run_configure(self):
        self._set_ok_to_start_step(InstallationStep.configure)

    def can_run_install(self):
        self._set_ok_to_start_step(InstallationStep.install)

    def can_run_prepare(self):
        self._set_ok_to_start_step(InstallationStep.prepare)


installation_scripting = InstallationScripting()

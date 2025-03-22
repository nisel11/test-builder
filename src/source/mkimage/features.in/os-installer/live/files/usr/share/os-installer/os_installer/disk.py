# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, Gtk

from .config import config
from .disk_provider import DeviceInfo, disk_provider
from .system_calls import open_disks
from .widgets import reset_model, DeviceRow


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/disk.ui')
class DiskPage(Gtk.Stack):
    __gtype_name__ = __qualname__

    disk_list = Gtk.Template.Child()

    disk_list_model = Gio.ListStore()

    def __init__(self, **kwargs):
        Gtk.Stack.__init__(self, **kwargs)

        self.minimum_disk_size = config.get('minimum_disk_size')

        # models
        self.disk_list.bind_model(
            self.disk_list_model, self._create_device_row)

        if disks := disk_provider.get_disks():
            reset_model(self.disk_list_model, disks)
            self.set_visible_child_name('disks')
        else:
            self.set_visible_child_name('no-disks')

    def _create_device_row(self, info: DeviceInfo):
        if info.size <= 0 or info.size >= self.minimum_disk_size:
            return DeviceRow(info)
        else:
            required_size_str = disk_provider.disk_size_to_str(
                self.minimum_disk_size)
            return DeviceRow(info, required_size_str)

    ### callbacks ###

    @Gtk.Template.Callback('clicked_disks_button')
    def _clicked_disks_button(self, button):
        open_disks()

    @Gtk.Template.Callback('disk_selected')
    def _disk_selected(self, list_box, row):
        config.set('selected_disk', row.info)
        config.set_next_page(self)

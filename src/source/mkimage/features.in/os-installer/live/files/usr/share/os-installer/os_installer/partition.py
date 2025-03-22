# SPDX-License-Identifier: GPL-3.0-or-later

from random import getrandbits

from gi.repository import Gio, Gtk

from .config import config
from .disk_provider import disk_provider
from .system_calls import is_booted_with_uefi
from .widgets import reset_model, DeviceRow


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/partition.ui')
class PartitionPage(Gtk.Stack):
    __gtype_name__ = __qualname__

    disk_size = Gtk.Template.Child()

    whole_disk_row = Gtk.Template.Child()
    partition_stack = Gtk.Template.Child()
    partition_list = Gtk.Template.Child()

    disk_list_model = Gio.ListStore()
    partition_list_model = Gio.ListStore()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.disk = None
        self.minimum_disk_size = config.get('minimum_disk_size')
        self.set_visible_child_name("default")

        # models
        self.partition_list.bind_model(
            self.partition_list_model, self._create_device_row)

        config.subscribe('selected_disk', self._setup_partition_list)

    def _create_device_row(self, info):
        if info.size >= self.minimum_disk_size:
            return DeviceRow(info)
        else:
            required_size_str = disk_provider.disk_size_to_str(
                self.minimum_disk_size)
            return DeviceRow(info, required_size_str)

    def disk_exists(self, disk):
        if config.get('demo_mode'):
            return True
        elif config.get('test_mode'):
            # claim disk existance in about 75% of cases
            claim_existance = getrandbits(2) != 3
            if not claim_existance:
                print('test-mode: randomly chose that disk does not exist anymore')
            return claim_existance
        else:
            return disk_provider.disk_exists(disk)

    def _setup_partition_list(self, selected_disk):
        if not self.disk_exists(selected_disk):
            self.set_visible_child_name("no-disk")
            return

        if not selected_disk.partitions:
            reset_model(self.partition_list_model, [])
            self.partition_stack.set_visible_child_name("no-partitions")
        elif is_booted_with_uefi() and selected_disk.efi_partition is None:
            self.partition_stack.set_visible_child_name("no-boot-partition")
        else:
            reset_model(self.partition_list_model, selected_disk.partitions)
            self.partition_stack.set_visible_child_name("available")

        # set disk info
        self.whole_disk_row.set_subtitle(selected_disk.device_path)
        self.disk_size.set_label(selected_disk.size_text)
        self.disk = selected_disk

    def _store_device_info(self, info):
        config.set('disk', (info.device_path, info.name))
        config.set('disk_is_partition', not type(info) == type(self.disk))
        config.set('disk_efi_partition', self.disk.efi_partition)

    ### callbacks ###

    @Gtk.Template.Callback('use_partition')
    def _use_partition(self, list_box, row):
        info = row.info
        if not info.name:
            info.name = row.get_title()
        self._store_device_info(info)
        config.set_next_page(self)

    @Gtk.Template.Callback('use_whole_disk')
    def _use_whole_disk(self, list_box, row):
        self._store_device_info(self.disk)
        config.set_next_page(self)

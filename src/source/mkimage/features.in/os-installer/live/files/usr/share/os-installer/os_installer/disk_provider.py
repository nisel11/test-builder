# SPDX-License-Identifier: GPL-3.0-or-later

from random import getrandbits

from gi.repository import GLib, GObject

from .config import config
from .preloadable import Preloadable


class DeviceInfo(GObject.Object):
    __gtype_name__ = __qualname__

    name: str = None
    size: int
    size_text: str
    device_path: str
    is_efi: bool

    def __init__(self, name, size, size_text, device_path, is_efi=False):
        super().__init__()

        if name:
            self.name = name.strip()
        self.size = size
        self.size_text = size_text
        self.device_path = device_path
        self.is_efi = is_efi


class Disk(DeviceInfo):
    partitions: list = []
    efi_partition: str = ''

    def __init__(self, name, size, size_text, device_path, partitions):
        super().__init__(name, size, size_text, device_path)

        if partitions:
            self.partitions = partitions
            efis = [partition for partition in partitions if partition.is_efi]
            efi_partition = efis[0].name if len(efis) > 0 else ''


class DiskProvider(Preloadable):

    EFI_PARTITION_GUID = 'C12A7328-F81F-11D2-BA4B-00A0C93EC93B'
    EFI_PARTITON_FLAGS = None

    def __init__(self):
        Preloadable.__init__(self, self._init_client)

    def _init_client(self):
        # avoids initializing udisks client in demo mode
        self.use_dummy_implementation = config.get('demo_mode')
        if self.use_dummy_implementation:
            return

        import gi                            # noqa: E402
        gi.require_version('UDisks', '2.0')  # noqa: E402
        from gi.repository import UDisks
        self.EFI_PARTITON_FLAGS = UDisks.PartitionTypeInfoFlags.SYSTEM.numerator
        self.udisks_client = UDisks.Client.new_sync()

    def _get_one_partition(self, partition, block):
        # partition info
        partition_info = DeviceInfo(
            name=block.props.id_label,
            size=block.props.size,
            size_text=self.disk_size_to_str(block.props.size),
            device_path=block.props.device,
            is_efi=partition.props.type.upper() == self.EFI_PARTITION_GUID)

        # add to disk info
        return partition_info

    def _get_partitions(self, partition_table):
        if not partition_table:
            return None

        partitions = []
        for partition_name in partition_table.props.partitions:
            partition_object = self.udisks_client.get_object(partition_name)
            if not partition_object:
                continue
            block = partition_object.get_block()
            partition = partition_object.get_partition()
            if block and partition:
                partitions.append(self._get_one_partition(partition, block))
            else:
                print('Unhandled partiton in partition table, ignoring.')

        return partitions

    def _get_disk_info(self, block, drive, partition_table):
        # disk info
        disk = Disk(
            name=(drive.props.vendor + ' ' + drive.props.model).strip(),
            size=block.props.size,
            size_text=self.disk_size_to_str(block.props.size),
            device_path=block.props.device,
            partitions=self._get_partitions(partition_table))

        return disk

    def _get_dummy_disks(self):
        return [
            Disk("Dummy", 10000, "10 KB", "/dev/null",
                 [DeviceInfo("Too small partiton", 1000, "1 KB", "/dev/00null")]),
            Disk("Totally real device", 100000000000, "100 GB", "/dev/sda", [
                DeviceInfo("EFI", 200000000, "2 GB", "/dev/sda_efi", True),
                DeviceInfo("Previous Installation", 20000000000, "40 GB",
                           "/dev/sda_yes"),
                DeviceInfo(None, 20000000000, "30 GB", "/dev/sda_unnamed"),
                DeviceInfo(None, 20000000000, "20 GB", "/dev/sda_unnamed2"),
                DeviceInfo("Swap", 20000000000, "8 GB", '/dev/sda_swap'),
            ]),
            Disk("VERY BIG DISK", 1000000000000000, "1000 TB",
                 "/dev/sdb_very_big", []),
        ]

    ### public methods ###

    def disk_exists(self, dev_info: DeviceInfo):
        self.assert_preloaded()

        if self.use_dummy_implementation:
            return True

        # check against all available devices
        dummy_var = GLib.Variant('a{sv}', None)
        manager = self.udisks_client.get_manager()
        devices = manager.call_get_block_devices_sync(dummy_var, None)
        for device in devices:
            if ((udisks_object := self.udisks_client.get_object(device)) and
                (block := udisks_object.get_block()) and
                    block.props.device == dev_info.device_path):
                return True

        return False

    def disk_size_to_str(self, size):
        self.assert_preloaded()

        if self.use_dummy_implementation:
            # fake it till you make it
            return f"{size / 1000000000:.1f} GB"

        return self.udisks_client.get_size_for_display(size, False, False)

    def get_disks(self):
        self.assert_preloaded()

        if self.use_dummy_implementation:
            return self._get_dummy_disks()

        if config.get('test_mode') and getrandbits(3) == 7:
            print("test-mode: randomly chose that no disks are available")
            return []

        # get available devices
        dummy_var = GLib.Variant('a{sv}', None)
        manager = self.udisks_client.get_manager()
        devices = manager.call_get_block_devices_sync(dummy_var, None)

        # get device information
        disks = []
        for device in devices:
            udisks_object = self.udisks_client.get_object(device)
            if not udisks_object:
                continue

            # skip partitions
            partition = udisks_object.get_partition()
            if partition:
                continue

            block = udisks_object.get_block()
            if not block:
                continue

            partition_table = udisks_object.get_partition_table()
            drive = self.udisks_client.get_drive_for_block(block)
            if drive and not drive.props.optical:
                disk_info = self._get_disk_info(block, drive, partition_table)
                disks.append(disk_info)

        return disks


disk_provider = DiskProvider()

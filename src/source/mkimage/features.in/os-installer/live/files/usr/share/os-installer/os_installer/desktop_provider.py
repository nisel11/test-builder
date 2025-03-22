# SPDX-License-Identifier: GPL-3.0-or-later

from typing import NamedTuple
import os

from gi.repository import Gdk

from .config import config
from .preloadable import Preloadable


class Desktop(NamedTuple):
    name: str
    description: str
    texture: str
    keyword: str


class DesktopProvider(Preloadable):
    def __init__(self):
        Preloadable.__init__(self, self._get_desktops)

    def _get_desktops(self):
        self.desktops: list = []
        for entry in config.get('desktop'):
            if not set(entry).issuperset(['name', 'keyword', 'image_path']):
                print(f'Desktop choice not correctly configured: {entry}')
                continue
            description = entry.get('description', '')
            image_path = entry['image_path']

            if not os.path.exists(image_path):
                print(f'Could not find desktop image "{image_path}"')
                continue
            texture = Gdk.Texture.new_from_filename(image_path)
            desktop = Desktop(entry['name'], description,
                              texture, entry['keyword'])
            self.desktops.append(desktop)

    ### public methods ###

    def get_desktops(self):
        self.assert_preloaded()
        return self.desktops


desktop_provider = DesktopProvider()

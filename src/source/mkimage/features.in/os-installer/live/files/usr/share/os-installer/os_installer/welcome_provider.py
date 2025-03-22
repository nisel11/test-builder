# SPDX-License-Identifier: GPL-3.0-or-later

import os

from gi.repository import Gdk

from .config import config
from .preloadable import Preloadable


class WelcomeProvider(Preloadable):
    def __init__(self):
        Preloadable.__init__(self, self._load_image)

    def _load_image(self):
        welcome = config.get('welcome_page')

        if logo := welcome['logo']:
            if os.path.exists(logo):
                texture = Gdk.Texture.new_from_filename(logo)
                config.set('welcome_page_image', texture)
            else:
                print(f'Could not find welcome logo "{logo}"')



welcome_provider = WelcomeProvider()

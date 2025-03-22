# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Thread

from .config import config

from .choices_provider import choices_provider
from .desktop_provider import desktop_provider
from .disk_provider import disk_provider
from .format_provider import format_provider
from .internet_provider import internet_provider
from .language_provider import language_provider
from .timezone_provider import timezone_provider
from .welcome_provider import welcome_provider

providers = [language_provider, welcome_provider, internet_provider, disk_provider,
             desktop_provider, format_provider, timezone_provider, choices_provider]


class PreloadManager:
    def __init__(self):
        self.thread = Thread(target=self._preload)

    def _preload(self):
        for provider in providers:
            provider.preload()

        # in testing mode locale might not get set, update it here
        if config.get('test_mode'):
            config.set('locale', config.get('locale'))

        for provider in providers:
            provider.assert_preloaded()

    ### public methods ###

    def start(self):
        self.thread.start()


preload_manager = PreloadManager()

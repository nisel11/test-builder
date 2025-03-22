# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Thread
from time import sleep
from urllib.request import urlopen

from .config import config
from .preloadable import Preloadable


class InternetProvider(Preloadable):
    def __init__(self):
        Preloadable.__init__(self, self._run_connection_checker)

    def _run_connection_checker(self):
        Thread(target=self._check_connection, daemon=True).start()

    def _check_connection(self):
        url = config.get('internet_checker_url')

        while not config.get('installation_running'):
            try:
                urlopen(url, timeout=50)
                config.set('internet_connection', True)
            except:
                config.set('internet_connection', False)
            sleep(1)


internet_provider = InternetProvider()

# SPDX-License-Identifier: GPL-3.0-or-later

from concurrent.futures import ThreadPoolExecutor
from threading import Lock

from .config import config


class Preloadable:
    # static thread pool
    thread_pool = ThreadPoolExecutor()

    def __init__(self, preload_func, config_var=None):
        self.preload_func = preload_func
        self.config_var = config_var
        self.preload_started = False
        self.preloaded = False
        self.preloading_lock = Lock()

    ### public methods ###

    def assert_preloaded(self):
        with self.preloading_lock:
            if self.preloaded:
                return

            if not self.preload_started:
                class_name = self.__class__.__name__
                print(f'Preloading for {class_name} was never started')
                self.preloading_lock.release()
                self.preload()
                self.preloading_lock.acquire()

            # await result
            self.future.result()
            self.preloaded = True

    def preload(self):
        with self.preloading_lock:
            if self.config_var:
                self.preloaded = True
                config.subscribe(
                    self.config_var, self.dependent_preload, delayed=True)
            else:
                if self.preload_started:
                    return
                self.future = self.thread_pool.submit(self.preload_func)
                self.preload_started = True

    def dependent_preload(self, value):
        with self.preloading_lock:
            self.preloaded = False
            self.future = self.thread_pool.submit(self.preload_func, value)
            self.preload_started = True

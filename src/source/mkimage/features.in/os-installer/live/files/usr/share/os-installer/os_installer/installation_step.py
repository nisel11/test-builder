# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum


class InstallationStep(Enum):
    none = 0
    prepare = 1
    install = 2
    configure = 3
    done = 4

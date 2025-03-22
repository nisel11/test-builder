# SPDX-License-Identifier: GPL-3.0-or-later

import re

from gi.repository import GLib, Gtk

from .config import config
from .installation_step import InstallationStep


def _get(var):
    if not config.has(var) and not config.get('test_mode'):
        print(f'Required variable {var} not set, using empty string fallback. '
              'Please report this error.')
        return ''
    else:
        value = config.get(var)
        if isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, tuple):
            return value[0]
        else:
            return value


def _get_username():
    if config.has('user_username'):
        return config.get('user_username')
    else:
        # This sticks to common linux username rules:
        # * starts with a lowercase letter
        # * only lowercase letters, numbers, underscore (_), and dash (-)
        # If the generation fails, a fallback is used.
        asciified = GLib.str_to_ascii(config.get('user_name')).lower()
        filtered = re.sub(r'[^a-z0-9-_]+', '', asciified)
        if (position := re.search(r'[a-z]', filtered)) is None:
            return 'user'
        return filtered[position.start():]


def _parse_choices(choices_var):
    keywords = []
    for choice in _get(choices_var):
        if choice.options:
            keywords.append(choice.state.keyword)
        elif choice.state:
            keywords.append(choice.keyword)
    return ' '.join(keywords)


def create_envs(installation_step: InstallationStep):
    with_configure_envs = installation_step is InstallationStep.configure
    with_install_envs = installation_step is InstallationStep.install or with_configure_envs

    envs = []
    if with_install_envs:
        envs += [
            f'OSI_DESKTOP={_get("desktop_chosen")}',
            f'OSI_LOCALE={_get("locale")}',
            f'OSI_KEYBOARD_LAYOUT={_get("keyboard_layout")}',
            f'OSI_DEVICE_PATH={_get("disk")}',
            f'OSI_DEVICE_IS_PARTITION={_get("disk_is_partition")}',
            f'OSI_DEVICE_EFI_PARTITION={_get("disk_efi_partition")}',
            f'OSI_USE_ENCRYPTION={_get("use_encryption")}',
            f'OSI_ENCRYPTION_PIN={_get("encryption_pin")}',
        ]

    if with_configure_envs:
        envs += [
            f'OSI_USER_NAME={_get("user_name")}',
            f'OSI_USER_USERNAME={_get("user_username")}',
            f'OSI_USER_AUTOLOGIN={_get("user_autologin")}',
            f'OSI_USER_PASSWORD={_get("user_password")}',
            f'OSI_FORMATS={_get("formats")}',
            f'OSI_TIMEZONE={_get("timezone")}',
            f'OSI_ADDITIONAL_SOFTWARE={_parse_choices("software_choices")}',
            f'OSI_ADDITIONAL_FEATURES={_parse_choices("feature_choices")}',
        ]
    return envs + [None]

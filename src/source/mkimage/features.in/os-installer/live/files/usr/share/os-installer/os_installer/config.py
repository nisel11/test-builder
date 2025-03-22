# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Lock
import yaml

DEFAULT_CONFIG_PATH = '/etc/os-installer/config.yaml'


default_config = {
    # general
    'distribution_name': 'Untitled',
    'demo_mode': False,
    'test_mode': False,
    # internet
    'internet_connection_required': True,
    'internet_checker_url': 'http://nmcheck.gnome.org/check_network_status.txt',
    # language
    'suggested_languages': ['en', 'ar', 'de', 'es', 'fr', 'ja', 'ru', 'zh'],
    'fixed_language': False,
    # welcome
    'welcome_page': {'usage': True, 'logo': None, 'text': None},
    # disk
    'minimum_disk_size': 5,
    'disk_encryption': {'offered': True, 'forced': False, 'min_length': 1, 'confirmation': False},
    # desktop
    'desktop': [],
    # user
    'user': {'min_password_length': 1, 'request_username': False, 'provide_autologin': False, 'password_confirmation': False},
    # optional pages
    'skip_user': False,
    'skip_locale': False,
    # software
    'additional_software': [],
    # feature
    'additional_features': [],
    # fail
    'failure_help_url': 'https://duckduckgo.com/?q="os-installer {}"+"failed installation"',
    # commands
    'browser_cmd': 'epiphany',
    'disks_cmd': 'gnome-disks',
    'wifi_cmd': 'gnome-control-center wifi',
}

legacy_values = {
    'offer_disk_encryption': ('disk_encryption',
                              True,
                              {'offered': True, 'forced': False, 'min_length': 1, 'confirmation': False},
                              {'offered': False, 'forced': False, 'min_length': 1, 'confirmation': False}),
}

# not configurable via config file
internal_values = {
    'installation_running': False,
    'internet_connection': False,
    'use_encryption': False,
    'encryption_pin': '',
    'desktop_chosen': '',
    'user_name': '',
    'user_username': '',
    'user_autologin': False,
    'user_password': '',
    'formats': ('en_US.UTF-8', 'United States'),
    'timezone': 'UTC',
    'feature_choices': {},
    'software_choices': {},
    'version': -1,
}

fallback_values = {
    'language': ('en_US', 'English for Dummies'),
    'locale': 'en_US.UTF-8',
    'keyboard_language': ('en_US' 'English (US)'),
    'keyboard_layout': ('us', 'English (US)'),
    'disk': ('/dev/null', 'Test Dummy'),
    'disk_is_partition': False,
    'disk_efi_partition': '/dev/null',
    'selected_disk': 'Unknown',
}


def _match(variables, var, *ok_types):
    if not var in variables:
        print(f'Config error: {var} does not exist.')
        return False
    elif type(variables[var]) not in ok_types:
        print(f'Config error: {var} not of expected type (expected ',
              f'{ok_types}, but got {type(variables[var])})')
        return False
    else:
        return True


def _validate(variables):
    assert not variables['fixed_language'] == True, 'Need to specify or disable fixed language.'

    return (
        _match(variables, 'welcome_page', dict) and
        _match(variables['welcome_page'], 'usage', bool) and
        _match(variables['welcome_page'], 'logo', str, type(None)) and
        _match(variables['welcome_page'], 'text', str, type(None)) and
        _match(variables, 'internet_connection_required', bool) and
        _match(variables, 'internet_checker_url', str) and
        _match(variables, 'suggested_languages', list) and
        _match(variables, 'minimum_disk_size', int) and
        _match(variables, 'disk_encryption', dict) and
        _match(variables['disk_encryption'], 'offered', bool) and
        _match(variables['disk_encryption'], 'forced', bool) and
        _match(variables['disk_encryption'], 'min_length', int) and
        _match(variables['disk_encryption'], 'confirmation', bool) and
        _match(variables, 'user', dict) and
        _match(variables['user'], 'min_password_length', int) and
        _match(variables['user'], 'request_username', bool) and
        _match(variables['user'], 'provide_autologin', bool) and
        _match(variables['user'], 'password_confirmation', bool) and
        _match(variables, 'additional_software', list) and
        _match(variables, 'additional_features', list) and
        _match(variables, 'distribution_name', str) and
        _match(variables, 'fixed_language', bool, str))


class Config:
    def __init__(self):
        self.variables = default_config
        self.subscription_lock = Lock()
        self.subscriptions = {}

        try:
            with open(DEFAULT_CONFIG_PATH, 'r') as file:
                self._load_from_file(file)
        except Exception as e:
            print(f'Error loading config: {e}. Check if the config contains '
                  'syntax errors.')
            self.variables = default_config
        if not _validate(self.variables):
            print('Config errors, loading default config.')
            self.variables = default_config
        self.variables.update(internal_values)
        self._preprocess_values()

    def _load_from_file(self, file):
        config_from_file = yaml.load(file, Loader=yaml.Loader)
        for config_property in config_from_file:
            if config_property in legacy_values:
                self._handle_legacy(
                    config_property, config_from_file[config_property])
            elif not config_property in default_config:
                print(f'Ignoring unknown config for "{config_property}"')
            elif type(self.variables[config_property]) is dict:
                for key, value in config_from_file[config_property].items():
                    self.variables[config_property][key] = value
            else:
                self.variables[config_property] = config_from_file[config_property]

    def _handle_legacy(self, legacy_prop, legacy_val):
        new_var, compare_val, new1, new2 = legacy_values[legacy_prop]
        print(f'Developer hint: "{legacy_prop}" is deprecated, '
              f'use "{new_var}" instead')
        self.variables[new_var] = new1 if legacy_val == compare_val else new2

    def _preprocess_values(self):
        GIGABYTE_FACTOR = 1000 * 1000 * 1000
        self.variables['minimum_disk_size'] *= GIGABYTE_FACTOR

    def _update_subscribers(self, variable, new_value):
        subscribers = []
        with self.subscription_lock:
            if variable in self.subscriptions:
                subscribers = self.subscriptions[variable]
        for func in subscribers:
            func(new_value)

    ### public methods ###

    def bump(self, variable):
        self._update_subscribers(variable, self.get(variable))

    def get(self, variable):
        if variable in self.variables:
            return self.variables[variable]
        elif variable in fallback_values:
            return fallback_values[variable]
        else:
            print(f'Requested "{variable}" not in config')
            return None

    def has(self, variable):
        return variable in self.variables

    def set(self, variable, new_value):
        '''Returns whether config was changed.'''
        if variable in self.variables and (old_value := self.variables[variable]) == new_value:
            return False

        self.variables[variable] = new_value

        self._update_subscribers(variable, new_value)

        return True

    def set_next_page(self, page):
        '''Convenience function'''
        self.set('displayed-page', ('next', page))

    def steal(self, variable):
        if variable in self.variables:
            return self.variables.pop(variable)

    def subscribe(self, variable, func, delayed=False):
        with self.subscription_lock:
            if variable in self.subscriptions:
                self.subscriptions[variable].append(func)
            else:
                self.subscriptions[variable] = [func]
        if delayed:
            return
        if variable in self.variables:
            func(self.variables[variable])
        elif not self.variables['test_mode']:
            print(f'subscribing to unknown variable {variable}')

    def unsubscribe(self, obj):
        with self.subscription_lock:
            for subs in self.subscriptions.values():
                for func in subs:
                    if func.__self__ == obj:
                        subs.remove(func)


config = Config()

# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import GObject
from typing import NamedTuple

from .config import config
from .preloadable import Preloadable


class Option(NamedTuple):
    display: str
    keyword: str


class Choice(GObject.Object):
    __gtype_name__ = __qualname__

    def __init__(self, name, description, icon_path, suggested=False, keyword=None, options=[]):
        super().__init__()

        self.name = name
        self.description = description
        self.icon_path = icon_path

        self.options = options
        self.state = options[0] if options else suggested
        self.keyword = keyword


def handle_choice(choice):
    name = choice['name']
    description = choice.get('description', '')
    icon_path = choice.get('icon_path', '')

    if 'options' in choice:
        if 'keyword' in choice or 'suggested' in choice:
            print(f'Config of {name}: '
                  "Can't combine 'options' with 'keyword'/'suggested'")
            return None

        options = []
        for option in choice['options']:
            if not 'option' in option:
                print(f'Option for {name} not correctly configured: {option}')
                continue
            option_name = option.get('name', option['option'])
            options.append(Option(option_name, option['option']))

        if len(options) == 0:
            print(f'No valid options found for {name}')
            return None
        else:
            return Choice(name, description, icon_path, options=options)
    else:
        if 'keyword' in choice:
            suggested = choice.get('suggested', False)
            return Choice(name, description, icon_path, suggested=suggested, keyword=choice['keyword'])
        else:
            print(f'No keyword found for {name}')
            return None


def handle_legacy(choice):
    if 'package' in choice:
        print("Syntax changed! Use 'keyword' instead of 'package'")
        choice['keyword'] = choice['package']
    if 'feature' in choice:
        print("Syntax changed! Use 'keyword' instead of 'feature'")
        choice['keyword'] = choice['feature']


def handle_choices(config_entries):
    if not config_entries:
        return []

    choices: list = []
    for choice in config_entries:
        handle_legacy(choice)
        if (not 'name' in choice or not
                ('options' in choice or 'keyword' in choice)):
            print(f'Choice not correctly configured: {choice}')
            continue
        if parsed := handle_choice(choice):
            choices.append(parsed)

    return choices


class ChoicesProvider(Preloadable):
    def __init__(self):
        Preloadable.__init__(self, self._get_choices)

    def _get_choices(self):
        feature_choices = handle_choices(config.get('additional_features'))
        for choice in feature_choices:
            choice.icon_name = 'puzzle-piece-symbolic'
        config.set('feature_choices', feature_choices)

        software_choices = handle_choices(config.get('additional_software'))
        for choice in software_choices:
            choice.icon_name = 'system-software-install-symbolic'
        config.set('software_choices', software_choices)

    ### public methods ###

    def get_software_suggestions(self):
        self.assert_preloaded()
        return config.get('software_choices')

    def get_feature_suggestions(self):
        self.assert_preloaded()
        return config.get('feature_choices')


choices_provider = ChoicesProvider()

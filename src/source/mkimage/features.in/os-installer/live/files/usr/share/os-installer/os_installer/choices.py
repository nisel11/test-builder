# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum
from gi.repository import Gio, Gtk

from .choices_provider import choices_provider
from .config import config
from .widgets import MultiSelectionRow, SelectionRow


class ChoiceType(Enum):
    feature = 0
    software = 1


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/choices.ui')
class ChoicesPage(Gtk.Box):
    __gtype_name__ = __qualname__

    list = Gtk.Template.Child()
    model = Gtk.Template.Child()

    def __init__(self, choice_type, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        match choice_type:
            case ChoiceType.feature:
                self.config_key = 'feature_choices'
                self.list_provider = choices_provider.get_feature_suggestions
            case ChoiceType.software:
                self.config_key = 'software_choices'
                self.list_provider = choices_provider.get_software_suggestions
            case _:
                print("Unknown choice type!")
                exit(0)

        self.model.splice(0, 0, self.list_provider())
        self.list.bind_model(self.model, self._create_row)

    def _create_row(self, choice):
        if choice.options:
            row = MultiSelectionRow(choice)
            row.connect("notify::selected-item", self._option_chosen)
        else:
            row = SelectionRow(choice)
            row.connect("activated", self._switch_flipped)
        return row

    ### callbacks ###

    def _option_chosen(self, row, _):
        row.update_choice()
        config.bump(self.config_key)

    def _switch_flipped(self, row):
        row.flip_switch()
        config.bump(self.config_key)

    @Gtk.Template.Callback('continue')
    def _continue(self, button):
        config.set_next_page(self)


FeaturePage = lambda **args: ChoicesPage(ChoiceType.feature, **args)
SoftwarePage = lambda **args: ChoicesPage(ChoiceType.software, **args)

# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gio, Gtk

from .config import config
from .widgets import reset_model, SummaryRow


def _filter_chosen_choices(choices):
    return [choice for choice in choices if choice.options or choice.state]


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/summary.ui')
class SummaryPage(Gtk.Box):
    __gtype_name__ = __qualname__

    # rows
    language_row = Gtk.Template.Child()
    keyboard_row = Gtk.Template.Child()
    user_row = Gtk.Template.Child()
    format_row = Gtk.Template.Child()
    timezone_row = Gtk.Template.Child()
    software_row = Gtk.Template.Child()
    feature_row = Gtk.Template.Child()

    # user row specific
    user_autologin = Gtk.Template.Child()

    # software list
    software_stack = Gtk.Template.Child()
    software_list = Gtk.Template.Child()
    software_model = Gio.ListStore()

    # feature list
    feature_stack = Gtk.Template.Child()
    feature_list = Gtk.Template.Child()
    feature_model = Gio.ListStore()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        if not config.get('fixed_language'):
            self.language_row.set_visible(True)
            config.subscribe('language', self._update_language)
        if config.get('additional_features'):
            self.feature_list.bind_model(self.feature_model, SummaryRow)
            self.feature_row.set_visible(True)
            config.subscribe('feature_choices', self._update_feature_choices)
        if config.get('additional_software'):
            self.software_list.bind_model(self.software_model, SummaryRow)
            self.software_row.set_visible(True)
            config.subscribe('software_choices', self._update_software_choices)
        if not config.get('skip_user'):
            self.user_row.set_visible(True)
            config.subscribe('user_autologin', self._update_user_autologin)
            config.subscribe('user_name', self._update_user_name)
        if not config.get('skip_locale'):
            self.format_row.set_visible(True)
            config.subscribe('formats', self._update_formats)
            self.timezone_row.set_visible(True)
            config.subscribe('timezone', self._update_timezone)

        config.subscribe('keyboard_layout', self._update_keyboard_layout)

    ### callbacks ###

    def _update_feature_choices(self, choices):
        if choices:
            self.feature_stack.set_visible_child_name('used')
            reset_model(self.feature_model, _filter_chosen_choices(choices))
        else:
            self.feature_stack.set_visible_child_name('none')

    def _update_formats(self, formats):
        self.format_row.set_subtitle(formats[1])

    def _update_keyboard_layout(self, keyboard_layout):
        _, name = keyboard_layout
        self.keyboard_row.set_subtitle(name)

    def _update_language(self, language):
        _, name = language
        self.language_row.set_subtitle(name)

    def _update_software_choices(self, choices):
        if choices:
            self.software_stack.set_visible_child_name('used')
            reset_model(self.software_model, _filter_chosen_choices(choices))
        else:
            self.software_stack.set_visible_child_name('none')

    def _update_timezone(self, timezone):
        self.timezone_row.set_subtitle(timezone)

    def _update_user_autologin(self, autologin):
        self.user_autologin.set_visible(autologin)

    def _update_user_name(self, user_name):
        self.user_row.set_subtitle(user_name)

    @Gtk.Template.Callback('continue')
    def _continue(self, button):
        config.set_next_page(self)

    @Gtk.Template.Callback('summary_row_activated')
    def _summary_row_activated(self, list_box, row):
        config.set('displayed-page', row.get_name())

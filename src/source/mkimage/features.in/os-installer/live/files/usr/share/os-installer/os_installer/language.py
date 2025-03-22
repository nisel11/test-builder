# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk

from .config import config
from .language_provider import language_provider
from .system_calls import set_system_language
from .widgets import ProgressRow


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/language.ui')
class LanguagePage(Gtk.Box):
    __gtype_name__ = __qualname__

    suggested_list = Gtk.Template.Child()
    suggested_model = Gtk.Template.Child()

    other_list = Gtk.Template.Child()
    other_model = Gtk.Template.Child()

    def __init__(self, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        if suggested_languages := language_provider.get_suggested_languages():
            self.suggested_model.splice(0, 0, suggested_languages)
            self.suggested_list.bind_model(
                self.suggested_model, lambda o: ProgressRow(o.name, o))
        else:
            self.suggested_list.set_visible(False)

        if other_languages := language_provider.get_other_languages():
            self.other_model.splice(0, 0, other_languages)
            self.other_list.bind_model(
                self.other_model, lambda o: ProgressRow(o.name, o))
        else:
            self.other_list.set_visible(False)

    ### callbacks ###

    @Gtk.Template.Callback('language_row_activated')
    def _language_row_activated(self, list_box, row):
        if config.set('language', (row.info.language_code, row.info.name)):
            set_system_language(row.info)
        config.set_next_page(self)

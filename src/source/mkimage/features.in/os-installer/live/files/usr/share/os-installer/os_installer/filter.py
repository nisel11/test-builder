# SPDX-License-Identifier: GPL-3.0-or-later

from enum import Enum
from gi.repository import Gtk

from .config import config
from .format_provider import format_provider
from .system_calls import set_system_formats, set_system_timezone
from .timezone_provider import timezone_provider
from .widgets import ProgressRow


class FilterType(Enum):
    format = 0
    timezone = 1


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/pages/filter.ui')
class FilterPage(Gtk.Box):
    __gtype_name__ = __qualname__

    search_entry = Gtk.Template.Child()
    custom_filter = Gtk.Template.Child()
    filter_list_model = Gtk.Template.Child()

    stack = Gtk.Template.Child()
    list = Gtk.Template.Child()
    list_model = Gtk.Template.Child()

    def __init__(self, filter_type, **kwargs):
        Gtk.Box.__init__(self, **kwargs)

        self.type = filter_type
        match self.type:
            case FilterType.format:
                self.filter = self._format_filter
                self.list_model.splice(0, 0, format_provider.get_formats())
            case FilterType.timezone:
                self.filter = self._timezone_filter
                self.list_model.splice(0, 0, timezone_provider.get_timezones())

        self.search_entry.connect("search-changed", self._filter)

        self.list.bind_model(
            self.filter_list_model, lambda f: ProgressRow(f.name))

    def _filter(self, *args):
        self.search_text = self.search_entry.get_text().lower()
        self.custom_filter.set_filter_func(self.filter)

        if self.filter_list_model.get_n_items() > 0:
            self.stack.set_visible_child_name('list')
        else:
            self.stack.set_visible_child_name('none')

    def _format_filter(self, format):
        return self.search_text in format.lower_case_name or format.locale.startswith(self.search_text)

    def _timezone_filter(self, timezone):
        if self.search_text in timezone.lower_case_name:
            return True
        for location in timezone.locations:
            if self.search_text in location:
                return True
        return False

    ### callbacks ###

    @Gtk.Template.Callback('row_selected')
    def _row_selected(self, list_box, row):
        match self.type:
            case FilterType.format:
                set_system_formats(row.info, row.get_title())
            case FilterType.timezone:
                set_system_timezone(row.get_title())
        config.set_next_page(self)


FormatPage = lambda **args: FilterPage(FilterType.format, **args)
TimezonePage = lambda **args: FilterPage(FilterType.timezone, **args)

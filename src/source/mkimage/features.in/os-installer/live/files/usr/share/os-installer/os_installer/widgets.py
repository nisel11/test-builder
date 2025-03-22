# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Adw, Gtk


def reset_model(model, new_values):
    '''
    Reset given model to contain the passed new values.
    (Convenience wrapper)
    '''
    n_prev_items = model.get_n_items()
    model.splice(0, n_prev_items, new_values)


class EntryErrorEnhancer():
    def __init__(self, row, condition):
        self.row = row
        self.condition = condition
        self.error = None

        self.update_row(self.row.get_text())

    def __bool__(self):
        return self.ok

    def update_row(self, text):
        self.empty = len(text) == 0
        self.ok = self.condition(text)

        if self.error and (self.empty or self.ok):
            self.row.remove_css_class('error')
            self.row.remove(self.error)
            del self.error
            self.error = None
        elif not self.error and not self.empty and not self.ok:
            self.row.add_css_class('error')
            self.error = Gtk.Image.new_from_icon_name(
                'dialog-warning-symbolic')
            self.row.add_suffix(self.error)
        return bool(self)


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/widgets/desktop_entry.ui')
class DesktopEntry(Gtk.Button):
    __gtype_name__ = __qualname__

    image = Gtk.Template.Child()
    name = Gtk.Template.Child()

    def __init__(self, desktop, **kwargs):
        super().__init__(**kwargs)

        self.desktop = desktop
        self.name.set_label(desktop.name)
        self.image.set_paintable(desktop.texture)


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/widgets/device_row.ui')
class DeviceRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    stack = Gtk.Template.Child()
    size_label = Gtk.Template.Child()
    too_small_label = Gtk.Template.Child()

    def __init__(self, info, required_size_str=None, **kwargs):
        super().__init__(**kwargs)

        self.info = info
        self.size_label.set_label(info.size_text)
        if info.name:
            self.set_title(info.name)

        self.set_subtitle(info.device_path)

        if required_size_str:
            smol = self.too_small_label.get_label()
            self.too_small_label.set_label(smol.format(required_size_str))
            self.set_activatable(False)
            self.set_sensitive(False)
            self.stack.set_visible_child_name('too_small')


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/widgets/multi_selection_row.ui')
class MultiSelectionRow(Adw.ComboRow):
    __gtype_name__ = __qualname__

    icon = Gtk.Template.Child()
    list = Gtk.Template.Child()

    def __init__(self, choice, **kwargs):
        super().__init__(**kwargs)

        self.choice = choice

        self.set_title(choice.name)
        self.set_subtitle(choice.description)
        if choice.icon_path:
            self.icon.set_from_file(choice.icon_path)
        else:
            self.icon.set_from_icon_name(choice.icon_name)
            self.icon.set_icon_size(Gtk.IconSize.LARGE)

        self.list.splice(0, 0, [option.display for option in choice.options])
        self.set_model(self.list)
        self.update_choice()

    def get_chosen_option(self):
        return self.choice.options[self.get_selected()]

    def update_choice(self):
        display_text = self.get_selected_item().get_string()
        for index, option in enumerate(self.choice.options):
            if option.display == display_text:
                self.set_selected(index)
                self.choice.state = option
                return


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/widgets/progress_row.ui')
class ProgressRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    def __init__(self, label, additional_info=None, **kwargs):
        super().__init__(**kwargs)

        self.set_title(label)
        self.info = additional_info


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/widgets/selection_row.ui')
class SelectionRow(Adw.ActionRow):
    __gtype_name__ = __qualname__

    icon = Gtk.Template.Child()
    switch = Gtk.Template.Child()

    def __init__(self, choice, **kwargs):
        super().__init__(**kwargs)

        self.choice = choice

        self.set_title(choice.name)
        self.set_subtitle(choice.description)
        self.switch.set_active(choice.state)
        if choice.icon_path:
            self.icon.set_from_file(choice.icon_path)
        else:
            self.icon.set_from_icon_name(choice.icon_name)
            self.icon.set_icon_size(Gtk.IconSize.LARGE)

    def is_activated(self):
        return self.switch.get_active()

    def flip_switch(self):
        new_state = not self.switch.get_active()
        self.switch.set_active(new_state)
        self.choice.state = new_state


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/widgets/summary_row.ui')
class SummaryRow(Gtk.ListBoxRow):
    __gtype_name__ = __qualname__

    icon = Gtk.Template.Child()
    name = Gtk.Template.Child()

    def __init__(self, choice, **kwargs):
        super().__init__(**kwargs)

        if choice.options:
            self.name.set_label(choice.state.display)
        else:
            self.name.set_label(choice.name)

        if choice.icon_path:
            self.icon.set_from_file(choice.icon_path)
        else:
            self.icon.set_from_icon_name(choice.icon_name)

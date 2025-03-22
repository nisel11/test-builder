# SPDX-License-Identifier: GPL-3.0-or-later

from threading import Lock
from os.path import exists

from gi.repository import Gio, Gtk, Adw

from .config import config
from .language_provider import language_provider
from .page_wrapper import PageWrapper
from .state_machine import page_order, state_machine
from .system_calls import set_system_language


forward = 1
backwards = -1


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/main_window.ui')
class OsInstallerWindow(Adw.ApplicationWindow):
    __gtype_name__ = __qualname__

    navigation_view = Gtk.Template.Child()

    navigation_lock = Lock()
    pages = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._setup_actions()
        self.connect("close-request", self._show_confirm_dialog, None)

        self._determine_available_pages()
        self._initialize_first_page()
        self.navigation_view.connect('popped', self._popped_page)
        self.navigation_view.connect('pushed', self._pushed_page)
        self.navigation_view.connect('get-next-page', self._add_next_page)

        config.subscribe('displayed-page', self._change_page, delayed=True)

    def _add_next_page(self, _):
        current_page = self.navigation_view.get_visible_page()
        next_index = self.available_pages.index(current_page.get_tag()) + 1
        if next_index >= len(self.available_pages):
            return None
        next_page_name = self.available_pages[next_index]
        return self.navigation_view.find_page(next_page_name)

    def _popped_page(self, _, popped_page):
        if not popped_page.permanent:
            del popped_page
        self._update_page()

    def _pushed_page(self, _):
        self._update_page()

    def _initialize_first_page(self):
        initial_page = PageWrapper(self.available_pages[0])
        initial_page.permanent = True
        self.navigation_view.add(initial_page)

    def _add_action(self, action_name, callback, keybinding):
        action = Gio.SimpleAction.new(action_name, None)
        action.connect('activate', callback)
        self.action_group.add_action(action)

        trigger = Gtk.ShortcutTrigger.parse_string(keybinding)
        named_action = Gtk.NamedAction.new(f'win.{action_name}')
        shortcut = Gtk.Shortcut.new(trigger, named_action)
        self.shortcut_controller.add_shortcut(shortcut)

    def _setup_actions(self):
        self.action_group = Gio.SimpleActionGroup()
        self.shortcut_controller = Gtk.ShortcutController()
        self.shortcut_controller.set_scope(Gtk.ShortcutScope(1))

        self._add_action('next-page', self._navigate_forward, '<Alt>Right')
        self._add_action('previous-page', self._navigate_backward, '<Alt>Left')
        self._add_action('reload-page', self._reload_page, 'F5')
        self._add_action('about-page', self._show_about_page, '<Alt>Return')
        self._add_action('quit', self._show_confirm_dialog, '<Ctl>q')

        if config.get('test_mode'):
            def show_failed(_, __):
                with self.navigation_lock:
                    return self._load_page('failed', permanent=False)
            self._add_action('fail-page', show_failed, '<Alt>F')

            def skip_page(_, __):
                with self.navigation_lock:
                    return self._advance(None)
            self._add_action('skip', skip_page, '<Alt>S')

        self.insert_action_group('win', self.action_group)
        self.add_controller(self.shortcut_controller)

    def _determine_available_pages(self):
        page_conditions = {
            'language': self._offer_language_selection(),
            'welcome': config.get('welcome_page')['usage'],
            'internet': config.get('internet_connection_required'),
            'encrypt': config.get('disk_encryption')['offered'],
            'desktop': config.get('desktop'),
            'confirm': exists('/etc/os-installer/scripts/install.sh'),
            'user': not config.get('skip_user'),
            'locale': not config.get('skip_locale'),
            'software': config.get('additional_software'),
            'feature': config.get('additional_features'),
        }

        self.available_pages = [
            page for page in page_order if page not in page_conditions or page_conditions[page]]

    def _offer_language_selection(self):
        # only initialize language page, others depend on chosen language
        if fixed_language := config.get('fixed_language'):
            if fixed_info := language_provider.get_fixed_language(fixed_language):
                config.set('language',
                           (fixed_info.language_code, fixed_info.name))
                set_system_language(fixed_info)
                return False
            else:
                print('Developer hint: defined fixed language not available')
                config.set('fixed_language', '')
        return True

    def _remove_all_pages(self, exception=None):
        for page_name in self.available_pages:
            if page_name == exception:
                continue
            if page := self.navigation_view.find_page(page_name):
                self.navigation_view.remove(page)
                del page

        replacement = []
        if exception:
            replacement = [self.navigation_view.find_page(exception)]
        self.navigation_view.replace(replacement)

    def _get_next_page_name(self, offset: int = forward):
        current_page = self.navigation_view.get_visible_page()
        current_index = self.available_pages.index(current_page.get_tag())
        return self.available_pages[current_index + offset]

    def _advance(self, page):
        # confirm calling page is current page to prevent incorrect navigation
        current_page = self.navigation_view.get_visible_page()
        if page != None and not current_page.has_same_type(page):
            return

        if not current_page.permanent:
            self.navigation_view.pop()
        else:
            next_page_name = self._get_next_page_name()
            match state_machine.transition(current_page.get_tag(), next_page_name):
                case 'no_return':
                    self._remove_all_pages()
                case 'retranslate':
                    self._remove_all_pages('language')

            self._load_page(next_page_name)

    def _load_page(self, page_name: str, offset: int = forward, permanent: bool = True):
        page_to_load = self.navigation_view.find_page(page_name)
        if not page_to_load:
            page_to_load = PageWrapper(page_name)
            page_to_load.permanent = permanent

            if permanent:
                self.navigation_view.add(page_to_load)
                if self.navigation_view.get_visible_page().get_tag() != page_name:
                    self.navigation_view.push_by_tag(page_name)
            else:
                self.navigation_view.push(page_to_load)
        else:
            # in case page is still in stack, but not in internal list
            if offset >= forward:
                self.navigation_view.push_by_tag(page_name)
            else:
                self.navigation_view.pop_to_tag(page_name)

        self._update_page()

    def _update_page(self):
        current_page = self.navigation_view.get_visible_page()
        is_first, is_last = self._current_is_first(), self._current_is_last()
        current_page.update_navigation_buttons(is_first, is_last)

    def _load_next_page(self, offset: int = forward):
        page_name = self._get_next_page_name(offset)
        self._load_page(page_name, offset)

    def _current_is_first(self):
        return len(self.navigation_view.get_navigation_stack()) == 1

    def _current_is_last(self):
        page = self.navigation_view.get_visible_page()
        if not page.permanent:
            return True
        page_index = self.available_pages.index(page.get_tag())
        if page_index + 1 == len(self.available_pages):
            return True
        next_page_name = self.available_pages[page_index + 1]
        return self.navigation_view.find_page(next_page_name) is None

    ### callbacks ###

    def _change_page(self, value):
        with self.navigation_lock:
            match value := config.steal('displayed-page'):
                case 'next', page:
                    self._advance(page)
                case _:
                    page_name = value
                    assert self.navigation_view.find_page(page_name) is None
                    self._load_page(page_name, permanent=False)

    def _navigate_backward(self, _, __):
        with self.navigation_lock:
            page = self.navigation_view.get_visible_page()
            if not page.permanent:
                self.navigation_view.pop()
            elif not self._current_is_first():
                self._load_next_page(backwards)

    def _navigate_forward(self, _, __):
        with self.navigation_lock:
            if not self._current_is_last():
                self._load_next_page()

    def _reload_page(self, _, __):
        with self.navigation_lock:
            self.navigation_view.get_visible_page().reload()

    def _show_about_page(self, _, __):
        with self.navigation_lock:
            builder = Gtk.Builder.new_from_resource(
                '/com/github/p3732/os-installer/ui/about_dialog.ui')
            popup = builder.get_object('about_window')
            popup.present(self)

    def _show_confirm_dialog(self, _, __):
        def check_quit(_, response, self):
            if response == 'stop':
                self.get_application().quit()

        if not config.get('installation_running'):
            self.get_application().quit()
            return False

        with self.navigation_lock:
            builder = Gtk.Builder.new_from_resource(
                '/com/github/p3732/os-installer/ui/confirm_quit_dialog.ui')
            popup = builder.get_object('popup')
            popup.connect('response', check_quit, self)
            popup.present(self)

        return True

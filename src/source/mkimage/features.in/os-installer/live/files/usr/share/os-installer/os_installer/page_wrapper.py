# SPDX-License-Identifier: GPL-3.0-or-later

from locale import gettext as _
from pathlib import Path

from gi.repository import Adw, Gdk, Gtk

from .config import config

from .choices import FeaturePage, SoftwarePage
from .confirm import ConfirmPage
from .desktop import DesktopPage
from .disk import DiskPage
from .done import DonePage
from .encrypt import EncryptPage
from .failed import FailedPage
from .filter import FormatPage, TimezonePage
from .install import InstallPage
from .internet import InternetPage
from .keyboard import KeyboardLanguagePage, KeyboardLayoutPage, KeyboardOverviewPage
from .language import LanguagePage
from .locale import LocalePage
from .partition import PartitionPage
from .restart import RestartPage
from .summary import SummaryPage
from .user import UserPage
from .welcome import WelcomePage

page_name_to_page_title = {
    # Translators: Page title
    'confirm':              _('Confirmation'),
    # Translators: Page title
    'desktop':              _('Desktop Selection'),
    # Translators: Page title
    'disk':                 _('Disk Selection'),
    # Translators: Page title
    'done':                 _('Installation Complete'),
    # Translators: Page title
    'encrypt':              _('Disk Encryption'),
    # Translators: Page title
    'failed':               _('Installation Failed'),
    # Translators: Page title
    'feature':              _('Additional Features'),
    # Translators: Page title
    'format':               _('Select Region'),
    # Translators: Page title
    'install':              _('Installing'),
    # Translators: Page title
    'internet':             _('Internet Connection Check'),
    # Translators: Page title
    'keyboard-language':    _('Keyboard Language'),
    # Translators: Page title
    'keyboard-layout':      _('Keyboard Layout Selection'),
    # Translators: Page title
    'keyboard-overview':    _('Keyboard Layout'),
    # Language page has no title
    'language':             ' ',
    # Translators: Page title
    'locale':               _('Adapt to Location'),
    # Special-cased: Partition page shows disk name as title
    'partition':            None,
    # Translators: Page title
    'restart':              _('Restarting'),
    # Translators: Page title
    'software':             _('Additional Software'),
    # Translators: Page title
    'summary':              _('Summary'),
    # Translators: Page title
    'timezone':             _('Select Location'),
    # Translators: Page title
    'user':                 _('User Account'),
    # Translators: Page title
    'welcome':              _('Welcome'),
}

page_name_to_image = {
    'confirm':              'question-round-symbolic',
    'desktop':              'computer-symbolic',
    'disk':                 'drive-harddisk-system-symbolic',
    'done':                 'success-symbolic',
    'encrypt':              'dialog-password-symbolic',
    'failed':               'computer-fail-symbolic',
    'feature':              'puzzle-piece-symbolic',
    'format':               'map-symbolic',
    'install':              'OS-Installer-symbolic',
    'keyboard-language':    'input-keyboard-symbolic',
    'keyboard-layout':      'input-keyboard-symbolic',
    'keyboard-overview':    'input-keyboard-symbolic',
    'language':             'language-symbolic',
    'locale':               'globe-symbolic',
    'partition':            'drive-harddisk-system-symbolic',
    'restart':              'system-reboot-symbolic',
    'software':             'system-software-install-symbolic',
    'summary':              'checkbox-checked-symbolic',
    'timezone':             'map-symbolic',
    'user':                 'user-symbolic',
}

special_image_pages = {'internet', 'welcome'}

page_name_to_type = {
    'confirm':              ConfirmPage,
    'desktop':              DesktopPage,
    'disk':                 DiskPage,
    'done':                 DonePage,
    'encrypt':              EncryptPage,
    'failed':               FailedPage,
    'feature':              FeaturePage,
    'format':               FormatPage,
    'install':              InstallPage,
    'internet':             InternetPage,
    'keyboard-language':    KeyboardLanguagePage,
    'keyboard-layout':      KeyboardLayoutPage,
    'keyboard-overview':    KeyboardOverviewPage,
    'language':             LanguagePage,
    'locale':               LocalePage,
    'partition':            PartitionPage,
    'restart':              RestartPage,
    'software':             SoftwarePage,
    'summary':              SummaryPage,
    'timezone':             TimezonePage,
    'user':                 UserPage,
    'welcome':              WelcomePage,
}

reloadable_pages = ['disk', 'partition']


@Gtk.Template(resource_path='/com/github/p3732/os-installer/ui/widgets/page_wrapper.ui')
class PageWrapper(Adw.NavigationPage):
    __gtype_name__ = __qualname__

    previous_button = Gtk.Template.Child()
    next_button = Gtk.Template.Child()
    title_image = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    reload_button = Gtk.Template.Child()

    content = Gtk.Template.Child()

    def __init__(self, page_name, **kwargs):
        super().__init__(**kwargs)
        self._set_new_page(page_name)
        self.reload_button.set_visible(page_name in reloadable_pages)

    def __del__(self):
        config.unsubscribe(self.page)
        del self.page

    def _set_new_page(self, page_name):
        self.page = page_name_to_type[page_name]()
        self.page_name = page_name
        self.content.set_child(self.page)
        if self.page_name in special_image_pages:
            config_value = f'{self.page_name}_page_image'
            config.subscribe(config_value, self._set_title_image)
        else:
            self._set_title_image(page_name_to_image[self.page_name])
        page_title = self._get_page_title()
        self.title_label.set_label(page_title)

        # AdwNavigationPage properties
        self.set_title(page_title)
        self.set_tag(page_name)

    def _get_page_title(self):
        page_title = page_name_to_page_title[self.page_name]
        if page_title == None:
            assert self.page_name == 'partition'
            page_title = config.get('selected_disk').name
        # only translate translatable strings
        elif page_title != ' ':
            page_title = _(page_title)
        return page_title

    def _set_title_image(self, image):
        if isinstance(image, str):
            self.title_image.set_from_icon_name(image)
        elif isinstance(image, Gdk.Texture):
            self.title_image.set_from_paintable(image)
        elif isinstance(image, Path):
            self.title_image.set_from_file(str(image))
        else:
            print('Developer hint: invalid title image')
            assert self.page_name == 'welcome'
            self.title_image.set_from_icon_name('weather-clear-symbolic')

    ### public methods ###

    def has_same_type(self, other_page):
        return type(self.page) == type(other_page)

    def reload(self):
        if not self.page_name in reloadable_pages:
            return
        config.unsubscribe(self.page)
        del self.page
        self._set_new_page(self.page_name)

    def update_navigation_buttons(self, is_first: bool, is_last: bool):
        self.previous_button.set_visible(not is_first)
        self.next_button.set_visible(not is_last)

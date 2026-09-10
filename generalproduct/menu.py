from admin_tools.menu import DefaultMenu, items
from admin_tools.utils import get_admin_site_name
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
class CustomMenu(DefaultMenu):
    def init_with_context(self, context):
        site_name = get_admin_site_name(context)
        self.children = [
            items.MenuItem(_('Dashboard'), reverse(f'{site_name}:index')),
            items.Bookmarks(),
            items.AppList(
                _('Applications'),
                exclude=('django.contrib.*',),
            ),
            items.AppList(
                _('Administration'),
                models=('django.contrib.*',),
            ),
        ]

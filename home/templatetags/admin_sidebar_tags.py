from django import template

from home.models import AdminPinnedApp

register = template.Library()


@register.simple_tag
def is_admin_app_pinned(app_label):
    return AdminPinnedApp.objects.filter(app_label=app_label, is_pinned=True).exists()


@register.simple_tag
def order_admin_apps(app_list):
    pinned = {
        item.app_label: item.order
        for item in AdminPinnedApp.objects.filter(is_pinned=True)
    }
    return sorted(
        app_list,
        key=lambda app: (
            0 if app['app_label'] in pinned else 1,
            pinned.get(app['app_label'], 999999),
            str(app['name']).lower(),
        ),
    )

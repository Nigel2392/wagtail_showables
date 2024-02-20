from wagtail import hooks
from django.urls import path
from django.urls import reverse
from django.utils.html import format_html
from django.templatetags.static import static
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from wagtail.admin.menu import MenuItem

from .views import (
    showables_list,
    showables_edit,
)


@hooks.register("insert_global_admin_css")
def global_admin_css():
    return format_html(
        '<link rel="stylesheet" href="{}">',
        static("wagtail_showables/css/showables.css"),
    )


# wagtail_showables_showables_list
# wagtail_showables_enable_disable_blocks

@hooks.register("register_admin_urls")
def register_admin_urls():
    return [
        path("showables/", showables_list, name="wagtail_showables_showables_list"),
        path("showables/edit/", showables_edit, name="wagtail_showables_enable_disable_blocks"),
    ]


class ShowablesMenuItem(MenuItem):
    def is_shown(self, request):
        return request.user.has_perm("wagtail_showables.can_view_showables")


@hooks.register("register_settings_menu_item")
def register_showables_menu_item():
    return ShowablesMenuItem(
        _("Showable Blocks"),
        reverse("wagtail_showables_showables_list"),
        name="wagtail_showables",
        icon_name="no-view",
        order=1000,
    )


@hooks.register("register_permissions")
def register_permissions():
    return Permission.objects.filter(
        content_type__app_label="wagtail_showables",
        codename__in=["can_toggle_showing", "can_view_showables"],
    )

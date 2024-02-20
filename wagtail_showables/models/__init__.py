from .data import ShowableRegistry
from .pages import ShowablesPage
from django.db import models
from django.utils.translation import gettext_lazy as _


# Create your models here.
class WagtailShowablesPermissions(models.Model):
    class Meta:
        verbose_name = _("Wagtail Showables Permissions")
        verbose_name_plural = _("Wagtail Showables Permissions")

        managed = False
        default_permissions = ()
        permissions = (
            ("can_toggle_showing", _("Can toggle if the block is shown")),
            ("can_view_showables", _("Can view the showable blocks in the admin list page.")),
        )

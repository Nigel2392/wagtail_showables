from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.contrib import messages
from .models import (
    ShowablesPage,
)
from . import (
    get_showable_backend,
)
from .registry import (
    get_sorted_registry,
)
from .backends import (
    BaseShowablePageBackend,
)



def showables_list(request: HttpRequest):
    if not request.user.has_perm("wagtail_showables.can_view_showables"):
        messages.error(request, _("You do not have the permissions to view or edit showables."))
        return redirect("wagtailadmin_home")

    registry = get_sorted_registry()

    return render(request, "wagtail_showables/showables_admin_list.html", {
        "registry": registry,
    })


def showables_edit(request: HttpRequest):
    if not request.user.has_perms([
        "wagtail_showables.can_toggle_showing",
        "wagtail_showables.can_view_showables",
    ]):
        messages.error(request, _("You do not have the permissions to view or edit showables."))
        return redirect("wagtailadmin_home")
    
    backend = get_showable_backend()
    registry = get_sorted_registry()
    form_class = backend.get_registry_form(request=request)
    form = form_class(backend, request=request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        data = form.save()
        backend.process_registry(data)

        messages.success(request, _("Showables have been updated."))
        return redirect("wagtail_showables_showables_list")
    
    elif request.method == "POST":
        messages.error(request, _("Something has gone wrong with your form submission."))

    context = {
        "registry": registry,
        "form": form,
    }

    if isinstance(backend, BaseShowablePageBackend):
        page_types = ShowablesPage.get_available_subclasses()
        d = []
        for page_type in page_types:
            d.append({
                "id": page_type._meta.label_lower,
                "name": page_type._meta.verbose_name,
            })
        context["page_types"] = d
    
    return render(request, "wagtail_showables/showables_admin_form.html", context)

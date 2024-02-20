from django.utils.translation import gettext_lazy as _
from wagtail.models import Page
from ..backends import set_showable_page_local

def get_available_subclasses(cls):
    l = []
    for subclass in cls.__subclasses__():
        if subclass._meta.abstract:
            continue 
           
        l.append(subclass)
        l.extend(get_available_subclasses(subclass))
    return l

class ShowablesPage(Page):

    class Meta:
        verbose_name = _("Showables Page")
        verbose_name_plural = _("Showables Pages")
        abstract = True

    def serve(self, request, *args, **kwargs):
        set_showable_page_local(request, self)
        response = super().serve(request, *args, **kwargs)
        return response

    @classmethod
    def get_available_subclasses(cls):
        return get_available_subclasses(cls)

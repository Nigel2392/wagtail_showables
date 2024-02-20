import warnings
from typing import TYPE_CHECKING

from django.http import HttpRequest
from . import get_showable_backend
from .models import ShowablesPage
from .backends import (
    _performance_backend_data,
    ShowablePerformanceCacheBackend,
    ShowablePerformanceDBBackend,
    set_showable_page_local,
    reset_showable_page_local,
)

from django.core.signals import request_finished
from django.dispatch import receiver
from django.apps import apps

if TYPE_CHECKING:
    from wagtail.models import Page, PageQuerySet

PageModel = apps.get_model("wagtailcore", "Page", require_ready=False)

class ShowablePerformanceDataMiddleware:
    """Middleware that saves request in thread local storage."""

    def __init__(self, get_response):
        self.get_response = get_response

        @receiver(request_finished)
        def reset_data_on_finish(sender, **kwargs):
            if hasattr(_performance_backend_data, "data"):
                del _performance_backend_data.data

    def __call__(self, request):
        backend = get_showable_backend()

        if not isinstance(backend, (ShowablePerformanceCacheBackend, ShowablePerformanceDBBackend)):
            warnings.warn(
                "You are using the ShowablePerformanceDataMiddleware without the ShowablePerformanceCacheBackend or ShowablePerformanceDBBackend. "
                "This middleware will have no effect."
            )
            return self.get_response(request)

        _performance_backend_data.data = backend.fetch_registry_data()
        try:
            response = self.get_response(request)
        finally:
            if hasattr(_performance_backend_data, "data"):
                del _performance_backend_data.data
        return response    
    

class ShowablePageAdminMiddleware:
    """Middleware that saves request in thread local storage."""

    def __init__(self, get_response):
        self.get_response = get_response

        @receiver(request_finished)
        def reset_data_on_finish(sender, **kwargs):
            reset_showable_page_local()

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request: HttpRequest, view_func, view_args, view_kwargs):
        if "wagtailadmin_pages" in request.resolver_match.app_names:
            page_id = view_kwargs.get("page_id")
            if page_id is not None:
                page = PageModel.objects\
                    .filter(id=page_id)\
                    .type(*ShowablesPage.get_available_subclasses())\
                    .specific()\
                    .first()
                set_showable_page_local(request, page.specific)
                return view_func(request, *view_args, **view_kwargs)
        
        return view_func(request, *view_args, **view_kwargs)
    

    

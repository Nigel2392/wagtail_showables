from abc import ABC, abstractmethod
from typing import Callable, List
from django import forms
from django.db import transaction
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from django.core.cache import (
    caches,
    DEFAULT_CACHE_ALIAS,
)
from wagtail import blocks
from wagtail.models import Page
import threading
from .forms import (
    ShowableForm,
)
from .models.data import ShowableRegistry
from .blocks import ShowableBlock

def get_shown(data: dict, data_key: str) -> bool:
    r: dict = data.get(data_key, {})
    return r.get("is_shown", False) not in [False, None]


class ShowableField:
    def __init__(self, name: str, label: str, field_type = forms.BooleanField, field_widget = forms.CheckboxInput, get_initial: str = None, default_initial: bool = False):
        self.name = name
        self.label = label
        self.field_type = field_type
        self.field_widget = field_widget
        self._get_initial = get_initial
        self._default_initial = default_initial
        self.block = None

    def get_form_field(self):
        return self.field_type(
            label=self.label,
            required=False,
        )
    
    def get_initial(self, block):

        if callable(self._get_initial):
            return self._get_initial(block)
        
        return block.extra.get(self.name, self._default_initial)
    


class ShowableBackend(ABC):
    def execute_checks(self, registry_data: dict, *args, **kwargs) -> bool:
        fields = self.get_form_fields()
        for field in fields:
            method_name = f"check_{field.name}"
            if field.name == "is_shown":
                continue

            elif hasattr(self, method_name):
                chk = getattr(self, method_name)
                if not chk(registry_data, *args, **kwargs):
                    return False
                
            elif registry_data.get(field.name, False) in [None, False]:
                return False
        return True

    @abstractmethod
    def process_registry(self, data: dict):
        """
            Process the registry data.
            This method should save the data in a way that it can be retrieved later.
        """

    @abstractmethod
    def registry_data(self) -> dict:
        """
            Return a dictionary of {registered_item.import_path: bool}
            Additional information can be added - this is the bare bones of what is needed.
        """

    @abstractmethod
    def is_active(self, block: blocks.StructBlock, data_key: str):
        """
            Return whether the block is active.
            This method only gets called for admin pages.
        """

    @abstractmethod
    def is_shown(self, block: blocks.StructBlock, data_key: str):
        """
            Return whether the block is shown on the front-end.
            If not - the block will not be rendered.
        """

    def renew(self):
        """
            Renew the backend's data in case of long-living objects.
            Might be useful for model-based backends.
            This is not to be used for garbage collection.
        """

    def get_form_fields(self):
        return [
            ShowableField(
                name="is_shown",
                label=_("Is Shown"),
                field_type=forms.BooleanField,
                field_widget=forms.CheckboxInput,
                get_initial=lambda block: block.is_shown,
                default_initial=False,
            )
        ]

    def get_registry_form(self, request: HttpRequest):
        return ShowableForm


class ShowableCacheBackend(ShowableBackend):
    def __init__(self, cache_key: str = "wagtail_showables", cache_backend: str = DEFAULT_CACHE_ALIAS):
        self.cache_backend = cache_backend
        self.cache = caches[cache_backend]
        self.cache_key = cache_key
        self._data = {}

    def process_registry(self, data: dict):
        self.cache.set(self.cache_key, data)
        if hasattr(self.cache, "persist"):
            self.cache.persist(self.cache_key)
        self._data = data

    def registry_data(self) -> dict:
        self._data = self.cache.get(self.cache_key, {})
        return self._data
    
    def is_active(self, block: blocks.StructBlock, data_key: str):
        return self.is_shown(block, data_key)

    def is_shown(self, block: blocks.StructBlock, data_key: str):
        data = self._data or self.registry_data() or {}
        return get_shown(data, data_key) and self.execute_checks(data, data_key=data_key)
        
    def renew(self):
        self._data = self.cache.get(self.cache_key, {})
        return self._data


_performance_backend_data = threading.local()


class ShowablePerformanceCacheBackend(ShowableCacheBackend):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        del self._data # We don't need this anymore

    def process_registry(self, data: dict):
        self.cache.set(self.cache_key, data)
        if hasattr(self.cache, "persist"):
            self.cache.persist(self.cache_key)
        _performance_backend_data.data = data

    def registry_data(self) -> dict:
        data = getattr(_performance_backend_data, "data", None)
        if data is None:
            raise ValueError("The data has not been set, are you using the ShowablePerformanceDataMiddleware?")
        return data
    
    def fetch_registry_data(self):
        return self.cache.get(self.cache_key, {}) or {}
    
    def is_shown(self, block: blocks.StructBlock, data_key: str):
        data = self.registry_data()
        return get_shown(data, data_key) and self.execute_checks(data, data_key=data_key)
    
    def renew(self):
        """
            Renew is not used for this backend.
            _performance_backend_data is a thread-local object.
            It only lives for the duration of the request.
        """
        pass


class ShowablePerformanceDBBackend(ShowableBackend):

    @transaction.atomic
    def process_registry(self, data: dict):
        registry = ShowableRegistry.load()
        registry.data = data
        registry.save()

    def registry_data(self) -> dict:
        data = getattr(_performance_backend_data, "data", None)
        if data is None:
            raise ValueError("The data has not been set, are you using the ShowablePerformanceDataMiddleware?")
        return data
    
    def is_active(self, block: blocks.StructBlock, data_key: str):
        return self.is_shown(block, data_key)
    
    def is_shown(self, block: blocks.StructBlock, data_key: str):
        data = self.registry_data()
        return get_shown(data, data_key) and self.execute_checks(data, data_key=data_key)
    
    def fetch_registry_data(self):
        registry = ShowableRegistry.load()
        return registry.data or {}
    
    def renew(self):
        """
            Renew is not used for this backend.
            _performance_backend_data is a thread-local object.
            It only lives for the duration of the request.
        """
        pass


class ShowableBlockLocal:
    def __init__(self, request: HttpRequest, page: "Page"):
        self.request    = request
        self.page       = page
        self.registry   = ShowableRegistry.load()
        

_showable_page_local = threading.local()

def get_showable_page_local() -> "ShowableBlockLocal":
    if hasattr(_showable_page_local, "showable_block_local"):
        return _showable_page_local.showable_block_local
    return None

def set_showable_page_local(request: HttpRequest, page: "Page"):
    if request is None and page is None:
        return reset_showable_page_local()
    
    _showable_page_local.showable_block_local = ShowableBlockLocal(request, page)

def reset_showable_page_local():
    if hasattr(_showable_page_local, "showable_block_local"):
        del _showable_page_local.showable_block_local


class BaseShowablePageBackend(ShowableBackend):
    """
        This backend is used for blocks on ShowablePage models.
        It can decide whether a block is shown based on the page and request.
        Using the middleware, it can also show if a block is active in the wagtailadmin.
        ShowablePageAdminMiddleware is required for this to work.
    """
    def __init__(self, default_is_shown: bool = False):
        self.default_is_shown = default_is_shown
    
    def process_registry(self, data: dict):
        registry = ShowableRegistry.load()
        registry.data = data
        registry.save()

        local = get_showable_page_local()
        if local is not None:
            local.registry = registry

    def registry_data(self) -> dict:
        local = get_showable_page_local()
        if local is None:
            registry = ShowableRegistry.load()
            return registry.data or {}
        return local.registry.data or {}
    
    def is_active(self, block: blocks.StructBlock, data_key: str):
        """
            Return whether the block is active in the wagtailadmin.
        """
        showable_block_local = get_showable_page_local()
        if showable_block_local is None:
            raise ValueError(f"The {self.__class__.__name__} is_active called on a non-showable type page, or middleware is not used.")
        
        if showable_block_local.registry is None:
            showable_block_local.registry = ShowableRegistry.load()

        return get_shown(showable_block_local.registry.data, data_key)

    def is_shown(self, block: blocks.StructBlock, data_key: str):
        """
            Return whether the block is shown on the front-end.
            Only do this for the BaseShowablePageBackend.
        """
        showable_block_local = get_showable_page_local()
        if showable_block_local is None:
            return self.default_is_shown
        
        if isinstance(block, ShowableBlock):
            return block.block_is_shown(
                backend   = self,
                request   = showable_block_local.request,
                page      = showable_block_local.page,
                data_key  = data_key,
            )
        
        return self.is_shown_for_page(
            registry_data = showable_block_local.registry.data,
            request       = showable_block_local.request,
            page          = showable_block_local.page,
            data_key      = data_key,
        )
    
    def is_shown_for_page(self, registry_data: dict, request: HttpRequest, page: "Page", data_key: str) -> bool:
        if get_shown(registry_data, data_key):
            return True
        
        if not self.execute_checks(registry_data, request=request, page=page, data_key=data_key):
            return False
                
        return True

    def renew(self):
        pass


class ShowablePageBackend(BaseShowablePageBackend):
    def get_form_fields(self):
        """
            Allow for additional logic based on the request and page.
        """
        return super().get_form_fields() + [
            ShowableField(
                name="requires_authentication",
                label=_("Requires Authentication"),
                field_type=forms.BooleanField,
                field_widget=forms.CheckboxInput,
                get_initial="requires_authentication",
                default_initial=False,
            ),
        ]
    
    def check_requires_authentication(self, registry_data: dict, request: HttpRequest, page: "Page", data_key: str) -> bool:
        """
            Checks if the user is authenticated.
            If not - the block will be hidden.
        """
        return request.user.is_authenticated


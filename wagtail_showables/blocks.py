from typing import TYPE_CHECKING
from django.http import HttpRequest
from wagtail import blocks


if TYPE_CHECKING:
    from .models.pages import ShowablesPage
    from .backends import (
        BaseShowablePageBackend,
    )


class ShowableBlock(blocks.StructBlock):
    """
        A block that can be shown or hidden based on the request, user or page.
    """

    def block_is_shown(self, backend: "BaseShowablePageBackend", request: "HttpRequest", page: "ShowablesPage", data_key: "str") -> "bool":
        """Check if the block is shown on the given page."""
        return backend.is_shown_for_page(
            registry_data=backend.registry_data(),
            request=request,
            page=page,
            data_key=data_key,
        )
    
    
    


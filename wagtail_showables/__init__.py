from .options import (
    SHOWABLES_BACKEND as _SHOWABLES_BACKEND,
    SHOWABLES_DEFAULT_BACKEND as _SHOWABLES_DEFAULT_BACKEND,
)

from django.utils.module_loading import import_string as _import_string

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .backends import ShowableBackend as _ShowableBackend

def get_showable_backend(showables_backend: str = _SHOWABLES_DEFAULT_BACKEND) -> "_ShowableBackend":
    try:
        backend_dict = _SHOWABLES_BACKEND[showables_backend]
    except KeyError as e:
        raise KeyError(f"Invalid showables backend configuration: {e}") from e
    
    try:
        backend_class = backend_dict["CLASS"]
        backend_options = backend_dict["OPTIONS"]
        backend = _import_string(backend_class)
    except ImportError as e:
        raise ImportError(f"Could not import the showables backend: {e}") from e
        
    except KeyError as e:
        raise KeyError(f"Invalid showables backend configuration: {e}") from e
    
    return backend(**backend_options)

def has_showable_backend(showables_backend: str = _SHOWABLES_DEFAULT_BACKEND) -> bool:
    return showables_backend in _SHOWABLES_BACKEND

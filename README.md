wagtail_showables
=================

An application to easily toggle types of blocks on your frontend from being seen.

It can also be used to limit admins in what they can see and edit - though there is no validation for this due to limitations with wagtail.

Quick start
-----------

1. Add 'wagtail_showables' to your `INSTALLED_APPS` setting like this:

   ```
   INSTALLED_APPS = [
   ...,
   'wagtail_showables',
   ]
   ```
2. Add the middleware to your `MIDDLEWARE` to allow for high-performance operations.

   ```python
   MIDDLEWARE = [
       "wagtail_showables.middleware.ShowablePerformanceDataMiddleware",
   ]

   ```
3. Set the default backend setting `WAGTAIL_SHOWABLES_DEFAULT_BACKEND`

   ```python
   WAGTAIL_SHOWABLES_DEFAULT_BACKEND = "performance_db"
   ```
4. Run `python manage.py migrate` to create the wagtail_showables models.
5. Run `python manage.py collectstatic` to collect the wagtail_showables static files.

## Options

### WAGTAIL_SHOWABLES_ADMIN_INTERACTION_LEVEL

The level of which the editor can interact with the block.
Options are:

```python
0 # Completely disabled and blurred out from viewing.
1 # Disabled from editing.
2 # Fully enabled
```

Example:

```python
WAGTAIL_SHOWABLES_ADMIN_INTERACTION_LEVEL = 2 # Admins can edit this block.
```

### WAGTAIL_SHOWABLES_DISABLED_DISPLAY_TEXT

The text to display when the block is disabled.
This only has an effect with `ADMIN_INTERACTION_LEVEL` set to 0.
Example:

```python
WAGTAIL_SHOWABLES_DISABLED_DISPLAY_TEXT = "This block is currently disabled."
```

### WAGTAIL_SHOWABLES_DEFAULT_BACKEND

The default backend to use for the showables.
Options are:

```python
"default" # Uses the default backend (caches, but refreshes way more often than the other backends.)
"performance_db" # Uses the database to store the showable data.
"performance_cache" # Uses the cache to store the showable data.
```

## Registering blocks with Wagtail Showables

To register a block with Wagtail Showables, you simply import the register function:

```python
from wagtail_showables.registry import register_block
```

Then, you can use the function to register your block:

```python
# def register_block(block: Type[blocks.StructBlock] = None, label: str = None, help_text: # str = None):

class MyBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    content = blocks.RichTextBlock()

register_block(MyBlock, label="My Block", help_text="This block gets used in application X and does Y.")
```

It can also be used as a decorator:

```python
@register_block(label="My Block", help_text="This block gets used in application X and does Y.")
class MyBlock(blocks.StructBlock):
    title = blocks.CharBlock()
    content = blocks.RichTextBlock()
```

You are now set to enable and disable blocks from the admin and users.

Simply head to the admin area, open the settings menu and go to the Showable Blocks menu.

## I want something more.

Do you need something more? Do you need permissions? It gets a little more complex from here.

You will need to implement your own custom backend - we provide a basic backend for is_authenticated.

The backend for pages is relatively easy to implement, this is how we implemented the `requires_authentication` field.

1. Implementing the backend.

```python
from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from wagtail_showables.backends import (
    BaseShowablePageBackend,
    ShowableField,
)

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
```

2. Adding the middleware

Add the following middleware to your `settings.py` to allow for proper garbage collection of the showable data 
and to allow for the showable blocks to get access to the request and page inside the Wagtail admin.

```python
MIDDLEWARE = [
    "wagtail_showables.middleware.ShowablePageAdminMiddleware",
]
```

3. Implementing your page model.

We require you to use a custom page model to use the backend to properly set the data in thread locals.

```python
from wagtail_showables.models import ShowablesPage
class BlogPage(ShowablesPage, Page):
    ...
```

4. Registering the backend.

Add the import path to your custom backend in your `settings.py` file.

```python
SHOWABLES_DEFAULT_BACKEND = "my_backend"
WAGTAIL_SHOWABLES_BACKEND = {
    "my_backend": {
        "CLASS": "myapp.backends.MyCustomBackend",
        "OPTIONS": {
            "my_option": "my_value",
        },
    }
}
```

You are now set to use your custom backend to control the showable blocks from the wagtailadmin.
Now you will also see your defined field in the wagtailadmin to give you more granular control over the showable blocks.

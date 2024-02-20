from typing import Any
from django import forms
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _
from .registry import get_sorted_registry

class RegisteredItemMultiWidget(forms.MultiWidget):

    template_name = "wagtail_showables/multi_widget.html"

    def __init__(self, block, fields, attrs=None):
        self.block = block
        self.widgets = [
            field.field_widget(attrs)
            for field in fields
        ]
        self.fields = fields
        super().__init__(self.widgets, attrs)
    
    def decompress(self, value):
        if value:
            return value
        return [False] * len(self.widgets)
    
    def get_context(self, name: str, value: Any, attrs: dict[str, Any] | None) -> dict[str, Any]:
        return super().get_context(name, value, attrs) | {
            "fields": [
                {
                    "label": field.label,
                    "widget": widget,
                }
                for field, widget in zip(self.fields, self.widgets)
            ],
            "block": self.block,
        }
    
class RegisteredItemMultiValueField(forms.MultiValueField):
    def __init__(self, block, fields, *args, **kwargs):
        widget = RegisteredItemMultiWidget(block, fields)
        fields = [
            field.get_form_field()
            for field in fields
        ]
        super().__init__(fields, widget=widget, *args, **kwargs)

    def compress(self, data_list):
        return data_list
    

class ShowableForm(forms.Form):
    def __init__(self, backend, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.registry = get_sorted_registry()
        self.showable_fields = backend.get_form_fields()
        for block in self.registry:
            self.fields[block.import_path] = RegisteredItemMultiValueField(
                block,
                fields=self.showable_fields,
                label=block.label,
                help_text=block.help_text,
                initial=[
                    field.get_initial(block)
                    for field in self.showable_fields
                ],
                required=False,
            )
            
        for block in self.registry:
            setattr(self[block.import_path], "showable_fields", self.showable_fields)

    def save(self):
        data = {}
        for block in self.registry:
            cleaned = self.cleaned_data[block.import_path]
            data[block.import_path] = {
                field.name: cleaned[i]
                for i, field in enumerate(self.showable_fields)
            }
        return data

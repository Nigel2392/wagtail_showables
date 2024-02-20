from django.db import models
from django.utils.translation import gettext_lazy as _

class ShowableRegistry(models.Model):
    key = models.CharField(max_length=1, unique=True, default="X", primary_key=True)
    data = models.JSONField(default=dict)

    def __str__(self):
        str(_(f"Showable Registry"))

    class Meta:
        verbose_name = _("Showable Registry")
        verbose_name_plural = _("Showable Registries")

    def save(self, *args, **kwargs):
        self.key = "X"
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        self, _ = cls.objects.get_or_create(key="X")
        return self

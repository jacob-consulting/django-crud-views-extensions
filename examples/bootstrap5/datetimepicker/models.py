from django.db import models
from django.utils.translation import gettext_lazy as _


class Event(models.Model):
    title = models.CharField(_("title"), max_length=100)
    day = models.DateField(_("day"))
    doors_open = models.TimeField(_("doors open"))
    starts_at = models.DateTimeField(_("starts at"))
    ends_at = models.DateTimeField(_("ends at"), null=True, blank=True)

    class Meta:
        ordering = ["day", "starts_at"]
        verbose_name = _("event")
        verbose_name_plural = _("events")

    def __str__(self):
        return self.title


class PickerVariant(models.Model):
    """One field per per-field config example; all optional so any subset can be tried."""

    name = models.CharField(_("name"), max_length=100)
    this_year = models.DateTimeField(_("this year only"), null=True, blank=True)
    quarter_hour = models.TimeField(_("quarter-hour steps"), null=True, blank=True)
    no_past = models.DateField(_("today or later"), null=True, blank=True)
    weekdays_only = models.DateField(_("weekdays only"), null=True, blank=True)
    inline_calendar = models.DateField(_("inline calendar"), null=True, blank=True)
    fixed_times = models.TimeField(_("fixed times"), null=True, blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("picker variant")
        verbose_name_plural = _("picker variants")

    def __str__(self):
        return self.name

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Team(models.Model):
    name = models.CharField(_("name"), max_length=100, unique=True)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="teams", blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("team")
        verbose_name_plural = _("teams")

    def __str__(self):
        return self.name


class Task(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="tasks")
    title = models.CharField(_("title"), max_length=100)
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="typeahead_tasks",
        verbose_name=_("assignee"),
    )

    class Meta:
        ordering = ["title"]
        verbose_name = _("task")
        verbose_name_plural = _("tasks")

    def __str__(self):
        return self.title

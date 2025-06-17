from django.db import models


class TimeStampedMixin(models.Model):
    """
    Abstract base class with a creation and update date and time
    """

    class Meta:
        abstract = True

    created_on = models.DateTimeField(
        verbose_name=("created at"), auto_now_add=True,)
    modified_on = models.DateTimeField(
        verbose_name=("last updated"), auto_now=True)

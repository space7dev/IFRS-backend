from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import ugettext_lazy as _


class User(AbstractUser):

    ADMIN = 0
    REGULAR = 1000
    ROLE_CHOICES = (
        (ADMIN, "Administrator"),
        (REGULAR, "Regular"),
    )

    role = models.PositiveSmallIntegerField(
        verbose_name=_("User Role"),
        choices=ROLE_CHOICES,
        default=REGULAR
    )

    def __str__(self):
        return f"[{self.email}] {self.get_full_name()}"

    def toggle_account_status(self):
        if self.is_active:
            self.is_active = False
        else:
            self.is_active = True
        self.save()

    def deactivate_account(self):
        self.is_active = False
        self.save()

    def activate_account(self):
        self.is_active = True
        self.save()

    def is_administrator(self):
        return self.role == self.ADMIN

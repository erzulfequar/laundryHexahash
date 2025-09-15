from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    is_superadmin = models.BooleanField(default=False)
    is_org_admin = models.BooleanField(default=False)
    organization = models.ForeignKey('laundry.Organization', null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return self.username

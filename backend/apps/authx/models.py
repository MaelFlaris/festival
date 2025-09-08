# backend/apps/authx/models.py
from django.conf import settings
from django.db import models
from apps.common.models import TimeStampedModel

class UserProfile(TimeStampedModel):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    display_name = models.CharField(max_length=120, blank=True)
    avatar = models.URLField(blank=True)
    preferences = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return self.display_name or self.user.get_username()

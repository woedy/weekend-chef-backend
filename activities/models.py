from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class AllActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='all_user_activities', blank=True, null=True)
    subject = models.CharField(max_length=500, unique=False, blank=True, null=True)
    body = models.TextField(unique=False, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

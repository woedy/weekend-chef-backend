from django.db import models
from django.db.models.signals import pre_save
from django.contrib.auth import get_user_model

from weekend_chef_project.utils import unique_admin_id_generator


User = get_user_model()

class WeekendChefAdmin(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='week_admin')
    admin_id = models.CharField(max_length=200, null=True, blank=True)
    
    
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)


    is_archived = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.user.email



def pre_save_admin_id_receiver(sender, instance, *args, **kwargs):
    if not instance.admin_id:
        instance.admin_id = unique_admin_id_generator(instance)

pre_save.connect(pre_save_admin_id_receiver, sender=WeekendChefAdmin)


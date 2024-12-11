import os
import random

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, pre_save

from tas_project.utils import unique_client_id_generator, unique_complaint_id_generator

User = get_user_model()




class DispatchDriver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    dispatch_id = models.CharField(max_length=200, null=True, blank=True)
    
    vehicle_type = models.CharField(max_length=50, null=True, blank=True)  # Vehicle type (bike, car, etc.)
    vehicle_registration_number = models.CharField(max_length=50, null=True, blank=True)  # Vehicle reg number
    # A field to store delivery areas or zones they cover, could be a JSON or many-to-many relation.
    zones_covered = models.CharField(max_length=255, null=True, blank=True)  # Example: a comma-separated list of zones



def pre_save_dispatch_id_receiver(sender, instance, *args, **kwargs):
    if not instance.dispatch_id:
        instance.dispatch_id = unique_dispatch_id_generator(instance)

pre_save.connect(pre_save_dispatch_id_receiver, sender=DispatchDriver)









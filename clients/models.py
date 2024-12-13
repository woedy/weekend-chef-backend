import os
import random

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, pre_save

from weekend_chef_project.utils import unique_client_id_generator


User = get_user_model()



CLIENT_TYPES = [
    ('Busy Professional', 'Busy Professional'),
    ('Fitness Health', 'Fitness & Health Enthusiast'),
    ('Family Meal Planner', 'Family Meal Planner'),
    ('Student', 'Student'),
    ('Food Lover', 'Foodie/Culinary Explorer'),
    ('Dietary Specific', 'Special Dietary Needs')
]

DIETARY_SUBTYPES = [
    ('Vegetarian', 'Vegetarian'),
    ('Vegan', 'Vegan'),
    ('Keto', 'Keto'),
    ('Gluten Free', 'Gluten-Free'),
    ('Halal', 'Halal'),
    ('Kosher', 'Kosher')
]

class Client(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clients')
    client_id = models.CharField(max_length=200, null=True, blank=True)
    dietary_type = models.CharField(choices=DIETARY_SUBTYPES, null=True, blank=True, max_length=200)
    
    
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)

    passport_id_number = models.CharField(null=True, blank=True, max_length=500)

    # Preferences
    client_type = models.CharField(max_length=100, choices=CLIENT_TYPES)
    dietary_preferences = models.ManyToManyField('DietaryPreference')
    allergies = models.ManyToManyField('Allergy')

    is_archived = models.BooleanField(default=False)
    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.user.email



def pre_save_client_id_receiver(sender, instance, *args, **kwargs):
    if not instance.client_id:
        instance.client_id = unique_client_id_generator(instance)

pre_save.connect(pre_save_client_id_receiver, sender=Client)





class DietaryPreference(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='dietary_icons/', null=True, blank=True)

    def __str__(self):
        return self.name

class Allergy(models.Model):
    name = models.CharField(max_length=100, unique=True)
    severity = models.CharField(max_length=50, choices=[
        ('Low', 'Low Risk'),
        ('Medium', 'Medium Risk'),
        ('High', 'High Risk')
    ])
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='allergy_icons/', null=True, blank=True)

    def __str__(self):
        return self.name



class ClientHomeLocation(models.Model):
    location_name = models.CharField(max_length=200, null=True, blank=True)
    digital_address = models.CharField(max_length=200, null=True, blank=True)
    lat = models.DecimalField(default=0.0, max_digits=30, decimal_places=15, null=True, blank=True)
    lng = models.DecimalField(default=0.0, max_digits=30, decimal_places=15, null=True, blank=True)

    is_deleted = models.BooleanField(default=False)

    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)






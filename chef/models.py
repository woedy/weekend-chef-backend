import os
import random

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models.signals import post_save, pre_save

from weekend_chef_project.utils import unique_chef_id_generator


User = get_user_model()


CHEF_TYPES = [
    ('Home Chef', 'Home Chef'),
    ('Professional Chef', 'Professional Chef'),
    ('Culinary Student', 'Culinary Student'),
    ('Hobby Cook', 'Hobby Cook'),
    ('Catering Professional', 'Catering Professional')
]

CHEF_CUISINE_SPECIALTIES = [
    ('Local', 'Local Cuisine'),
    ('International', 'International Cuisine'),
    ('Fusion', 'Fusion Cuisine'),
    ('Healthy', 'Healthy Cooking'),
    ('Baking', 'Baking & Desserts'),
    ('Vegetarian', 'Vegetarian Specialist'),
    ('Vegan', 'Vegan Cuisine')
]


class CuisineSpecialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='cuisine_icons/', null=True, blank=True)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Certification(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to='chef_certifications/', null=True, blank=True)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name



CHEF_AVAILABILITY = [
    ('Saturday', 'Saturday'),
    ('Sunday', 'Sunday'),
    ('Both', 'Both'),
    
]


class ChefProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    chef_id = models.CharField(max_length=200, null=True, blank=True)

    chef_type = models.CharField(max_length=100, choices=CHEF_TYPES, null=True, blank=True)
    certifications = models.ManyToManyField('Certification', blank=True)
    
    # Location & Availability
    kitchen_address = models.TextField(null=True, blank=True)

    kitchen_location = models.CharField(max_length=5000, null=True, blank=True)
    lat = models.DecimalField(default=0.0, max_digits=30, decimal_places=15, null=True, blank=True)
    lng = models.DecimalField(default=0.0, max_digits=30, decimal_places=15, null=True, blank=True)




    service_radius = models.IntegerField(default=10)  # km
    availability = models.CharField(max_length=100, choices=CHEF_AVAILABILITY, null=True, blank=True)
    
    # Professional Details
    cuisine_specialties = models.ManyToManyField('CuisineSpecialty', blank=True)
    years_of_experience = models.IntegerField(null=True, blank=True)
    
    max_order_capacity = models.IntegerField(default=10)

    # Performance Metrics
    total_orders = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)



def pre_save_chef_id_receiver(sender, instance, *args, **kwargs):
    if not instance.chef_id:
        instance.chef_id = unique_chef_id_generator(instance)

pre_save.connect(pre_save_chef_id_receiver, sender=ChefProfile)




class ChefReview(models.Model):
    review_id = models.CharField(max_length=200, null=True, blank=True)

    chef = models.ForeignKey(ChefProfile, on_delete=models.CASCADE, related_name="complaints_complaints")

    review = models.TextField(null=True, blank=True)


    is_archived = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)




def pre_save_review_id_receiver(sender, instance, *args, **kwargs):
    if not instance.review_id:
        instance.review_id = unique_review_id_generator(instance)

pre_save.connect(pre_save_review_id_receiver, sender=ChefReview)







class ChefGallery(models.Model):
    name = models.CharField(max_length=200)
    chef = models.ForeignKey(ChefProfile, on_delete=models.CASCADE)
    description = models.TextField()
    photo = models.ImageField(upload_to='chef/gallery/', null=True, blank=True)




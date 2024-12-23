from django.db import models
from django.db.models.signals import post_save, pre_save

from weekend_chef_project.utils import unique_dish_gallery_id_generator, unique_dish_id_generator, unique_ingredient_id_generator

class FoodCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    photo = models.ImageField(upload_to='dish/category/', null=True, blank=True)

    is_archived = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Dish(models.Model):
    dish_id = models.CharField(max_length=255, blank=True, null=True, unique=True)
    name = models.CharField(max_length=200)
    category = models.ForeignKey(FoodCategory, on_delete=models.CASCADE)
    description = models.TextField()
    cover_photo = models.ImageField(upload_to='dish/covers/', null=True, blank=True)
    base_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(default=1)

    is_archived = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

def pre_save_dish_id_receiver(sender, instance, *args, **kwargs):
    if not instance.dish_id:
        instance.dish_id = unique_dish_id_generator(instance)

pre_save.connect(pre_save_dish_id_receiver, sender=Dish)





class DishIngredient(models.Model):
    ingredient_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    name = models.CharField(max_length=200)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    description = models.TextField()
    photo = models.ImageField(upload_to='dish/ingredient/', null=True, blank=True)

    category = models.CharField(max_length=50, choices=[('Solid', 'Solid'), ('Liquid', 'Liquid')], default='Solid')
    unit = models.CharField(max_length=50)  # Unit of measurement (kg, g, L, mL, cups, etc.)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Optional field for price tracking

    is_archived = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def pre_save_ingredient_id_receiver(sender, instance, *args, **kwargs):
    if not instance.ingredient_id:
        instance.ingredient_id = unique_ingredient_id_generator(instance)

pre_save.connect(pre_save_ingredient_id_receiver, sender=DishIngredient)



class DishGallery(models.Model):
    dish_gallery_id = models.CharField(max_length=255, blank=True, null=True, unique=True)

    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    caption = models.TextField()
    photo = models.ImageField(upload_to='dish/gallery/', null=True, blank=True)

    is_archived = models.BooleanField(default=False)

    active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def pre_save_dish_gallery_id_receiver(sender, instance, *args, **kwargs):
    if not instance.dish_gallery_id:
        instance.dish_gallery_id = unique_dish_gallery_id_generator(instance)

pre_save.connect(pre_save_dish_gallery_id_receiver, sender=DishGallery)


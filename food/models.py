from django.db import models

class FoodCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)



class Dish(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(FoodCategory, on_delete=models.CASCADE)
    description = models.TextField()
    cover_photo = models.ImageField(upload_to='dish/covers/', null=True, blank=True)
    base_price = models.CharField(max_length=255, null=True, blank=True)
    quantity = models.IntegerField(default=1)




class DishIngredient(models.Model):
    name = models.CharField(max_length=200)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    description = models.TextField()
    photo = models.ImageField(upload_to='dish/ingredient/', null=True, blank=True)


class DishGallery(models.Model):
    name = models.CharField(max_length=200)
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    description = models.TextField()
    photo = models.ImageField(upload_to='dish/gallery/', null=True, blank=True)



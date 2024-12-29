from django.contrib import admin

from food.models import CustomizationOption, Dish, DishGallery, DishIngredient, FoodCategory, FoodCustomization, FoodPairing

admin.site.register(FoodCategory)
admin.site.register(Dish)
admin.site.register(DishIngredient)
admin.site.register(DishGallery)
admin.site.register(CustomizationOption)
admin.site.register(FoodPairing)
admin.site.register(FoodCustomization)

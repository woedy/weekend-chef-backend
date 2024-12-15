from django.contrib import admin

from food.models import Dish, DishIngredient, FoodCategory

admin.site.register(FoodCategory)
admin.site.register(Dish)
admin.site.register(DishIngredient)

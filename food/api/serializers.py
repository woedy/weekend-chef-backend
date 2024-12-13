from django.contrib.auth import get_user_model
from rest_framework import serializers

from food.models import Dish, DishGallery, DishIngredient, FoodCategory

User = get_user_model()




class AllFoodCategorysSerializer(serializers.ModelSerializer):

    class Meta:
        model = FoodCategory
        fields = "__all__"


class AllDishsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dish
        fields = "__all__"




class DishDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dish
        fields = "__all__"



####### INGREDIENTS 

class AllIngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = DishIngredient
        fields = "__all__"

class DishIngredientDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DishIngredient
        fields = "__all__"

class AllDishGallerySerializer(serializers.ModelSerializer):

    class Meta:
        model = DishGallery
        fields = "__all__"

class DishGalleryDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = DishGallery
        fields = "__all__"


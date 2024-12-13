from django.contrib.auth import get_user_model
from rest_framework import serializers

from food.models import Dish, FoodCategory

User = get_user_model()




class AllFoodCategorysSerializer(serializers.ModelSerializer):

    class Meta:
        model = FoodCategory
        fields = "__all__"


class AllDishsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dish
        fields = "__all__"


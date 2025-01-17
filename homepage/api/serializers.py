
from rest_framework import serializers

from food.models import Dish, FoodCategory


class HomeDishsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dish
        fields = ['dish_id', 'name', 'cover_photo', 'small_price', 'small_value', 'customizable', 'description']


class HomeFoodCategorysSerializer(serializers.ModelSerializer):

    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'photo']

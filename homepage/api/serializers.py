
from rest_framework import serializers

from food.models import Dish, FoodCategory


class HomeDishsSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dish
        fields = ['dish_id', 'name', 'cover_photo', 'base_price', 'value', 'customizable']


class HomeFoodCategorysSerializer(serializers.ModelSerializer):
    dishes = HomeDishsSerializer(many=True)

    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'photo', 'dishes']

from django.contrib.auth import get_user_model
from rest_framework import serializers

from food.models import Dish, DishGallery, DishIngredient, FoodCategory

User = get_user_model()




class AllFoodCategorysSerializer(serializers.ModelSerializer):

    class Meta:
        model = FoodCategory
        fields = "__all__"


class AllDishsSerializer(serializers.ModelSerializer):

    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = ['dish_id', 
                  'name', 
                  'category_name', 
                  'description', 
                  'cover_photo', 
                  'small_price', 
                  'small_value', 
                  'customizable'
                  ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None


        
class DishDetailIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = DishIngredient
        fields = ['ingredient_id', 'name', 'quantity', 'unit', 'price', 'photo']



class DishDetailsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [ 'dish_id', 'name', 'category_name', 'description', 'cover_photo', 'base_price', 'value', 'customizable', 'quantity']

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None



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


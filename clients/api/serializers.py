from django.contrib.auth import get_user_model
from rest_framework import serializers

from chef.models import ChefProfile
from clients.models import Client
from complaints.models import ClientComplaint
from food.models import CustomizationOption, Dish, DishGallery, DishIngredient, FoodCustomization, FoodPairing

User = get_user_model()


class ClientUserDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"

class AllClientsUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = "__all__"


class ClientDetailsSerializer(serializers.ModelSerializer):
    user = ClientUserDetailSerializer(many=False)
    class Meta:
        model = Client
        fields = "__all__"


class AllClientsSerializer(serializers.ModelSerializer):
    user = AllClientsUserSerializer(many=False)
    class Meta:
        model = Client
        fields = "__all__"




class ClientComplaintDetailSerializer(serializers.ModelSerializer):
    client = ClientDetailsSerializer(many=False)

    class Meta:
        model = ClientComplaint
        fields = "__all__"

class AllClientComplaintsSerializer(serializers.ModelSerializer):
    client = ClientDetailsSerializer(many=False)
    class Meta:
        model = ClientComplaint
        fields = "__all__"

        
class DishGallerySerializer(serializers.ModelSerializer):
    class Meta:
        model = DishGallery
        fields = ['dish_gallery_id', 'caption', 'photo']

        
class DishIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = DishIngredient
        fields = ['ingredient_id', 'name', 'photo']


class DishDetailsSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    ingredients = DishIngredientSerializer(many=True) 

    class Meta:
        model = Dish
        fields = ['dish_id', 
                  'name', 
                  'description', 
                  'base_price', 
                  'cover_photo', 
                  'category_name', 
                  'quantity', 
                  'value', 
                  'customizable',
                  'ingredients',
                  ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
    

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'email', 'first_name', 'last_name', 'phone', 'photo']

class ChefProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)

    class Meta:
        model = ChefProfile
        fields = ['user', 'chef_id','kitchen_location']



class FoodItemSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = ['dish_id', 
                  'name', 
                  'cover_photo',
                  'description',
                  'base_price',
                  'category_name',
                  ]
        
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None



class CustomizationOptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomizationOption
        fields = ['custom_option_id', 
                  'name', 
                  'photo',
                    'price',
                    'quantity',
                    'unit'
                  ]


class FoodCustomizationSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(many=False) 
    custom_option = CustomizationOptionSerializer(many=False) 

    class Meta:
        model = FoodCustomization
        fields = ['food_item', 'custom_option']


class FoodPairingSerializer(serializers.ModelSerializer):
    food_item = FoodItemSerializer(many=False) 
    related_food = FoodItemSerializer(many=False) 

    class Meta:
        model = FoodPairing
        fields = ['food_item', 'related_food']
from django.contrib.auth import get_user_model
from rest_framework import serializers

from chef.models import ChefProfile
from clients.models import Client
from complaints.models import ClientComplaint
from food.models import CustomizationOption, Dish, DishGallery, DishIngredient, FoodCategory, FoodCustomization, FoodPairing

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
    parent_category_names = serializers.SerializerMethodField()  # Field to get parent category names
    ingredients = DishIngredientSerializer(many=True)

    class Meta:
        model = Dish
        fields = [
            'dish_id', 
            'name', 
            'description', 

            'small_price', 
            'small_value', 

            'medium_price',
            'medium_value', 

            'large_price',
            'large_value', 

            'cover_photo', 
            'category_name', 
            'quantity', 
            'customizable',
            'ingredients',
            'parent_category_names',  # Add parent_category_names field
        ]

    def get_category_name(self, obj):
        return obj.category.name if obj.category else None

    def get_parent_category_names(self, obj):
        # Initialize a list to store the parent category names
        parent_categories = []
        current_category = obj.category
        
        # Traverse the category hierarchy upwards to get the parent categories
        while current_category and current_category.parent:
            parent_categories.append(current_category.parent.name)
            current_category = current_category.parent
        
        # Return the parent categories (if any), reversed to show the hierarchy from top to bottom
        return parent_categories[::-1]


        

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
                  'small_price',
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



class ClientFoodCategorysSerializer(serializers.ModelSerializer):

    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'description', 'photo', 'parent']









class ClientDishesSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = ['dish_id', 
                  'name', 
                  'cover_photo',
                  'description',
                  'small_price',
                  'category_name',
                  'small_value'
                  ]
        
    def get_category_name(self, obj):
        return obj.category.name if obj.category else None
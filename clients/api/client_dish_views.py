from django.contrib.auth import get_user_model
from requests import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.response import Response

from chef.models import ChefProfile
from clients.api.serializers import ChefProfileSerializer, DishDetailsSerializer, DishIngredientSerializer, FoodCustomizationSerializer, FoodItemSerializer, FoodPairingSerializer
from food.models import Dish, DishGallery, DishIngredient, FoodCustomization, FoodPairing

User = get_user_model()



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_client_dish_details_view(request):
    payload = {}
    data = {}
    errors = {}

    closest_chef = []
    custom = []
    ingredients = []
    gallery = []

    # Get query parameters
    dish_id = request.query_params.get('dish_id', None)
    user_id = request.query_params.get('user_id', None)
    radius = request.query_params.get('radius', None)

    # Validate required fields
    if not dish_id:
        errors['dish_id'] = ["Dish id required"]

    if not user_id:
        errors['user_id'] = ["User id required"]

    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        errors['dish_id'] = ['Dish does not exist.']

    try:
        user = User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        errors['user_id'] = ['User does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Handle radius if provided
    if radius:
        try:
            radius = int(radius)
        except ValueError:
            errors['radius'] = ['Radius must be an integer.']
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Get closest chefs (if needed)
    chefs = ChefProfile.objects.all()
    chef_serializer = ChefProfileSerializer(chefs, many=True)
    closest_chef = chef_serializer.data if chef_serializer else []

    # Get custom options for the dish (exclude food_item from response)
    custom_options = FoodCustomization.objects.filter(food_item=dish)
    custom_serializer = FoodCustomizationSerializer(custom_options, many=True)

    # Modify the custom serializer data to remove custom_option wrapper
    custom = []
    for option in custom_serializer.data:
        custom_option = option.get('custom_option', {})
        # Remove the wrapper and add the fields directly
        custom.append({
            'custom_option_id': custom_option.get('custom_option_id'),
            'name': custom_option.get('name'),
            'photo': custom_option.get('photo'),
            'price': custom_option.get('price')
        })

    # Get ingredients for the dish
    ingredients = DishIngredient.objects.filter(dish=dish)
    ingredient_serializer = DishIngredientSerializer(ingredients, many=True)
    ingredients = ingredient_serializer.data if ingredient_serializer else []

    # Get only related foods (excluding the original dish)
    related_foods = FoodPairing.objects.filter(food_item=dish).exclude(related_food=dish).select_related('related_food')
    
    # Serialize only the related food items
    related_foods = [pair.related_food for pair in related_foods]  # Extract only the related foods

    related_foods_serializer = FoodItemSerializer(related_foods, many=True)
    related_foods = related_foods_serializer.data if related_foods_serializer else []

    # Serialize the dish details
    dish_serializer = DishDetailsSerializer(dish, many=False)
    dish = dish_serializer.data if dish_serializer else {}

    # Prepare response data
    data['dish'] = dish
    
    data['closest_chef'] = closest_chef
    data['related_foods'] = related_foods  # Only the related foods, not the original dish
    data['custom'] = custom  # Now custom contains the flattened custom options
    data['ingredients'] = ingredients

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

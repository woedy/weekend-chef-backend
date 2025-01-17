from django.contrib.auth import get_user_model
from requests import Response
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework import status
from rest_framework.response import Response

from chef.models import ChefProfile
from clients.api.serializers import ChefProfileSerializer, ClientDishesSerializer, ClientFoodCategorysSerializer, DishDetailsSerializer, DishIngredientSerializer, FoodCustomizationSerializer, FoodItemSerializer, FoodPairingSerializer
from food.models import Dish, DishGallery, DishIngredient, FoodCategory, FoodCustomization, FoodPairing


from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q

User = get_user_model()



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_client_dish_details_view(request):
    payload = {}
    data = {}
    errors = {}

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
    
    data['related_foods'] = related_foods  # Only the related foods, not the original dish
    data['custom'] = custom  # Now custom contains the flattened custom options
    data['ingredients'] = ingredients

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_client_dishes_view(request):
    payload = {}
    data = {}
    errors = {}

    # Get query parameters
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    category_id = request.query_params.get('category_id', '')  
    page_size = 10




    if not category_id:
        errors['category_id'] = ['Category ID is required.']
        return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)

    # Start with all dishes, excluding archived ones
    all_dishs = Dish.objects.filter(is_archived=False)
    print(all_dishs)



    try:
        all_dishs = all_dishs.filter(category__id=category_id)
        print(all_dishs)
    except:
        errors['category_id'] = ["Invalid categories format."]
        return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)

    # If a search query is provided, filter by dish name
    if search_query:
        all_dishs = all_dishs.filter(Q(name__icontains=search_query)).distinct()



    # Paginate the result
    paginator = Paginator(all_dishs, page_size)

    try:
        paginated_dishs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dishs = paginator.page(1)
    except EmptyPage:
        paginated_dishs = paginator.page(paginator.num_pages)

    # Serialize the paginated dishes
    all_dishs_serializer = ClientDishesSerializer(paginated_dishs, many=True)

    # Prepare the response data
    data['dishes'] = all_dishs_serializer.data
    data['pagination'] = {
        'page_number': paginated_dishs.number,
        'total_pages': paginator.num_pages,
        'next': paginated_dishs.next_page_number() if paginated_dishs.has_next() else None,
        'previous': paginated_dishs.previous_page_number() if paginated_dishs.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_client_food_categories(request):
    payload = {}
    data = {}
    errors = {}

    # Get query parameters
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    # Filter categories: only those without a parent (main categories)
    all_food_categories = FoodCategory.objects.filter(is_archived=False, parent__isnull=True)

    # Apply search filter if provided
    if search_query:
        all_food_categories = all_food_categories.filter(
            Q(name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(all_food_categories, page_size)

    try:
        paginated_food_categories = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_food_categories = paginator.page(1)
    except EmptyPage:
        paginated_food_categories = paginator.page(paginator.num_pages)

    # Serialize food categories
    all_food_categories_serializer = ClientFoodCategorysSerializer(paginated_food_categories, many=True)

    # Prepare pagination data
    data['food_categories'] = all_food_categories_serializer.data
    data['pagination'] = {
        'page_number': paginated_food_categories.number,
        'total_pages': paginator.num_pages,
        'next': paginated_food_categories.next_page_number() if paginated_food_categories.has_next() else None,
        'previous': paginated_food_categories.previous_page_number() if paginated_food_categories.has_previous() else None,
    }

    # Return successful response
    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_client_food_sub_categories(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    category_id = request.query_params.get('category_id', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    # Ensure category_id is provided and valid
    if not category_id:
        errors['category_id'] = ['Category ID is required.']
        payload['message'] = 'Errors'
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch the food category based on the provided category_id
        food_category = FoodCategory.objects.get(id=category_id)
    except FoodCategory.DoesNotExist:
        errors['category_id'] = ['FoodCategory does not exist.']
        payload['message'] = 'Errors'
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    # Fetch all subcategories related to the found category
    all_subcategories = food_category.subcategories.all().filter(is_archived=False)

    # If there is a search query, filter the subcategories by name
    if search_query:
        all_subcategories = all_subcategories.filter(Q(name__icontains=search_query))

    # Paginate the results
    paginator = Paginator(all_subcategories, page_size)
    
    try:
        paginated_subcategories = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_subcategories = paginator.page(1)
    except EmptyPage:
        paginated_subcategories = paginator.page(paginator.num_pages)

    # Serialize the data
    subcategories_serializer = ClientFoodCategorysSerializer(paginated_subcategories, many=True)

    # Prepare the response data
    data['food_categories'] = subcategories_serializer.data
    data['pagination'] = {
        'page_number': paginated_subcategories.number,
        'total_pages': paginator.num_pages,
        'next': paginated_subcategories.next_page_number() if paginated_subcategories.has_next() else None,
        'previous': paginated_subcategories.previous_page_number() if paginated_subcategories.has_previous() else None,
    }

    payload['message'] = 'Successful'
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)







from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.api.custom_jwt import CustomJWTAuthentication
from accounts.api.client_views import is_valid_email, check_email_exist
from activities.models import AllActivity
from clients.api.serializers import AllClientsSerializer, ClientDetailsSerializer, AllClientComplaintsSerializer, \
    ClientComplaintDetailSerializer

from clients.models import Client, ClientComplaint
from food.models import FoodCategory

User = get_user_model()


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_chef_dishes(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        email = request.data.get('email', "").lower()
        company_name = request.data.get('company_name', "")
        first_name = request.data.get('first_name', "")
        last_name = request.data.get('last_name', "")
        phone = request.data.get('phone', "")
        purpose = request.data.get('purpose', "")
        photo = request.data.get('photo', "")
        person_in_charge = request.data.get('person_in_charge', "")
        client_type = request.data.get('client_type', "")

        if not email:
            errors['email'] = ['User Email is required.']
        elif not is_valid_email(email):
            errors['email'] = ['Valid email required.']
        elif check_email_exist(email):
            errors['email'] = ['Email already exists in our database.']

        if not company_name:
            errors['company_name'] = ['Company Name is required.']

        if not first_name:
            errors['first_name'] = ['First Name is required.']

        if not phone:
            errors['phone'] = ['Phone number is required.']

        if not last_name:
            errors['last_name'] = ['Last Name is required.']

        if not purpose:
            errors['purpose'] = ['Purpose is required.']

        if not client_type:
            errors['client_type'] = ['Client Type is required.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        user = User.objects.create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            department="CLIENT",
            photo=photo
        )

        client_profile = Client.objects.create(
            user=user,
            purpose=purpose,
            company_name=company_name,
            person_in_charge=person_in_charge,
            client_type=client_type,

        )

        data["user_id"] = user.user_id
        data["client_id"] = client_profile.client_id
        data["company_name"] = client_profile.company_name
        data["purpose"] = client_profile.purpose
        data["email"] = user.email
        data["first_name"] = user.first_name
        data["last_name"] = user.last_name


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_parent_categories_for_dish_and_chef(request):
    payload = {}
    data = {}

    # Retrieve query parameters
    dish_id = request.query_params.get('dish_id', None)
    chef_id = request.query_params.get('chef_id', None)
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    # Ensure dish_id and chef_id are provided
    if not dish_id or not chef_id:
        return Response({'error': 'dish_id and chef_id are required'}, 
                        status=status.HTTP_400_BAD_REQUEST)

    # Step 1: Ensure the dish belongs to the chef
    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        return Response({'error': 'Dish with the provided dish_id does not exist.'},
                        status=status.HTTP_404_NOT_FOUND)

    # Check if the dish belongs to the provided chef
    if not ChefDish.objects.filter(chef_id=chef_id, dish=dish).exists():
        return Response({'error': 'The provided dish does not belong to the specified chef.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Step 2: Fetch parent categories (those with parent=None) that are associated with the chef's dish
    parent_categories = FoodCategory.objects.filter(parent__isnull=True, is_archived=False)

    # Apply search query if provided
    if search_query:
        parent_categories = parent_categories.filter(
            Q(name__icontains=search_query)
        )

    # Step 3: Filter parent categories by the chef's dishes
    # Get all the dishes the chef is associated with
    chef_dishes = ChefDish.objects.filter(chef_id=chef_id).values_list('dish_id', flat=True)

    # Now filter the parent categories to ensure they are linked to the chef's dishes
    parent_categories = parent_categories.filter(dishes__dish_id__in=chef_dishes)

    # Step 4: Paginate the results
    paginator = Paginator(parent_categories, page_size)
    try:
        paginated_parent_categories = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_parent_categories = paginator.page(1)
    except EmptyPage:
        paginated_parent_categories = paginator.page(paginator.num_pages)

    # Step 5: Serialize the parent categories
    parent_categories_serializer = AllFoodCategorysSerializer(paginated_parent_categories, many=True)

    # Prepare response data
    data['parent_categories'] = parent_categories_serializer.data
    data['pagination'] = {
        'page_number': paginated_parent_categories.number,
        'total_pages': paginator.num_pages,
        'next': paginated_parent_categories.next_page_number() if paginated_parent_categories.has_next() else None,
        'previous': paginated_parent_categories.previous_page_number() if paginated_parent_categories.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_sub_categories_for_category_and_chef(request):
    payload = {}
    data = {}

    # Retrieve query parameters
    category_id = request.query_params.get('category_id', None)
    chef_id = request.query_params.get('chef_id', None)
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    # Ensure category_id and chef_id are provided
    if not category_id or not chef_id:
        return Response({'error': 'category_id and chef_id are required'}, 
                        status=status.HTTP_400_BAD_REQUEST)

    # Step 1: Ensure the category exists
    try:
        category = FoodCategory.objects.get(id=category_id)
    except FoodCategory.DoesNotExist:
        return Response({'error': 'Category with the provided category_id does not exist.'},
                        status=status.HTTP_404_NOT_FOUND)

    # Step 2: Ensure the chef has a dish in the given category
    chef_dishes = ChefDish.objects.filter(chef_id=chef_id, dish__category=category)
    if not chef_dishes.exists():
        return Response({'error': 'The provided chef does not have a dish in the specified category.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Step 3: Fetch subcategories for the given category (where parent_id=category_id)
    sub_categories = FoodCategory.objects.filter(parent_id=category_id, is_archived=False)

    # Apply search query if provided
    if search_query:
        sub_categories = sub_categories.filter(
            Q(name__icontains=search_query)
        )

    # Step 4: Paginate the results
    paginator = Paginator(sub_categories, page_size)
    try:
        paginated_sub_categories = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_sub_categories = paginator.page(1)
    except EmptyPage:
        paginated_sub_categories = paginator.page(paginator.num_pages)

    # Step 5: Serialize the subcategories
    sub_categories_serializer = AllFoodCategorysSerializer(paginated_sub_categories, many=True)

    # Prepare response data
    data['sub_categories'] = sub_categories_serializer.data
    data['pagination'] = {
        'page_number': paginated_sub_categories.number,
        'total_pages': paginator.num_pages,
        'next': paginated_sub_categories.next_page_number() if paginated_sub_categories.has_next() else None,
        'previous': paginated_sub_categories.previous_page_number() if paginated_sub_categories.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_dishes_by_category_and_chef(request):
    payload = {}
    data = {}

    # Retrieve query parameters
    category_id = request.query_params.get('category_id', None)
    chef_id = request.query_params.get('chef_id', None)
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    # Ensure category_id and chef_id are provided
    if not category_id or not chef_id:
        return Response({'error': 'category_id and chef_id are required'}, 
                        status=status.HTTP_400_BAD_REQUEST)

    # Step 1: Ensure the category exists
    try:
        category = FoodCategory.objects.get(id=category_id, is_archived=False)
    except FoodCategory.DoesNotExist:
        return Response({'error': 'FoodCategory with the provided category_id does not exist or is archived.'},
                        status=status.HTTP_404_NOT_FOUND)

    # Step 2: Ensure the chef is associated with dishes
    try:
        chef_dishes = ChefDish.objects.filter(chef_id=chef_id)
    except ChefDish.DoesNotExist:
        return Response({'error': 'Chef not found or does not have associated dishes.'},
                        status=status.HTTP_404_NOT_FOUND)

    # Step 3: Retrieve dishes based on category and associated chef
    dishes = Dish.objects.filter(category=category, is_archived=False)

    # Apply search query if provided
    if search_query:
        dishes = dishes.filter(
            Q(name__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Step 4: Filter dishes to include only those related to the specified chef
    dish_ids_for_chef = chef_dishes.values_list('dish_id', flat=True)
    dishes = dishes.filter(dish_id__in=dish_ids_for_chef)

    # Step 5: Paginate the results
    paginator = Paginator(dishes, page_size)
    try:
        paginated_dishes = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dishes = paginator.page(1)
    except EmptyPage:
        paginated_dishes = paginator.page(paginator.num_pages)

    # Step 6: Serialize the dishes
    dishes_serializer = DishSerializer(paginated_dishes, many=True)

    # Prepare response data
    data['dishes'] = dishes_serializer.data
    data['pagination'] = {
        'page_number': paginated_dishes.number,
        'total_pages': paginator.num_pages,
        'next': paginated_dishes.next_page_number() if paginated_dishes.has_next() else None,
        'previous': paginated_dishes.previous_page_number() if paginated_dishes.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)






@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_chef_dish_details(request):
    payload = {}
    data = {}
    errors = {}

    chef_id = request.query_params.get('chef_id', None)
    dish_id = request.query_params.get('dish_id', None)

    # Validate required parameters
    if not chef_id:
        errors['chef_id'] = ["Chef id is required"]
    if not dish_id:
        errors['dish_id'] = ["Dish id is required"]

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Get the ChefDish for the specific chef and dish
        chef_dish = ChefDish.objects.get(chef_id=chef_id, dish_id=dish_id)
    except ChefDish.DoesNotExist:
        errors['chef_dish'] = ['Chef-Dish combination does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Prepare the chef dish details to return
    chef_dish_details = {
        'chef_id': chef_dish.chef.id,
        'chef_name': chef_dish.chef.name,
        'dish_id': chef_dish.dish.dish_id,
        'dish_name': chef_dish.dish.name,
        'small_price': chef_dish.small_price,
        'medium_price': chef_dish.medium_price,
        'large_price': chef_dish.large_price,
        'small_value': chef_dish.small_value,
        'medium_value': chef_dish.medium_value,
        'large_value': chef_dish.large_value,
        'is_archived': chef_dish.is_archived,
        'active': chef_dish.active,
        'created_at': chef_dish.created_at,
        'updated_at': chef_dish.updated_at,
    }

    # Return the chef dish details in the response
    data['chef_dish_details'] = chef_dish_details
    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


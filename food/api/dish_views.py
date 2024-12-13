
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from food.api.serializers import AllDishsSerializer
from food.models import Dish, FoodCategory

User = get_user_model()


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_dish(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        category_id = request.data.get('category_id', "")
        cover_photo = request.data.get('cover_photo', "")
        base_price = request.data.get('base_price', "")
        quantity = request.data.get('quantity', "")


        if not name:
            errors['name'] = ['Name is required.']

        if not category_id:
            errors['category_id'] = ['Category is required.']

        if not cover_photo:
            errors['cover_photo'] = ['Cover photo is required.']

        if not base_price:
            errors['base_price'] = ['Base Price is required.']
        if not quantity:
            errors['quantity'] = ['Quantity is required.']

        if not description:
            errors['description'] = ['Description is required.']

     # Check if the name is already taken
        if Dish.objects.filter(name=name).exists():
            errors['name'] = ['A Dish with this name already exists.']

        try:
            category = FoodCategory.objects.get(id=category_id)
        except:
            errors['category_id'] = ['Food category does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        dish = Dish.objects.create(
            category=category,
            name=name,
            description=description,
            cover_photo=cover_photo,
            base_price=base_price,
            quantity=quantity,

        )

        data["dish_id"] = dish.dish_id
        data["name"] = dish.name
        data["description"] = dish.description
        data["cover_photo"] = dish.cover_photo.url
     

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_dishs_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    category = request.query_params.get('category', '')
    page_size = 10

    all_dishs = Dish.objects.all().filter(is_archived=False)


    if search_query:
        all_dishs = all_dishs.filter(
            Q(name__icontains=search_query) 
        
        ).distinct() 

        # Filter by service category if provided
    if category:
        all_dishs = all_dishs.filter(
            category__name__icontains=category
        ).distinct()

    paginator = Paginator(all_dishs, page_size)

    try:
        paginated_dishs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dishs = paginator.page(1)
    except EmptyPage:
        paginated_dishs = paginator.page(paginator.num_pages)

    all_dishs_serializer = AllDishsSerializer(paginated_dishs, many=True)


    data['dishs'] = all_dishs_serializer.data
    data['pagination'] = {
        'page_number': paginated_dishs.number,
        'total_pages': paginator.num_pages,
        'next': paginated_dishs.next_page_number() if paginated_dishs.has_next() else None,
        'previous': paginated_dishs.previous_page_number() if paginated_dishs.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_dish_details_view(request):
    payload = {}
    data = {}
    errors = {}

    dish_id = request.query_params.get('dish_id', None)

    if not dish_id:
        errors['dish_id'] = ["Dish id required"]

    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        errors['dish_id'] = ['Dish does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    dish_serializer = DishDetailsSerializer(dish, many=False)
    if dish_serializer:
        dish = dish_serializer.data

    dish_serializer = DishDetailsSerializer(dish, many=False)

    payload['message'] = "Successful"
    payload['data'] = dish

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def edit_dish(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        id = request.data.get('id', "")
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        photo = request.data.get('photo', "")


        if not name:
            errors['name'] = ['Name is required.']

        if not id:
            errors['id'] = ['ID is required.']


     # Check if the name is already taken
        if Dish.objects.filter(name=name).exists():
            errors['name'] = ['A food category with this name already exists.']

        try:
            dish = Dish.objects.get(id=id)
        except:
            errors['dish_id'] = ['Dish does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update fields only if provided and not empty
        if name:
            dish.name = name
        if description:
            dish.description = description
        if photo:
            dish.photo = photo

        dish.save()

        data["name"] = dish.name


        new_activity = AllActivity.objects.create(
            subject="Food Category Edited",
            body=f"{dish.name} was edited."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def archive_dish(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        id = request.data.get('id', "")

        if not id:
            errors['id'] = ['Food Category ID is required.']

        try:
            dish = Dish.objects.get(id=id)
        except:
            errors['id'] = ['Food Category does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.is_archived = True
        dish.save()

        new_activity = AllActivity.objects.create(
            subject="Food Category Archived",
            body="Food Category Archived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def unarchive_dish(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        id = request.data.get('id', "")

        if not id:
            errors['id'] = ['Food Category ID is required.']

        try:
            dish = Dish.objects.get(id=id)
        except:
            errors['id'] = ['Food Category does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.is_archived = False
        dish.save()

        new_activity = AllActivity.objects.create(
            subject="Food Category unarchived",
            body="Food Category unarchived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_archived_dishs_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_dishs = Dish.objects.all().filter(is_archived=True)


    if search_query:
        all_dishs = all_dishs.filter(
            Q(name__icontains=search_query) 
        
        )


    paginator = Paginator(all_dishs, page_size)

    try:
        paginated_dishs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dishs = paginator.page(1)
    except EmptyPage:
        paginated_dishs = paginator.page(paginator.num_pages)

    all_dishs_serializer = AllDishsSerializer(paginated_dishs, many=True)


    data['dishs'] = all_dishs_serializer.data
    data['pagination'] = {
        'page_number': paginated_dishs.number,
        'total_pages': paginator.num_pages,
        'next': paginated_dishs.next_page_number() if paginated_dishs.has_next() else None,
        'previous': paginated_dishs.previous_page_number() if paginated_dishs.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def delete_dish(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        id = request.data.get('id', "")

        if not id:
            errors['id'] = ['Food Category ID is required.']

        try:
            dish = Dish.objects.get(id=id)
        except:
            errors['id'] = ['Food Category does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)




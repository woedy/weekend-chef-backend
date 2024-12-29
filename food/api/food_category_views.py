
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from food.api.serializers import AllFoodCategorysSerializer
from food.models import FoodCategory

User = get_user_model()


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_food_category(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        photo = request.data.get('photo', "")


        if not name:
            errors['name'] = ['Name is required.']

        if not description:
            errors['description'] = ['Description is required.']

     # Check if the name is already taken
        if FoodCategory.objects.filter(name=name).exists():
            errors['name'] = ['A food category with this name already exists.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        food_category = FoodCategory.objects.create(
            name=name,
            description=description,
            photo=photo,

        )

        data["id"] = food_category.id
        data["name"] = food_category.name
        data["description"] = food_category.description
        data["photo"] = food_category.photo.url
     

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_food_categorys_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_food_categorys = FoodCategory.objects.all().filter(is_archived=False)


    if search_query:
        all_food_categorys = all_food_categorys.filter(
            Q(name__icontains=search_query) 
        
        )


    paginator = Paginator(all_food_categorys, page_size)

    try:
        paginated_food_categorys = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_food_categorys = paginator.page(1)
    except EmptyPage:
        paginated_food_categorys = paginator.page(paginator.num_pages)

    all_food_categorys_serializer = AllFoodCategorysSerializer(paginated_food_categorys, many=True)


    data['food_categories'] = all_food_categorys_serializer.data
    data['pagination'] = {
        'page_number': paginated_food_categorys.number,
        'total_pages': paginator.num_pages,
        'next': paginated_food_categorys.next_page_number() if paginated_food_categorys.has_next() else None,
        'previous': paginated_food_categorys.previous_page_number() if paginated_food_categorys.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_food_category_details_view(request):
    payload = {}
    data = {}
    errors = {}

    food_category_id = request.query_params.get('food_category_id', None)

    if not food_category_id:
        errors['food_category_id'] = ["FoodCategory id required"]

    try:
        food_category = FoodCategory.objects.get(food_category_id=food_category_id)
    except FoodCategory.DoesNotExist:
        errors['food_category_id'] = ['FoodCategory does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    food_category_serializer = FoodCategoryDetailsSerializer(food_category, many=False)
    if food_category_serializer:
        food_category = food_category_serializer.data

    food_category_serializer = FoodCategoryDetailsSerializer(food_category, many=False)

    payload['message'] = "Successful"
    payload['data'] = food_category

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def edit_food_category(request):
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
        if FoodCategory.objects.filter(name=name).exists():
            errors['name'] = ['A food category with this name already exists.']

        try:
            food_category = FoodCategory.objects.get(id=id)
        except:
            errors['food_category_id'] = ['FoodCategory does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update fields only if provided and not empty
        if name:
            food_category.name = name
        if description:
            food_category.description = description
        if photo:
            food_category.photo = photo

        food_category.save()

        data["name"] = food_category.name


        new_activity = AllActivity.objects.create(
            subject="Food Category Edited",
            body=f"{food_category.name} was edited."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def archive_food_category(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        id = request.data.get('id', "")

        if not id:
            errors['id'] = ['Food Category ID is required.']

        try:
            food_category = FoodCategory.objects.get(id=id)
        except:
            errors['id'] = ['Food Category does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        food_category.is_archived = True
        food_category.save()

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
def unarchive_food_category(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        id = request.data.get('id', "")

        if not id:
            errors['id'] = ['Food Category ID is required.']

        try:
            food_category = FoodCategory.objects.get(id=id)
        except:
            errors['id'] = ['Food Category does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        food_category.is_archived = False
        food_category.save()

        new_activity = AllActivity.objects.create(
            subject="Food Category unarchived.",
            body="Food Category unarchived."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_archived_food_categorys_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10

    all_food_categorys = FoodCategory.objects.all().filter(is_archived=True)


    if search_query:
        all_food_categorys = all_food_categorys.filter(
            Q(name__icontains=search_query) 
        
        )


    paginator = Paginator(all_food_categorys, page_size)

    try:
        paginated_food_categorys = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_food_categorys = paginator.page(1)
    except EmptyPage:
        paginated_food_categorys = paginator.page(paginator.num_pages)

    all_food_categorys_serializer = AllFoodCategorysSerializer(paginated_food_categorys, many=True)


    data['food_categorys'] = all_food_categorys_serializer.data
    data['pagination'] = {
        'page_number': paginated_food_categorys.number,
        'total_pages': paginator.num_pages,
        'next': paginated_food_categorys.next_page_number() if paginated_food_categorys.has_next() else None,
        'previous': paginated_food_categorys.previous_page_number() if paginated_food_categorys.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def delete_food_category(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        id = request.data.get('id', "")

        if not id:
            errors['id'] = ['Food Category ID is required.']

        try:
            food_category = FoodCategory.objects.get(id=id)
        except:
            errors['id'] = ['Food Category does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        food_category.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)





from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from food.api.serializers import AllIngredientSerializer, DishDetailsSerializer, DishIngredientDetailsSerializer
from food.models import Dish, DishIngredient

User = get_user_model()


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_ingredient(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        dish_id = request.data.get('dish_id', "")
        photo = request.data.get('photo', "")
        category = request.data.get('category', "")
        unit = request.data.get('unit', "")
        price_per_unit = request.data.get('price_per_unit', "")


        if not name:
            errors['name'] = ['Name is required.']

        if not dish_id:
            errors['dish_id'] = ['Dish is required.']

        if not photo:
            errors['photo'] = ['Photo is required.']

        if not description:
            errors['description'] = ['Description is required.']


        # Check if the name is already taken
        if DishIngredient.objects.filter(name=name).exists():
            errors['name'] = ['An ingredient with this name already exists.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        ingredient = DishIngredient.objects.create(
            dish=dish,
            name=name,
            description=description,
            photo=photo,
            category=category,
            unit=unit,
            price_per_unit=price_per_unit,
        )

        data["ingredient_id"] = ingredient.ingredient_id
        data["name"] = ingredient.name
        data["description"] = ingredient.description
        data["photo"] = ingredient.photo.url

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_ingredients_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    dish = request.query_params.get('dish', '')
    page_size = 10

    all_ingredients = DishIngredient.objects.all().filter(is_archived=False)


    if search_query:
        all_ingredients = all_ingredients.filter(
            Q(name__icontains=search_query) 
        
        ).distinct() 

        # Filter by service dish if provided
    if dish:
        all_ingredients = all_ingredients.filter(
            dish__name__icontains=dish
        ).distinct()

    paginator = Paginator(all_ingredients, page_size)

    try:
        paginated_ingredients = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_ingredients = paginator.page(1)
    except EmptyPage:
        paginated_ingredients = paginator.page(paginator.num_pages)

    all_ingredients_serializer = AllIngredientSerializer(paginated_ingredients, many=True)


    data['ingredients'] = all_ingredients_serializer.data
    data['pagination'] = {
        'page_number': paginated_ingredients.number,
        'total_pages': paginator.num_pages,
        'next': paginated_ingredients.next_page_number() if paginated_ingredients.has_next() else None,
        'previous': paginated_ingredients.previous_page_number() if paginated_ingredients.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_ingredient_details_view(request):
    payload = {}
    data = {}
    errors = {}

    ingredient_id = request.query_params.get('ingredient_id', None)

    if not ingredient_id:
        errors['ingredient_id'] = ["Ingredient id required"]

    try:
        ingredient = DishIngredient.objects.get(ingredient_id=ingredient_id)
    except:
        errors['ingredient_id'] = ['Ingredient does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    ingredient_serializer = DishIngredientDetailsSerializer(ingredient, many=False)
    if ingredient_serializer:
        ingredient = ingredient_serializer.data


    payload['message'] = "Successful"
    payload['data'] = ingredient

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def edit_ingredient_view(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        ingredient_id = request.data.get('ingredient_id', "")
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        dish_id = request.data.get('dish_id', "")
        photo = request.data.get('photo', "")
        category = request.data.get('category', "")
        unit = request.data.get('unit', "")
        price_per_unit = request.data.get('price_per_unit', "")


        if not ingredient_id:
            errors['ingredient_id'] = ['Ingredient ID is required.']

        if not name:
            errors['name'] = ['Name is required.']

        if not dish_id:
            errors['dish_id'] = ['Dish is required.']

        if not photo:
            errors['photo'] = ['Cover photo is required.']


        if not description:
            errors['description'] = ['Description is required.']

     # Check if the name is already taken
        if DishIngredient.objects.filter(name=name).exists():
            errors['name'] = ['An ingredient with this name already exists.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']

        try:
            ingredient = DishIngredient.objects.get(ingredient_id=ingredient_id)
        except:
            errors['ingredient_id'] = ['Ingredient does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update fields only if provided and not empty
        if name:
            ingredient.name = name
        if dish:
            ingredient.dish = dish
        if description:
            ingredient.description = description
        if photo:
            ingredient.photo = photo
        if category:
            ingredient.category = category
        if unit:
            ingredient.unit = unit
        if price_per_unit:
            ingredient.price_per_unit = price_per_unit
        ingredient.save()

        data["name"] = ingredient.name


        new_activity = AllActivity.objects.create(
            subject="Ingredient Edited",
            body=f"{ingredient.name} was edited."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def archive_ingredient(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        ingredient_id = request.data.get('ingredient_id', "")

        if not ingredient_id:
            errors['ingredient_id'] = ['Ingredient ID is required.']

        try:
            dish = DishIngredient.objects.get(ingredient_id=ingredient_id)
        except:
            errors['ingredient_id'] = ['Ingredient does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.is_archived = True
        dish.save()

        new_activity = AllActivity.objects.create(
            subject="Ingredient Archived",
            body="Ingredient Archived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def unarchive_ingredient(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        ingredient_id = request.data.get('ingredient_id', "")

        if not ingredient_id:
            errors['ingredient_id'] = ['Ingredient ID is required.']

        try:
            ingredient = DishIngredient.objects.get(ingredient_id=ingredient_id)
        except:
            errors['ingredient_id'] = ['Ingredient does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        ingredient.is_archived = False
        ingredient.save()

        new_activity = AllActivity.objects.create(
            subject="Ingredient unarchived",
            body="Ingredient unarchived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_unarchived_ingredient_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    dish = request.query_params.get('dish', '')
    page_size = 10

    all_ingredients = DishIngredient.objects.all().filter(is_archived=True)


    if search_query:
        all_ingredients = all_ingredients.filter(
            Q(name__icontains=search_query) 
        
        ).distinct() 

        # Filter by service dish if provided
    if dish:
        all_ingredients = all_ingredients.filter(
            dish__name__icontains=dish
        ).distinct()

    paginator = Paginator(all_ingredients, page_size)

    try:
        paginated_ingredients = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_ingredients = paginator.page(1)
    except EmptyPage:
        paginated_ingredients = paginator.page(paginator.num_pages)

    all_ingredients_serializer = AllIngredientSerializer(paginated_ingredients, many=True)


    data['ingredients'] = all_ingredients_serializer.data
    data['pagination'] = {
        'page_number': paginated_ingredients.number,
        'total_pages': paginator.num_pages,
        'next': paginated_ingredients.next_page_number() if paginated_ingredients.has_next() else None,
        'previous': paginated_ingredients.previous_page_number() if paginated_ingredients.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def delete_ingredient(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        ingredient_id = request.data.get('ingredient_id', "")

        if not ingredient_id:
            errors['ingredient_id'] = ['Ingredient ID is required.']

        try:
            ingredient = DishIngredient.objects.get(ingredient_id=ingredient_id)
        except:
            errors['ingredient_id'] = ['Ingredient does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        ingredient.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)




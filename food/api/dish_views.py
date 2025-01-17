
import json
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from chef.models import ChefProfile
from clients.api.serializers import ChefProfileSerializer, FoodCustomizationSerializer, FoodItemSerializer
from food.api.serializers import AllDishsSerializer, DishDetailIngredientSerializer, DishDetailsSerializer
from food.models import CustomizationOption, Dish, DishIngredient, FoodCategory, FoodCustomization, FoodPairing

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
        quantity = request.data.get('quantity', "")


        small_price = request.data.get('small_price', "")
        small_value = request.data.get('small_value', "")
        medium_price = request.data.get('medium_price', "")
        medium_value = request.data.get('medium_value', "")
        large_price = request.data.get('large_price', "")
        large_value = request.data.get('large_value', "")



        if not name:
            errors['name'] = ['Name is required.']

        if not category_id:
            errors['category_id'] = ['Category is required.']

        if not cover_photo:
            errors['cover_photo'] = ['Cover photo is required.']

        if not quantity:
            errors['quantity'] = ['Quantity is required.']

        if not description:
            errors['description'] = ['Description is required.']


        
        if not small_price:
            errors['small_price'] = ["Small Price required"]
        if not small_value:
            errors['small_value'] = ["Small Value required"]

        if not medium_price:
            errors['medium_price'] = ["Medium Price required"]
        if not medium_value:
            errors['medium_value'] = ["Medium Value required"]


        if not large_price:
            errors['large_price'] = ["Large Price required"]
        if not large_value:
            errors['Large_value'] = ["Large Value required"]



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
            quantity=quantity,

            small_price =small_price,
            small_value =small_value ,
            medium_price=medium_price,
            medium_value=medium_value,
            large_price =large_price ,
            large_value =large_value 

        )

        data["dish_id"] = dish.dish_id
        data["name"] = dish.name
        data["description"] = dish.description
        data["cover_photo"] = dish.cover_photo.url
     

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_dishs_view(request):
    payload = {}
    data = {}
    errors = {}

    # Get query parameters
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    categories = request.query_params.get('categories', '')  # categories is expected as a JSON string
    price_value = request.query_params.get('price', '')  # Assuming price filter exists
    page_size = 10

    # Start with all dishes, excluding archived ones
    all_dishs = Dish.objects.filter(is_archived=False)

    # Print out the categories to inspect
    print('############################')
    print(categories)

    # If 'categories' is provided in the query, parse it and filter by category IDs
    if categories:
        try:
            # Parse the categories JSON string into a Python dictionary
            category_dict = json.loads(categories)

            # Filter dishes that belong to any of the selected categories
            selected_category_ids = [int(cat_id) for cat_id, is_checked in category_dict.items() if is_checked]
            if selected_category_ids:
                all_dishs = all_dishs.filter(category__id__in=selected_category_ids).distinct()
        except json.JSONDecodeError:
            errors['categories'] = "Invalid categories format."
            return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)

    # If a search query is provided, filter by dish name
    if search_query:
        all_dishs = all_dishs.filter(Q(name__icontains=search_query)).distinct()

    # If a price filter is provided (assuming price is a range or specific value)
    #if price_value:
    #    try:
    #        price_value = float(price_value)
    #        all_dishs = all_dishs.filter(base_price__lte=price_value)
    #    except ValueError:
    #        errors['price'] = "Invalid price format."
    #        return Response({"error": errors}, status=status.HTTP_400_BAD_REQUEST)

    # Paginate the result
    paginator = Paginator(all_dishs, page_size)

    try:
        paginated_dishs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dishs = paginator.page(1)
    except EmptyPage:
        paginated_dishs = paginator.page(paginator.num_pages)

    # Serialize the paginated dishes
    all_dishs_serializer = AllDishsSerializer(paginated_dishs, many=True)

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
        _dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        errors['dish_id'] = ['Dish does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    dish_serializer = DishDetailsSerializer(_dish, many=False)
    if dish_serializer:
        dish = dish_serializer.data

    data['dish_details'] = dish


      # Get ingredients for the dish
    ingredients = DishIngredient.objects.filter(dish=_dish)
    ingredient_serializer = DishDetailIngredientSerializer(ingredients, many=True)
    ingredients = ingredient_serializer.data if ingredient_serializer else []

    data['ingredients'] = ingredients


    # Get custom options for the dish (exclude food_item from response)
    custom_options = FoodCustomization.objects.filter(food_item=_dish)
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

    data['custom_options'] = custom


    # Get only related foods (excluding the original dish)
    related_foods = FoodPairing.objects.filter(food_item=_dish).exclude(related_food=_dish).select_related('related_food')
    
    # Serialize only the related food items
    related_foods = [pair.related_food for pair in related_foods]  # Extract only the related foods
    related_foods_serializer = FoodItemSerializer(related_foods, many=True)
    related_foods = related_foods_serializer.data if related_foods_serializer else []

    data['related_foods'] = related_foods

    # Get closest chefs (if needed)
    chefs = ChefProfile.objects.all()
    chef_serializer = ChefProfileSerializer(chefs, many=True)
    dish_chefs = chef_serializer.data if chef_serializer else []

    data['chefs'] = dish_chefs

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def edit_dish_view(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_id = request.data.get('dish_id', "")
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        category_id = request.data.get('category_id', "")
        cover_photo = request.data.get('cover_photo', "")
        base_price = request.data.get('base_price', "")
        quantity = request.data.get('quantity', "")


        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']
        if not dish_id:
            errors['dish_id'] = ["Dish id required"]

        if not description:
            errors['description'] = ['Description is required.']

        # Check if the name is already taken
        #if Dish.objects.filter(name=name).exists():
         #   errors['name'] = ['A Dish with this name already exists.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']

        try:
            category = FoodCategory.objects.get(id=category_id)
        except:
            errors['category_id'] = ['Food category does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update fields only if provided and not empty
        if name:
            if name != dish.name:
                dish.name = name
        if category:
            dish.category = category
        if description:
            dish.description = description
        if cover_photo:
            dish.cover_photo = cover_photo
        if base_price:
            dish.base_price = base_price
        if quantity:
            dish.quantity = quantity

        dish.save()

        data["name"] = dish.name


        new_activity = AllActivity.objects.create(
            subject="Dish Edited",
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
        dish_id = request.data.get('dish_id', "")

        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.is_archived = True
        dish.save()

        new_activity = AllActivity.objects.create(
            subject="Dish Archived",
            body="Dish Archived"
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
        dish_id = request.data.get('dish_id', "")

        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.is_archived = False
        dish.save()

        new_activity = AllActivity.objects.create(
            subject="Dish unarchived",
            body="Dish unarchived"
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
    category = request.query_params.get('category', '')
    page_size = 10

    all_dishs = Dish.objects.all().filter(is_archived=True)


    if search_query:
        all_dishs = all_dishs.filter(
            Q(name__icontains=search_query) 
        
        ).distinct() 

        # Filter by service category if provided
    if category:
        all_dishs = all_dishs.filter(
            category__name__icontains=category
        )

    paginator = Paginator(all_dishs, page_size)

    try:
        paginated_dishs = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dishs = paginator.page(1)
    except EmptyPage:
        paginated_dishs = paginator.page(paginator.num_pages)

    all_dishs_serializer = AllDishsSerializer(paginated_dishs, many=True)


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



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def delete_dish(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_id = request.data.get('dish_id', "")

        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_related_food(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_id = request.data.get('dish_id', "")
        related_food = request.data.get('related_food', [])

        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']

        if not related_food:
            errors['related_food'] = ["Related food id required"]

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        for food_id in related_food:
            try:
                related_dish = Dish.objects.get(dish_id=food_id)
            except:
                errors['related_food'] = ['Related food does not exist.']
                payload['message'] = "Errors"
                payload['errors'] = errors
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            # Check if the pairing already exists
            if FoodPairing.objects.filter(food_item=dish, related_food=related_dish).exists():
                errors['related_food'] = [f"{dish.name} is already paired with {related_dish.name}."]
                payload['message'] = "Errors"
                payload['errors'] = errors
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            # Create new food pairing
            new_food_pair = FoodPairing.objects.create(
                food_item=dish,
                related_food=related_dish
            )

        # Create activity log
        new_activity = AllActivity.objects.create(
            subject="Food Relation added",
            body=f"{dish.name} relation was added."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_related_food_list(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_id = request.data.get('dish_id', "")
        related_food = request.data.get('related_food', [])

        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']

        if not related_food:
            errors['related_food'] = ["Related food ids are required."]

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except Dish.DoesNotExist:
            errors['dish_id'] = ['Dish does not exist.']

        # If there are errors, return them
        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        existing_pairings = FoodPairing.objects.filter(food_item=dish)

        # Initialize a list to track new pairings that were added
        new_pairings = []

        for food_id in related_food:
            try:
                related_dish = Dish.objects.get(dish_id=food_id)
            except Dish.DoesNotExist:
                errors['related_food'] = [f'Related food with ID {food_id} does not exist.']
                payload['message'] = "Errors"
                payload['errors'] = errors
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)

            # Check if the pairing already exists for the current dish and related dish
            if FoodPairing.objects.filter(food_item=dish, related_food=related_dish).exists():
                # If the pairing exists, skip it and inform the user
                errors['related_food'] = [f"{dish.name} is already paired with {related_dish.name}. Skipping."]
                continue  # Skip to the next related food
            
            # If pairing does not exist, create the new pairing
            new_food_pair = FoodPairing.objects.create(
                food_item=dish,
                related_food=related_dish
            )
            new_pairings.append(new_food_pair)

        # Check if there were any new pairings created
        if new_pairings:
            # Create activity log for successful pairing additions
            new_activity = AllActivity.objects.create(
                subject="Food Relation added",
                body=f"Relations were added for {dish.name}."
            )
            new_activity.save()

            payload['message'] = "Successful"
            payload['data'] = {'new_pairings': [pairing.related_food.dish_id for pairing in new_pairings]}
        else:
            # If no new pairings were created, return an appropriate message
            payload['message'] = "No new pairings added (all pairings already exist)."

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_dish_custom_option(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_id = request.data.get('dish_id', "")
        custom_option_id = request.data.get('custom_option_id', [])
     


        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']

        if not custom_option_id:
            errors['custom_option_id'] = ["Custom option id required"]



        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']


        try:
            custom_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
        except:
            errors['custom_option_id'] = ['Custom option does not exist.']



        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        
        new_custom = FoodCustomization.objects.create(
            food_item=dish,
            custom_option=custom_option
        )

        new_activity = AllActivity.objects.create(
            subject="Food Customization aded",
            body=f"{dish.name} customization was added."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_dish_custom_option_list(request):
    payload = {}
    errors = {}

    # Get dish_id and custom_option_ids from the request
    dish_id = request.data.get('dish_id', "")
    custom_option_ids = request.data.get('custom_option_ids', [])  # No change: we simply get a list here

    if not dish_id:
        errors['dish_id'] = ['Dish ID is required.']

    if not custom_option_ids:
        errors['custom_option_ids'] = ['At least one custom option ID is required.']

    # Validate that the dish exists
    try:
        dish = Dish.objects.get(dish_id=dish_id)
    except Dish.DoesNotExist:
        errors['dish_id'] = ['Dish does not exist.']

    # Validate that each custom_option_id exists
    custom_options = []
    for custom_option_id in custom_option_ids:
        try:
            custom_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
            custom_options.append(custom_option)
        except CustomizationOption.DoesNotExist:
            errors[f'custom_option_id_{custom_option_id}'] = [f'Custom option with ID {custom_option_id} does not exist.']

    # If there are any errors, return them
    if errors:
        payload['message'] = 'Errors occurred'
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Check if the custom options are already associated with the dish
    existing_customizations = FoodCustomization.objects.filter(food_item=dish, custom_option__in=custom_options)

    # Prepare a list of options that are not already associated with the dish
    new_customizations = [custom_option for custom_option in custom_options if custom_option not in [ec.custom_option for ec in existing_customizations]]

    # If there are any new customizations to be added
    if new_customizations:
        # Create the FoodCustomization for each valid new custom option
        for custom_option in new_customizations:
            FoodCustomization.objects.create(
                food_item=dish,
                custom_option=custom_option
            )

        # Create activity log entry
        new_activity = AllActivity.objects.create(
            subject="Food Customization added",
            body=f"Customizations were added to {dish.name}."
        )
        new_activity.save()

    # If no new customizations were added, inform the user
    if not new_customizations:
        payload['message'] = 'No new customizations added (all options already exist for this dish).'
        return Response(payload, status=status.HTTP_200_OK)

    payload['message'] = 'Success'
    payload['data'] = {'dish_id': dish_id, 'custom_option_ids': custom_option_ids}
    return Response(payload, status=status.HTTP_200_OK)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_dish_package_view(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_id = request.data.get('dish_id', "")

        small_price = request.data.get('small_price', "")
        small_value = request.data.get('small_value', "")
        medium_price = request.data.get('medium_price', "")
        medium_value = request.data.get('medium_value', "")
        large_price = request.data.get('large_price', "")
        large_value = request.data.get('large_value', "")




        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']


        if not small_price:
            errors['small_price'] = ["Small Price required"]
        if not small_value:
            errors['small_value'] = ["Small Value required"]

        if not medium_price:
            errors['medium_price'] = ["Medium Price required"]
        if not medium_value:
            errors['medium_value'] = ["Medium Value required"]


        if not large_price:
            errors['large_price'] = ["Large Price required"]
        if not large_value:
            errors['Large_value'] = ["Large Value required"]





        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)
        



        new_activity = AllActivity.objects.create(
            subject="Dish Price Addedd",
            body=f"{dish.name} price was added."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

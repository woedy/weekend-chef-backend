
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from orders.api.serializers import AllCustomizationOptionSerializer, CustomizationOptionDetailsSerializer
from orders.models import CustomizationOption

User = get_user_model()


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_custom_option(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        option_type = request.data.get('option_type', "")
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        photo = request.data.get('photo', "")
        price = request.data.get('price', "")


        if not option_type:
            errors['option_type'] = ['Option type is required.']


        if not name:
            errors['name'] = ['Name is required.']

      

        if not price:
            errors['price'] = ['Price is required.']

        if not description:
            errors['description'] = ['Description is required.']

     # Check if the name is already taken
        if CustomizationOption.objects.filter(name=name).exists():
            errors['name'] = ['A CustomizationOption with this name already exists.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        custom_option = CustomizationOption.objects.create(
            option_type=option_type,
            name=name,
            description=description,
            photo=photo,
            price=price,
        )

        data["custom_option_id"] = custom_option.custom_option_id
        data["option_type"] = custom_option.option_type
        data["name"] = custom_option.name
        data["description"] = custom_option.description
     

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_custom_options_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    category = request.query_params.get('category', '')
    page_size = 10

    all_custom_options = CustomizationOption.objects.all().filter(is_archived=False)


    if search_query:
        all_custom_options = all_custom_options.filter(
            Q(name__icontains=search_query) 
        
        ).distinct() 

        # Filter by service category if provided
    if category:
        all_custom_options = all_custom_options.filter(
            category__name__icontains=category
        ).distinct()

    paginator = Paginator(all_custom_options, page_size)

    try:
        paginated_custom_options = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_custom_options = paginator.page(1)
    except EmptyPage:
        paginated_custom_options = paginator.page(paginator.num_pages)

    all_custom_options_serializer = AllCustomizationOptionSerializer(paginated_custom_options, many=True)


    data['custom_optiones'] = all_custom_options_serializer.data
    data['pagination'] = {
        'page_number': paginated_custom_options.number,
        'total_pages': paginator.num_pages,
        'next': paginated_custom_options.next_page_number() if paginated_custom_options.has_next() else None,
        'previous': paginated_custom_options.previous_page_number() if paginated_custom_options.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_custom_option_details_view(request):
    payload = {}
    data = {}
    errors = {}

    custom_option_id = request.query_params.get('custom_option_id', None)

    if not custom_option_id:
        errors['custom_option_id'] = ["CustomizationOption id required"]

    try:
        custom_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
    except CustomizationOption.DoesNotExist:
        errors['custom_option_id'] = ['CustomizationOption does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    custom_option_serializer = CustomizationOptionDetailsSerializer(custom_option, many=False)
    if custom_option_serializer:
        custom_option = custom_option_serializer.data


    payload['message'] = "Successful"
    payload['data'] = custom_option

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def edit_custom_option_view(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        custom_option_id = request.data.get('custom_option_id', "")
        option_type = request.data.get('option_type', "")
        name = request.data.get('name', "")
        description = request.data.get('description', "")
        photo = request.data.get('photo', "")
        price = request.data.get('price', "")


        if not option_type:
            errors['option_type'] = ['Option type is required.']


        if not name:
            errors['name'] = ['Name is required.']

      

        if not price:
            errors['price'] = ['Price is required.']

        if not description:
            errors['description'] = ['Description is required.']

     # Check if the name is already taken
        if CustomizationOption.objects.filter(name=name).exists():
            errors['name'] = ['A CustomizationOption with this name already exists.']


        try:
            custom_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
        except:
            errors['custom_option_id'] = ['CustomizationOption does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update fields only if provided and not empty
        if name:
            custom_option.name = name
        if option_type:
            custom_option.option_type = option_type
        if description:
            custom_option.description = description
        if photo:
            custom_option.photo = photo
        if price:
            custom_option.price = price


        custom_option.save()

        data["name"] = custom_option.name


        new_activity = AllActivity.objects.create(
            subject="CustomizationOption Edited",
            body=f"{custom_option.name} was edited."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def archive_custom_option(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        custom_option_id = request.data.get('custom_option_id', "")

        if not custom_option_id:
            errors['custom_option_id'] = ['CustomizationOption ID is required.']

        try:
            custom_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
        except:
            errors['custom_option_id'] = ['CustomizationOption does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        custom_option.is_archived = True
        custom_option.save()

        new_activity = AllActivity.objects.create(
            subject="CustomizationOption Archived",
            body="CustomizationOption Archived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def unarchive_custom_option(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        custom_option_id = request.data.get('custom_option_id', "")

        if not custom_option_id:
            errors['custom_option_id'] = ['CustomizationOption ID is required.']

        try:
            custom_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
        except:
            errors['custom_option_id'] = ['CustomizationOption does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        custom_option.is_archived = False
        custom_option.save()

        new_activity = AllActivity.objects.create(
            subject="CustomizationOption unarchived",
            body="CustomizationOption unarchived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_archived_custom_options_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    category = request.query_params.get('category', '')
    page_size = 10

    all_custom_options = CustomizationOption.objects.all().filter(is_archived=True)


    if search_query:
        all_custom_options = all_custom_options.filter(
            Q(name__icontains=search_query) 
        
        ).distinct() 

        # Filter by service category if provided
    if category:
        all_custom_options = all_custom_options.filter(
            category__name__icontains=category
        ).distinct()

    paginator = Paginator(all_custom_options, page_size)

    try:
        paginated_custom_options = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_custom_options = paginator.page(1)
    except EmptyPage:
        paginated_custom_options = paginator.page(paginator.num_pages)

    all_custom_options_serializer = AllCustomizationOptionSerializer(paginated_custom_options, many=True)


    data['custom_optiones'] = all_custom_options_serializer.data
    data['pagination'] = {
        'page_number': paginated_custom_options.number,
        'total_pages': paginator.num_pages,
        'next': paginated_custom_options.next_page_number() if paginated_custom_options.has_next() else None,
        'previous': paginated_custom_options.previous_page_number() if paginated_custom_options.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def delete_custom_option(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        custom_option_id = request.data.get('custom_option_id', "")

        if not custom_option_id:
            errors['custom_option_id'] = ['CustomizationOption ID is required.']

        try:
            custom_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
        except:
            errors['custom_option_id'] = ['CustomizationOption does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        custom_option.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)





from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from food.api.serializers import AllDishGallerySerializer, DishDetailsSerializer, DishGalleryDetailsSerializer
from food.models import Dish, DishGallery

User = get_user_model()


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def add_dish_gallery(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        caption = request.data.get('caption', "")
        dish_id = request.data.get('dish_id', "")
        photo = request.data.get('photo', "")




        if not dish_id:
            errors['dish_id'] = ['Dish is required.']

        if not photo:
            errors['photo'] = ['Photo is required.']

        if not caption:
            errors['caption'] = ['Caption is required.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)


        dish_gallery = DishGallery.objects.create(
            dish=dish,
            caption=caption,
            photo=photo,
        )

        data["dish_gallery_id"] = dish_gallery.dish_gallery_id
        data["caption"] = dish_gallery.caption
        data["photo"] = dish_gallery.photo.url

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_dish_gallerys_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    dish = request.query_params.get('dish', '')
    page_size = 10

    all_dish_gallerys = DishGallery.objects.all().filter(is_archived=False)


    if search_query:
        all_dish_gallerys = all_dish_gallerys.filter(
            Q(caption__icontains=search_query) 
        
        ).distinct() 

        # Filter by service dish if provided
    if dish:
        all_dish_gallerys = all_dish_gallerys.filter(
            dish__caption__icontains=dish
        ).distinct()

    paginator = Paginator(all_dish_gallerys, page_size)

    try:
        paginated_dish_gallerys = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dish_gallerys = paginator.page(1)
    except EmptyPage:
        paginated_dish_gallerys = paginator.page(paginator.num_pages)

    all_dish_gallerys_serializer = AllDishGallerySerializer(paginated_dish_gallerys, many=True)


    data['dish_gallery'] = all_dish_gallerys_serializer.data
    data['pagination'] = {
        'page_number': paginated_dish_gallerys.number,
        'total_pages': paginator.num_pages,
        'next': paginated_dish_gallerys.next_page_number() if paginated_dish_gallerys.has_next() else None,
        'previous': paginated_dish_gallerys.previous_page_number() if paginated_dish_gallerys.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_dish_gallery_details_view(request):
    payload = {}
    data = {}
    errors = {}

    dish_gallery_id = request.query_params.get('dish_gallery_id', None)

    if not dish_gallery_id:
        errors['dish_gallery_id'] = ["DishGallery id required"]

    try:
        dish_gallery = DishGallery.objects.get(dish_gallery_id=dish_gallery_id)
    except:
        errors['dish_gallery_id'] = ['DishGallery does not exist.']

    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    dish_gallery_serializer = DishGalleryDetailsSerializer(dish_gallery, many=False)
    if dish_gallery_serializer:
        dish_gallery = dish_gallery_serializer.data


    payload['message'] = "Successful"
    payload['data'] = dish_gallery

    return Response(payload, status=status.HTTP_200_OK)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def edit_dish_gallery(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_gallery_id = request.data.get('dish_gallery_id', "")
        caption = request.data.get('caption', "")
        dish_id = request.data.get('dish_id', "")
        photo = request.data.get('photo', "")


        if not dish_gallery_id:
            errors['dish_gallery_id'] = ['DishGallery ID is required.']


        if not dish_id:
            errors['dish_id'] = ['Dish is required.']

        if not photo:
            errors['photo'] = ['Cover photo is required.']


        if not caption:
            errors['caption'] = ['Caption is required.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except:
            errors['dish_id'] = ['Dish does not exist.']

        try:
            dish_gallery = DishGallery.objects.get(dish_gallery_id=dish_gallery_id)
        except:
            errors['dish_gallery_id'] = ['DishGallery does not exist.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update fields only if provided and not empty

        if dish:
            dish_gallery.dish = dish
        if caption:
            dish_gallery.caption = caption
        if photo:
            dish_gallery.photo = photo
        dish_gallery.save()

        data["caption"] = dish_gallery.caption


        new_activity = AllActivity.objects.create(
            subject="DishGallery Edited",
            body=f"{ingredient.caption} was edited."
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def archive_dish_gallery(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_gallery_id = request.data.get('dish_gallery_id', "")

        if not dish_gallery_id:
            errors['dish_gallery_id'] = ['Dish Gallery ID is required.']

        try:
            dish = DishGallery.objects.get(dish_gallery_id=dish_gallery_id)
        except:
            errors['dish_gallery_id'] = ['Dish Gallery does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.is_archived = True
        dish.save()

        new_activity = AllActivity.objects.create(
            subject="Dish Gallery Archived",
            body="DishGallery Archived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)

@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def unarchive_dish_gallery(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_gallery_id = request.data.get('dish_gallery_id', "")

        if not dish_gallery_id:
            errors['dish_gallery_id'] = ['Dish Gallery ID is required.']

        try:
            dish = DishGallery.objects.get(dish_gallery_id=dish_gallery_id)
        except:
            errors['dish_gallery_id'] = ['Dish Gallery does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        dish.is_archived = False
        dish.save()

        new_activity = AllActivity.objects.create(
            subject="Dish Gallery unArchived",
            body="DishGallery unArchived"
        )
        new_activity.save()

        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)




@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_all_archived_dish_gallerys_view(request):
    payload = {}
    data = {}
    errors = {}

    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    dish = request.query_params.get('dish', '')
    page_size = 10

    all_dish_gallerys = DishGallery.objects.all().filter(is_archived=True)


    if search_query:
        all_dish_gallerys = all_dish_gallerys.filter(
            Q(caption__icontains=search_query) 
        
        ).distinct() 

        # Filter by service dish if provided
    if dish:
        all_dish_gallerys = all_dish_gallerys.filter(
            dish__caption__icontains=dish
        ).distinct()

    paginator = Paginator(all_dish_gallerys, page_size)

    try:
        paginated_dish_gallerys = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_dish_gallerys = paginator.page(1)
    except EmptyPage:
        paginated_dish_gallerys = paginator.page(paginator.num_pages)

    all_dish_gallerys_serializer = AllDishGallerySerializer(paginated_dish_gallerys, many=True)


    data['dish_gallery'] = all_dish_gallerys_serializer.data
    data['pagination'] = {
        'page_number': paginated_dish_gallerys.number,
        'total_pages': paginator.num_pages,
        'next': paginated_dish_gallerys.next_page_number() if paginated_dish_gallerys.has_next() else None,
        'previous': paginated_dish_gallerys.previous_page_number() if paginated_dish_gallerys.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


@api_view(['POST', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def delete_dish_gallery(request):
    payload = {}
    data = {}
    errors = {}

    if request.method == 'POST':
        dish_gallery_id = request.data.get('dish_gallery_id', "")

        if not dish_gallery_id:
            errors['dish_gallery_id'] = ['Dish Gallery ID is required.']

        try:
            ingredient = DishGallery.objects.get(dish_gallery_id=dish_gallery_id)
        except:
            errors['dish_gallery_id'] = ['Dish Gallery does not exist.']


        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        ingredient.delete()


        payload['message'] = "Successful"
        payload['data'] = data

    return Response(payload)




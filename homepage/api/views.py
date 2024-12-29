
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from food.api.serializers import AllFoodCategorysSerializer
from food.models import FoodCategory
from homepage.api.serializers import HomeFoodCategorysSerializer


@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_homepage_data_view(request):
    payload = {}
    data = {}
    errors = {}

    user_data = {}
    notification_count = 0
    dish_categories = []

    user_id = request.query_params.get('user_id', None)
    
    if user_id is None:
        errors['user_id'] = "User ID is required"

    try:
        user = get_user_model().objects.get(user_id=user_id)
    except:
        errors['user_id'] = ['User does not exist.']    
        
    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)
    

    categories = FoodCategory.objects.all()
    category_serializer = HomeFoodCategorysSerializer(categories, many=True)
    if category_serializer:
        dish_categories = category_serializer.data

    notifications = user.notifications.all().filter(read=False)
    notification_count = notifications.count()
    
    user_data['user_id'] = user.user_id
    user_data['first_name'] = user.first_name
    user_data['last_name'] = user.last_name
    user_data['photo'] = user.photo.url




    data['user_data'] = user_data
    data['notification_count'] = notification_count
    data['dish_categories'] = dish_categories

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)


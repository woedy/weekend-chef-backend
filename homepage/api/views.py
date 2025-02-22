
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from food.api.serializers import AllFoodCategorysSerializer
from food.models import Dish, FoodCategory
from homepage.api.serializers import HomeDishsSerializer, HomeFoodCategorysSerializer
from orders.models import Cart, Order


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
    

    categories = FoodCategory.objects.filter(is_archived=False, parent__isnull=True)
    category_serializer = HomeFoodCategorysSerializer(categories, many=True)
    if category_serializer:
        dish_categories = category_serializer.data

    notifications = user.notifications.all().filter(read=False)
    notification_count = notifications.count()

    # Safely handle cart
    cart = Cart.objects.filter(client__user=user).first()
    cart_item_count = cart.items.all().count() if cart else 0

    all_dishs = Dish.objects.filter(is_archived=False)[:10]
    all_dishs_serializer = HomeDishsSerializer(all_dishs, many=True)



    user_data['user_id'] = user.user_id
    user_data['first_name'] = user.first_name
    user_data['last_name'] = user.last_name
    user_data['photo'] = user.photo.url

    data['user_data'] = user_data
    data['notification_count'] = notification_count
    data['dish_categories'] = dish_categories
    data['cart_item_count'] = cart_item_count
    data['popular'] = all_dishs_serializer.data

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)






@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_admin_dashboard_data_view(request):
    payload = {}
    data = {}
    errors = {}

    user_data = {}
    notification_count = 0

    total_sales = 0
    total_customers = 0
    total_chefs = 0

    pending_orders = 0  
    accepted_orders = 0
    preparation_orders = 0
    delivery_orders = 0


        
    if errors:
        payload['message'] = "Errors"
        payload['errors'] = errors
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)
    
    orders = Order.objects.all()
    order_count = orders.count()
    print(order_count)
    data['orders_count'] = order_count

    data['total_sales'] = total_sales
    data['total_customers'] = total_customers
    data['total_chefs'] = total_chefs

    data['pending_orders'] = pending_orders
    data['accepted_orders'] = accepted_orders
    data['preparation_orders'] = preparation_orders
    data['delivery_orders'] = delivery_orders

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET', ])
@permission_classes([IsAuthenticated, ])
@authentication_classes([TokenAuthentication, ])
def get_chef_homepage_data_view(request):
    payload = {}
    data = {}
    errors = {}

    user_data = {}
    notification_count = 0
    total_sales = 0
    pending_order_count = 0
    total_order_count = 0
    pending_orders_list = []
    availability =  {}

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
    

    notifications = user.notifications.all().filter(read=False)
    notification_count = notifications.count()



    user_data['user_id'] = user.user_id
    user_data['first_name'] = user.first_name
    user_data['last_name'] = user.last_name
    user_data['photo'] = user.photo.url

    data['user_data'] = user_data
    data['notification_count'] = notification_count

    data['total_sales'] = total_sales
    data['pending_order_count'] = pending_order_count
    data['total_order_count'] = total_order_count
    data['pending_orders_list'] = pending_orders_list
    data['availability'] = availability

    total_sales = 0
    pending_order_count = 0
    total_order_count = 0
    pending_orders_list = []
    availability =  {}


    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)



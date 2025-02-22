from datetime import datetime
from time import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from chef.models import ChefProfile
from orders.api.order_serializers import ChefOrderItemSerializer, ChefOrderSerializer, OrderItemSerializer, OrderSerializer
from orders.models import  Order, OrderItem, OrderStatus





@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_chef_orders_view(request):
    payload = {}
    data = {}
    errors = {}

    # Extract query parameters
    user_id = request.query_params.get('user_id', None)
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10  # You can make this configurable as well

    # Start with all orders
    orders = Order.objects.all()

    # Filter by chef_id if provided
    if user_id:
        try:
            chef = ChefProfile.objects.get(chef_user_id=user_id)
            orders = orders.filter(chef=chef, status="Pending")
        except ChefProfile.DoesNotExist:
            errors['chef_id'] = ['Chef with the given ID does not exist.']
            return Response({'message': 'Errors', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

    # Search functionality
    if search_query:
        orders = orders.filter(
            Q(order_id__icontains=search_query) |
            Q(location_name__icontains=search_query) |
            Q(digital_address__icontains=search_query) |
            Q(status__icontains=search_query)  # Assuming 'status' is a field you want to search
        ).distinct()

    # Pagination
    paginator = Paginator(orders, page_size)

    try:
        paginated_orders = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_orders = paginator.page(1)
    except EmptyPage:
        paginated_orders = paginator.page(paginator.num_pages)

    # Serialize the orders
    orders_serializer = ChefOrderSerializer(paginated_orders, many=True)

    # Prepare the data for pagination
    data['orders'] = orders_serializer.data
    data['pagination'] = {
        'page_number': paginated_orders.number,
        'total_pages': paginator.num_pages,
        'next': paginated_orders.next_page_number() if paginated_orders.has_next() else None,
        'previous': paginated_orders.previous_page_number() if paginated_orders.has_previous() else None,
    }

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)





status_choices = [
    ('Review', 'Review'),
        ('Pending', 'Pending'),
        ('Initiated', 'Initiated'),
        ('Cooking', 'Cooking'),
        ('Completed', 'Completed'),
]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def change_chef_order_status_view(request):
    payload = {}
    errors = {}

    if request.method == 'POST':
        # Extract data from the request
        order_id = request.data.get('order_id')
        new_status = request.data.get('status')

        # Validate the status
        if not new_status:
            errors['status'] = ['Status is required.']
        elif new_status not in dict(status_choices).keys():
            errors['status'] = ['Invalid status. Valid statuses are: Pending, Shipped, Delivered, Cancelled.']

        if not order_id:
            errors['order_id'] = ['Order ID is required.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the order
            order = Order.objects.get(order_id=order_id)

            # Get the current status of the order
            current_status = order.order_statuses.last()

            # If no status has been assigned yet, the default is 'Pending'
            if current_status:
                current_status = current_status.status
            else:
                current_status = 'Pending'

            # If the order is already in a final state (e.g., Delivered or Cancelled), prevent further status updates
            if current_status in ['Delivered', 'Cancelled']:
                errors['status'] = ['This order has already been completed or cancelled and cannot be updated.']
                return Response({'message': 'Errors', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

            # Optionally, you can define allowed status transitions
            allowed_transitions = {
                'Pending': ['Shipped', 'Cancelled'],
                'Shipped': ['Delivered', 'Cancelled'],
                'Delivered': [],
                'Cancelled': [],
            }

            # Check if the status change is allowed
            if new_status not in allowed_transitions.get(current_status, []):
                errors['status'] = [f"Cannot transition from {current_status} to {new_status}."]
                return Response({'message': 'Errors', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

            # Create a new OrderStatus entry with the new status
            order_status = OrderStatus(
                order=order,
                status=new_status,
                created_at=timezone.now()
            )
            order_status.save()

            # Return success response
            return Response({
                'message': 'Order status updated successfully.',
                'data': {
                    'order_id': order.id,
                    'new_status': new_status,
                    'created_at': order_status.created_at,
                }
            }, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            errors['order_id'] = ['Order not found.']
            return Response({'message': 'Errors', 'errors': errors}, status=status.HTTP_404_NOT_FOUND)






@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_chef_order_details_view(request):
    payload = {}
    data = {}
    errors = {}

    order_id = request.query_params.get('order_id', '')

    # Retrieve the order by its ID or return a 404 if not found
    order = get_object_or_404(Order, order_id=order_id)


    # Serialize the order data
    order_serializer = OrderSerializer(order)

    # Get the order items for this order
    order_items = OrderItem.objects.filter(order=order)
    order_item_serializer = ChefOrderItemSerializer(order_items, many=True)

    # Fetch the order status history
    order_statuses = OrderStatus.objects.filter(order=order).order_by('created_at')
    order_status_data = [
        {"status": status.status, "created_at": status.created_at} for status in order_statuses
    ]

    # Prepare the response data
    data['order'] = order_serializer.data
    data['order_items'] = order_item_serializer.data
    data['order_statuses'] = order_status_data

    payload['message'] = "Successful"
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

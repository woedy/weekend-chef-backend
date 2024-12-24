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
from django.utils.crypto import get_random_string
from django.db import transaction
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from clients.models import Client
from orders.api.order_serializers import OrderItemSerializer, OrderSerializer
from orders.models import Cart, Order, OrderItem, OrderPayment, OrderStatus



@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def place_order_view(request):
    payload = {}
    errors = {}

    if request.method == 'POST':
        # Extract client information from the request
        client_id = request.data.get('client_id')
        order_date = request.data.get('order_date')
        order_time = request.data.get('order_time')
        delivery_date = request.data.get('delivery_date')
        delivery_time = request.data.get('delivery_time')
        location_name = request.data.get('location_name')
        digital_address = request.data.get('digital_address')
        lat = request.data.get('lat')
        lng = request.data.get('lng')
        delivery_fee = request.data.get('delivery_fee')
        tax = request.data.get('tax')

        # Validate client_id
        if not client_id:
            errors['client_id'] = ['Client ID is required.']
        else:
            try:
                client = Client.objects.get(client_id=client_id)
            except Client.DoesNotExist:
                errors['client_id'] = ['Client does not exist.']

        if errors.get('client_id'):
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Validate other fields like order_date, delivery_date, location_name, etc.
        # (same validation as before)

        # Validate if the client has an active cart
        try:
            cart = Cart.objects.get(client=client, purchased=False)
        except Cart.DoesNotExist:
            errors['cart'] = ['No active cart available for placing an order.']

        if not cart.items.exists():
            errors['cart'] = ['The cart does not contain any items.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Create the order
        with transaction.atomic():
            # Create the Order instance
            order = Order(
                client=client,
                total_price=0,  # Will be updated later
                paid=False,
                room=None,  # Optional or add from request if needed
                order_date=order_date,
                order_time=order_time,
                delivery_date=delivery_date,
                delivery_time=delivery_time,
                location_name=location_name,
                digital_address=digital_address,
                lat=lat,
                lng=lng,
                delivery_fee=delivery_fee,
                tax=tax
            )
            order.save()

            # Add items from the cart to the order
            for cart_item in cart.items.all():
                # Create the OrderItem and associate it with the Order
                order_item = OrderItem(
                    order=order,
                    cart_item=cart_item,  # Link to CartItem (which includes customizations)
                    quantity=cart_item.quantity
                )
                order_item.save()

            # Update the total price for the order (this will calculate based on CartItems)
            order.update_total_price()

            # Set the order status to 'Pending'
            OrderStatus.objects.create(order=order, status='Pending')

            # Mark the cart as purchased
            cart.purchased = True
            cart.save()

        # Prepare the response data
        order_data = {
            'order_id': order.order_id,
            'total_price': order.total_price,
            'order_date': order.order_date,
            'order_time': order.order_time,
            'status': 'Pending',
        }

        return Response({
            'message': 'Order placed successfully.',
            'data': order_data
        }, status=status.HTTP_201_CREATED)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def make_order_payment_view(request):
    payload = {}
    errors = {}

    if request.method == 'POST':
        # Extract required fields from the request data
        order_id = request.data.get('order_id')
        payment_method = request.data.get('payment_method')
        amount = request.data.get('amount')

        # Validate the inputs
        if not order_id:
            errors['order_id'] = ['Order ID is required.']
        
        if not payment_method:
            errors['payment_method'] = ['Payment method is required.']

        if not amount:
            errors['amount'] = ['Amount is required.']
        else:
            try:
                # Convert amount to Decimal for precise monetary calculations
                amount = Decimal(amount)
                if amount <= 0:
                    errors['amount'] = ['Amount must be greater than zero.']
            except (ValueError, TypeError):
                errors['amount'] = ['Amount must be a valid number.']

        if errors:
            payload['message'] = "Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve the order
            order = Order.objects.get(order_id=order_id)

            # Check if the order has already been paid
            if order.paid:
                errors['order'] = ['This order has already been paid for.']
                return Response({'message': 'Errors', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        except Order.DoesNotExist:
            errors['order_id'] = ['Order does not exist.']
            return Response({'message': 'Errors', 'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        # Proceed with the payment creation
        with transaction.atomic():  # Ensure payment creation is atomic
            # Create the OrderPayment instance
            payment = OrderPayment(
                order=order,
                payment_method=payment_method,
                amount=str(amount)  # Store the amount as a string or Decimal in your DB
            )
            payment.save()

            # Update the order's paid status if the amount matches the total price
            # For simplicity, assume a single payment is being made at a time
            total_paid = sum(Decimal(p.amount) for p in order.order_payments.all())  # Get the total paid so far
            if total_paid >= order.total_price:  # If the total payments cover the order price
                order.paid = True
                order.save()

        # Return the response with payment details
        payment_data = {
            'order_id': order.id,
            'payment_method': payment.payment_method,
            'amount': payment.amount,
            'created_at': payment.created_at,
        }

        return Response({
            'message': 'Payment processed successfully.',
            'data': payment_data
        }, status=status.HTTP_201_CREATED)

status_choices = [
    ('Pending', 'Pending'),
    ('Shipped', 'Shipped'),
    ('Delivered', 'Delivered'),
    ('Cancelled', 'Cancelled'),
]

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def change_order_status_view(request):
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
def get_all_orders_view(request):
    payload = {}
    data = {}
    errors = {}

    # Extract query parameters
    client_id = request.query_params.get('client_id', None)
    search_query = request.query_params.get('search', '')
    page_number = request.query_params.get('page', 1)
    page_size = 10  # You can make this configurable as well

    # Start with all orders
    orders = Order.objects.all()

    # Filter by client_id if provided
    if client_id:
        try:
            client = Client.objects.get(client_id=client_id)
            orders = orders.filter(client=client)
        except Client.DoesNotExist:
            errors['client_id'] = ['Client with the given ID does not exist.']
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
    orders_serializer = OrderSerializer(paginated_orders, many=True)

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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_order_details_view(request):
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
    order_item_serializer = OrderItemSerializer(order_items, many=True)

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







@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_order_payment(request, payment_id):
    """
    View to update the payment details for a specific payment.
    """
    payload = {}
    data = {}

    try:
        # Retrieve the payment
        payment = OrderPayment.objects.get(id=payment_id)

        # Ensure the user making the request has permission to update this payment
        if payment.order.client.user != request.user and not request.user.is_staff:
            payload['message'] = "You do not have permission to update this payment."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Get the updated payment details
        payment_method = request.data.get('payment_method')
        amount = request.data.get('amount')

        if payment_method:
            payment.payment_method = payment_method

        if amount:
            payment.amount = amount

        payment.save()

        # Return the updated payment details
        data['payment_method'] = payment.payment_method
        data['amount'] = payment.amount
        data['message'] = "Payment updated successfully."

        return Response(data, status=status.HTTP_200_OK)

    except ObjectDoesNotExist:
        payload['message'] = "Payment not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        payload['message'] = str(e)
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_order_payment(request, payment_id):
    """
    View to delete a payment for a specific order.
    """
    payload = {}

    try:
        # Retrieve the payment
        payment = OrderPayment.objects.get(id=payment_id)

        # Ensure the user making the request has permission to delete this payment
        if payment.order.client.user != request.user and not request.user.is_staff:
            payload['message'] = "You do not have permission to delete this payment."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Deactivate the payment (mark as inactive)
        payment.active = False
        payment.save()

        payload['message'] = "Payment deleted successfully."
        return Response(payload, status=status.HTTP_204_NO_CONTENT)

    except ObjectDoesNotExist:
        payload['message'] = "Payment not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        payload['message'] = str(e)
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)





@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def generate_shopping_list_for_order_item(request):
    """
    Generate a shopping list for a single order item in the order, including prices and a total shopping price.
    """
    payload = {}
    data = []
    errors = {}
    total_quantity = 0  # Initialize total quantity
    total_price = 0  # Initialize total price for the shopping list


    order_id = request.data.get('order_id', "")
    order_item_id = request.data.get('order_item_id', "")


    try:
        # Fetch the Order
        order = Order.objects.get(order_id=order_id)
    except Order.DoesNotExist:
        payload['message'] = 'Order not found.'
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    # Fetch the specific OrderItem
    try:
        order_item = OrderItem.objects.get(id=order_item_id, order=order)
    except OrderItem.DoesNotExist:
        payload['message'] = 'Order item not found in this order.'
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    # Initialize a dictionary to store ingredients and their total quantities
    shopping_list = {}

    # Get the dish for this order item
    dish = order_item.cart.dish  # The dish ordered in this order item

    # Add ingredients from the dish itself
    for ingredient in dish.ingredients.all():
        total_quantity += ingredient.quantity * order_item.quantity  # Add to total quantity
        ingredient_total_price = ingredient.price * ingredient.quantity * order_item.quantity  # Calculate price for the ingredient
        total_price += ingredient_total_price  # Add to total price

        if ingredient.name in shopping_list:
            shopping_list[ingredient.name]['quantity'] += ingredient.quantity * order_item.quantity
            shopping_list[ingredient.name]['total_price'] += ingredient_total_price
        else:
            shopping_list[ingredient.name] = {
                'ingredient': ingredient,
                'quantity': ingredient.quantity * order_item.quantity,
                'unit': ingredient.unit,
                'price_per_unit': ingredient.price,
                'total_price': ingredient_total_price
            }

    # Handle customizations for this order item (if any)
    for customization in order_item.customizations.all():
        customization_ingredient = customization.customization_option.ingredient  # Assuming a relationship exists
        if customization_ingredient:
            total_quantity += customization_ingredient.quantity * order_item.quantity  # Add to total quantity
            ingredient_total_price = customization_ingredient.price * customization_ingredient.quantity * order_item.quantity  # Calculate price for the customization ingredient
            total_price += ingredient_total_price  # Add to total price

            if customization_ingredient.name in shopping_list:
                shopping_list[customization_ingredient.name]['quantity'] += customization_ingredient.quantity * order_item.quantity
                shopping_list[customization_ingredient.name]['total_price'] += ingredient_total_price
            else:
                shopping_list[customization_ingredient.name] = {
                    'ingredient': customization_ingredient,
                    'quantity': customization_ingredient.quantity * order_item.quantity,
                    'unit': customization_ingredient.unit,
                    'price_per_unit': customization_ingredient.price,
                    'total_price': ingredient_total_price
                }

    # Prepare the shopping list data
    for ingredient_name, ingredient_data in shopping_list.items():
        data.append({
            'ingredient': ingredient_data['ingredient'].name,
            'quantity': ingredient_data['quantity'],
            'unit': ingredient_data['unit'],
            'price_per_unit': str(ingredient_data['price_per_unit']),
            'total_price': str(ingredient_data['total_price'])
        })

    # Add the total quantity and total price to the response
    payload['message'] = 'Shopping list generated successfully.'
    payload['total_quantity'] = total_quantity  # Add total quantity to the payload
    payload['total_price'] = str(total_price)  # Add total price to the payload
    payload['data'] = data

    return Response(payload, status=status.HTTP_200_OK)

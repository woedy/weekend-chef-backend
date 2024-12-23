from datetime import datetime
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from django.utils.crypto import get_random_string
from django.db import transaction

from clients.models import Client
from orders.models import Cart, Order, OrderItem, OrderStatus



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
def create_order_payment(request, order_id):
    """
    View to create a payment for an order.
    """
    payload = {}
    data = {}

    try:
        # Retrieve the order
        order = Order.objects.get(id=order_id)

        # Check if the authenticated user is authorized to make payments for this order
        # For simplicity, we assume clients can only make payments for their own orders
        if order.client.user != request.user:
            payload['message'] = "You do not have permission to make a payment for this order."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Get payment details from the request
        payment_method = request.data.get('payment_method')
        amount = request.data.get('amount')

        if not payment_method:
            payload['message'] = "Payment method is required."
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        if not amount:
            payload['message'] = "Payment amount is required."
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Create an order payment record
        payment = OrderPayment.objects.create(
            order=order,
            payment_method=payment_method,
            amount=amount,
            active=True  # Payment is active by default
        )

        # Update the order's total payment (if needed)
        # Here, we can track the total payments made for the order

        order.update_total_price()  # Assuming update_total_price method exists for handling payments

        # Return success response with payment details
        data['order_id'] = order.id
        data['payment_method'] = payment.payment_method
        data['amount'] = payment.amount
        data['message'] = "Payment created successfully."

        return Response(data, status=status.HTTP_201_CREATED)

    except ObjectDoesNotExist:
        payload['message'] = "Order not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        payload['message'] = str(e)
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)


    except Exception as e:
        payload['message'] = str(e)
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)






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




@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def list_all_orders(request):
    """
    View to list all orders with optional filters by client, chef, dispatch, or search by order ID or dish name.
    """
    payload = {}
    data = []

    # Retrieve query parameters for filtering
    client_id = request.query_params.get('client', None)
    chef_id = request.query_params.get('chef', None)
    dispatch_id = request.query_params.get('dispatch', None)
    search_query = request.query_params.get('search', None)  # Search by order ID or dish name

    # Base query to fetch orders
    orders = Order.objects.all()

    # Apply filters based on query parameters
    if client_id:
        orders = orders.filter(client__id=client_id)

    if chef_id:
        orders = orders.filter(chef__id=chef_id)

    if dispatch_id:
        orders = orders.filter(dispatch__id=dispatch_id)

    # Search by order ID or dish name
    if search_query:
        orders = orders.filter(
            Q(id__icontains=search_query) | 
            Q(items__dish__name__icontains=search_query)
        ).distinct()

    # Serialize the orders into a list of dictionaries
    for order in orders:
        order_data = {
            'order_id': order.id,
            'order_date': order.order_date,
            'status': order.status,
            'total_price': order.total_price,
            'client': order.client.user.username,  # Assuming user is related to client
            'chef': order.chef.user.username,  # Assuming user is related to chef
            'dispatch': order.dispatch.user.username,  # Assuming user is related to dispatch
            'delivery_date': order.delivery_date,
            'delivery_time': order.delivery_time,
        }
        data.append(order_data)

    if not data:
        payload['message'] = "No orders found with the given filters."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    payload['data'] = data
    return Response(payload, status=status.HTTP_200_OK)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def order_detail_view(request, order_id):
    """
    View to get the details of a specific order.
    It includes order details, client, chef, dispatch, order items, and payment information.
    """
    try:
        # Retrieve the order by order_id
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise NotFound("Order not found.")

    # Ensure the authenticated user has permission to view the order
    if order.client.user != request.user and order.chef.user != request.user and order.dispatch.user != request.user:
        raise PermissionDenied("You do not have permission to view this order.")

    # Serialize the order with its related data
    serializer = OrderDetailSerializer(order)

    # Return the serialized order data
    return Response({
        'message': 'Order details fetched successfully.',
        'data': serializer.data
    }, status=status.HTTP_200_OK)





@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def generate_shopping_list_for_order_item(request, order_id, order_item_id):
    """
    Generate a shopping list for a single order item in the order, including prices and a total shopping price.
    """
    payload = {}
    data = []
    errors = {}
    total_quantity = 0  # Initialize total quantity
    total_price = 0  # Initialize total price for the shopping list

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

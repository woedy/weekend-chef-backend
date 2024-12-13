from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from django.core.exceptions import ObjectDoesNotExist
from .models import Order, OrderItem, Dish, Client, ChefProfile, DispatchDriver, OrderStatus, Cart
from rest_framework.exceptions import ValidationError
from django.utils.crypto import get_random_string


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def place_order(request):
    """
    Place a new order for the client, creating order items and order statuses.
    """
    payload = {}
    data = {}

    # Get the client from the authenticated user
    client = request.user.client  # Assuming the Client model is related to User model
    client_id = request.data.get('client_id')
    chef_id = request.data.get('chef_id')
    dispatch_id = request.data.get('dispatch_id')

    if not client_id or client.id != client_id:
        payload['message'] = 'Client ID is invalid or does not match the authenticated user.'
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Fetch chef and dispatch details
        chef = ChefProfile.objects.get(id=chef_id)
        dispatch_driver = DispatchDriver.objects.get(id=dispatch_id)

    except ObjectDoesNotExist:
        payload['message'] = 'Invalid Chef or Dispatch Driver.'
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Get order items
    order_items_data = request.data.get('order_items', [])
    if not order_items_data:
        payload['message'] = 'Order items are required.'
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Generate a unique order_id (can be enhanced with your logic)
    order_id = get_random_string(length=8).upper()

    # Initialize total price
    total_price = 0

    # Create the order
    order = Order.objects.create(
        order_id=order_id,
        client=client,
        chef=chef,
        dispatch=dispatch_driver,
        status='Pending',  # Initially set to Pending
        total_price=total_price,  # This will be updated after the items are processed
        paid=False,  # Payment status
        order_date=request.data.get('order_date'),
        order_time=request.data.get('order_time'),
        delivery_date=request.data.get('delivery_date'),
        delivery_time=request.data.get('delivery_time'),
        location_name=request.data.get('location_name'),
        digital_address=request.data.get('digital_address'),
        lat=request.data.get('lat', 0.0),
        lng=request.data.get('lng', 0.0),
        delivery_fee=request.data.get('delivery_fee', 0.0),
        tax=request.data.get('tax', 0.0),
    )

    # Create order items (dishes) and link them to the order
    for item_data in order_items_data:
        try:
            cart = Cart.objects.get(id=item_data['cart_id'])  # Assuming Cart ID is given in the request
        except Cart.DoesNotExist:
            payload['message'] = f"Cart with ID {item_data['cart_id']} not found."
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

        # Create OrderItem and link it to the order
        order_item = OrderItem.objects.create(
            order=order,
            cart=cart,
            quantity=item_data['quantity'],
        )

        # Handle customizations if present
        customizations = item_data.get('customizations', [])
        if customizations:
            try:
                customization_values = []
                for customization in customizations:
                    customization_id = customization.get('id')
                    customization_quantity = customization.get('quantity', 1)  # Default to 1 if no quantity is provided

                    # Fetch the CustomizationValue object
                    customization_value = CustomizationValue.objects.get(id=customization_id)
                    
                    # Check if customization quantity is valid (e.g., must be positive)
                    if customization_quantity <= 0:
                        raise ValidationError("Customization quantity must be greater than 0.")

                    # Assign the customization value and quantity
                    customization_value.quantity = customization_quantity
                    customization_values.append(customization_value)

                # Link customizations to the order item
                order_item.customizations.set(customization_values)

            except CustomizationValue.DoesNotExist:
                order_item.delete()  # Clean up if error occurs
                return Response({
                    'message': "Customization Error",
                    'errors': {'customizations': ['One or more customizations not found.']}
                }, status=status.HTTP_404_NOT_FOUND)
            except ValidationError as e:
                order_item.delete()  # Clean up if validation fails
                return Response({
                    'message': "Invalid Customization Quantity",
                    'errors': {'customizations': [str(e)]}
                }, status=status.HTTP_400_BAD_REQUEST)

        # Recalculate the total price for this order item, including customizations
        total_price += order_item.total_price()

    # Update the order's total price
    order.total_price = total_price
    order.save()

    # Create initial order status (Pending)
    OrderStatus.objects.create(
        order=order,
        status='Pending',
    )

    # Mark the cart as archived or inactive
    cart.is_archived = True  # Or `cart.is_active = False`
    cart.save()

    # Prepare the response data
    data = {
        'order_id': order.order_id,
        'status': order.status,
        'total_price': str(order.total_price),
        'delivery_fee': str(order.delivery_fee),
        'tax': str(order.tax),
        'order_date': str(order.order_date),
        'order_time': str(order.order_time),
        'delivery_date': str(order.delivery_date),
        'delivery_time': str(order.delivery_time),
        'location_name': order.location_name,
        'digital_address': order.digital_address,
        'lat': str(order.lat),
        'lng': str(order.lng),
        'client': order.client.user.username,
        'chef': order.chef.user.username,
        'dispatch_driver': order.dispatch.user.username,
        'order_items': [
            {
                'dish': item.cart.dish.name,
                'quantity': item.quantity,
                'total_price': str(item.total_price()),
                'customizations': [
                    {
                        'customization': cv.customization_option.name,
                        'value': cv.value,
                        'quantity': cv.quantity
                    }
                    for cv in item.customizations.all()
                ]
            }
            for item in order.items.all()
        ]
    }

    payload['message'] = 'Order placed successfully.'
    payload['data'] = data
    return Response(payload, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def change_order_status(request, order_id):
    """
    View to change the status of an order.
    Allowed statuses: Pending, Shipped, Delivered, Cancelled
    """
    payload = {}
    data = {}

    try:
        # Retrieve the order based on the order_id (URL parameter)
        order = Order.objects.get(id=order_id)

        # Check if the authenticated user is authorized to update the order status
        # Assuming different roles: admin, chef, dispatch driver, etc.
        user = request.user
        
        # Only allow the status change for certain roles
        # Customize this based on your requirements (admin, chef, dispatch, etc.)
        if not user.is_staff:  # Example: Only allow staff (admin, chef, etc.)
            payload['message'] = 'You do not have permission to change the order status.'
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Get the new status from the request data
        new_status = request.data.get('status')

        # Validate the new status
        if new_status not in dict(status_choices).keys():
            payload['message'] = f"Invalid status: {new_status}. Valid statuses are: {', '.join(dict(status_choices).keys())}"
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update the order's status
        order.status = new_status
        order.save()

        # Create an OrderStatus entry to track the status change
        OrderStatus.objects.create(
            order=order,
            status=new_status
        )

        # Prepare the response data
        data['order_id'] = order.id
        data['order_status'] = order.status
        data['message'] = 'Order status updated successfully.'

        return Response(data, status=status.HTTP_200_OK)




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

        try:
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

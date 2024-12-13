
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from food.api.serializers import AllFoodCategorysSerializer
from food.models import FoodCategory

User = get_user_model()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_cart_item(request):
    payload = {}
    errors = {}

    if request.method == 'POST':
        # Extract fields from the request body
        dish_id = request.data.get('dish')
        quantity = request.data.get('quantity')
        is_custom = request.data.get('is_custom', False)
        special_notes = request.data.get('special_notes', '')
        customizations = request.data.get('customizations', [])

        # Validate required fields
        if not dish_id:
            errors['dish'] = ['Dish is required.']
        if not quantity or quantity <= 0:
            errors['quantity'] = ['Quantity must be greater than 0.']
        if is_custom and not customizations:
            errors['customizations'] = ['Customizations are required when the item is custom.']

        if errors:
            return Response({
                'message': "Validation Errors",
                'errors': errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # Fetch the authenticated user's cart (or create it if it doesn't exist)
        client = request.user.client  # Assuming user has a one-to-one relationship with Client
        cart, created = Cart.objects.get_or_create(client=client)

        try:
            # Fetch the Dish object
            dish = Dish.objects.get(id=dish_id)
        except Dish.DoesNotExist:
            return Response({
                'message': "Dish Not Found",
                'errors': {'dish': ['Dish not found.']}
            }, status=status.HTTP_404_NOT_FOUND)

        # Create CartItem object
        cart_item = CartItem(
            cart=cart,
            dish=dish,
            quantity=quantity,
            is_custom=is_custom,
            special_notes=special_notes
        )

        # Save the CartItem
        cart_item.save()

        # Handle customizations if the item is custom
        if is_custom and customizations:
            try:
                customization_values = []
                for customization in customizations:
                    # Extract the customization ID and quantity
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

                # Assign customizations to the cart item
                cart_item.customizations.set(customization_values)
            except CustomizationValue.DoesNotExist:
                cart_item.delete()  # Clean up if error occurs
                return Response({
                    'message': "Customization Error",
                    'errors': {'customizations': ['One or more customizations not found.']}
                }, status=status.HTTP_404_NOT_FOUND)
            except ValidationError as e:
                cart_item.delete()  # Clean up if validation fails
                return Response({
                    'message': "Invalid Customization Quantity",
                    'errors': {'customizations': [str(e)]}
                }, status=status.HTTP_400_BAD_REQUEST)

        # Prepare response data
        data = {
            "id": cart_item.id,
            "dish": cart_item.dish.name,
            "quantity": cart_item.quantity,
            "special_notes": cart_item.special_notes,
            "customizations": [
                {"customization": cv.customization_option.name, "value": cv.value, "quantity": cv.quantity}
                for cv in cart_item.customizations.all()
            ],
            "total_price": cart_item.total_price()  # Calculate total price
        }

        # Return success response
        return Response({
            'message': "Item added to cart successfully.",
            'data': data
        }, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_carts_view(request):
    """
    View to retrieve all carts, with an optional filter by client.
    """
    payload = {}
    data = []

    # Get the 'client_id' from query parameters (if provided)
    client_id = request.query_params.get('client', None)

    # If client_id is provided, filter carts by client
    if client_id:
        try:
            client = Client.objects.get(id=client_id)
            carts = Cart.objects.filter(client=client)
        except Client.DoesNotExist:
            payload['message'] = "Client not found."
            return Response(payload, status=status.HTTP_404_NOT_FOUND)
    else:
        # If no client_id is provided, retrieve all carts
        carts = Cart.objects.all()

    if not carts:
        payload['message'] = "No carts found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    # Loop through each cart and get cart items
    for cart in carts:
        # Fetch all CartItems for the current cart
        cart_items = CartItem.objects.filter(cart=cart)

        cart_data = {
            'cart_id': cart.id,
            'created_at': cart.created_at,
            'cart_items': []
        }

        for item in cart_items:
            # For each CartItem, fetch relevant details
            cart_item_data = {
                'id': item.id,
                'dish': item.dish.name,  # Assuming 'dish' has a 'name' field
                'quantity': item.quantity,
                'special_notes': item.special_notes,
                'customizations': [cv.value for cv in item.customizations.all()],
                'total_price': item.total_price()
            }
            cart_data['cart_items'].append(cart_item_data)

        # Add this cart data to the response data
        data.append(cart_data)

    payload['message'] = "Success"
    payload['data'] = data
    return Response(payload, status=status.HTTP_200_OK)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_cart_detail_view(request, cart_id):
    """
    View to retrieve detailed information about a specific cart, including:
    - Client details
    - Cart item details (with customizations)
    - Cart total price
    """
    payload = {}
    data = {}

    try:
        # Fetch the cart based on the cart_id (which is passed as a URL parameter)
        cart = Cart.objects.get(id=cart_id)

        # Get the client associated with the cart
        client = cart.client
        client_data = {
            'client_id': client.id,
            'client_name': client.user.first_name + ' ' + client.user.last_name,
            'client_email': client.user.email,
        }

        # Fetch all CartItems for the current cart
        cart_items = CartItem.objects.filter(cart=cart)

        cart_item_details = []
        cart_total = 0  # Variable to keep track of the total price of the cart

        for item in cart_items:
            # For each CartItem, get the relevant details
            cart_item_data = {
                'id': item.id,
                'dish': item.dish.name,  # Assuming 'dish' has a 'name' field
                'dish_description': item.dish.description,  # Assuming 'dish' has a 'description' field
                'quantity': item.quantity,
                'special_notes': item.special_notes,
                'customizations': [],
                'total_price': item.total_price(),
            }

            # Get all customizations for this CartItem
            for customization_value in item.customizations.all():
                cart_item_data['customizations'].append({
                    'customization_option': customization_value.customization_option.name,
                    'customization_value': customization_value.value,
                })

            # Add the cart item data to the list
            cart_item_details.append(cart_item_data)

            # Add the item's total price to the cart's total price
            cart_total += item.total_price()

        # Construct the response data
        data['cart_id'] = cart.id
        data['created_at'] = cart.created_at
        data['client'] = client_data
        data['cart_items'] = cart_item_details
        data['cart_total'] = cart_total

        payload['message'] = "Success"
        payload['data'] = data
        return Response(payload, status=status.HTTP_200_OK)

    except Cart.DoesNotExist:
        payload['message'] = "Cart not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def cart_item_detail_view(request, cart_id, item_id):
    """
    View to get the details of a specific cart item.
    """
    payload = {}

    try:
        # Retrieve the cart based on the cart_id (URL parameter)
        cart = Cart.objects.get(id=cart_id)

        # Ensure the cart belongs to the authenticated user
        if cart.client.user != request.user:
            payload['message'] = "You do not have permission to view this cart."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Retrieve the specific cart item based on the item_id
        cart_item = CartItem.objects.get(id=item_id, cart=cart)

        # Prepare the data to return
        cart_item_data = {
            "id": cart_item.id,
            "dish": cart_item.dish.name,  # The name of the dish in the cart item
            "quantity": cart_item.quantity,  # The quantity of this cart item
            "special_notes": cart_item.special_notes,  # Special notes for the cart item
            "customizations": [cv.value for cv in cart_item.customizations.all()],  # List of applied customizations
            "total_price": str(cart_item.total_price())  # The total price for this cart item
        }

        payload['message'] = "Cart item details retrieved successfully."
        payload['data'] = cart_item_data
        return Response(payload, status=status.HTTP_200_OK)

    except Cart.DoesNotExist:
        payload['message'] = "Cart not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)
    except CartItem.DoesNotExist:
        payload['message'] = "Cart item not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)



@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_cart_view(request, cart_id):
    """
    View to edit an existing cart, allowing users to update:
    - Cart items (quantity, special notes)
    - Customizations for cart items
    - Adding/removing items in the cart
    """
    payload = {}
    data = {}

    try:
        # Retrieve the cart based on the cart_id (URL parameter)
        cart = Cart.objects.get(id=cart_id)

        # Ensure the cart belongs to the authenticated user
        if cart.client.user != request.user:
            payload['message'] = "You do not have permission to edit this cart."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # List to track updated CartItems
        updated_cart_items = []

        # Loop through the provided cart items data from the request
        for item_data in request.data.get('cart_items', []):
            # Check if cart item ID is provided for update or if it's a new item
            item_id = item_data.get('id', None)

            # If updating an existing item
            if item_id:
                try:
                    cart_item = CartItem.objects.get(id=item_id, cart=cart)
                    
                    # Update the cart item fields
                    if 'quantity' in item_data:
                        cart_item.quantity = item_data['quantity']
                    if 'special_notes' in item_data:
                        cart_item.special_notes = item_data['special_notes']
                    
                    # Clear and update customizations if provided
                    if 'customizations' in item_data:
                        customizations = item_data['customizations']
                        # Validate and add the customizations
                        valid_customizations = []
                        for customization_id in customizations:
                            try:
                                customization = CustomizationValue.objects.get(id=customization_id)
                                valid_customizations.append(customization)
                            except CustomizationValue.DoesNotExist:
                                raise ValidationError(f"Invalid customization ID: {customization_id}")
                        cart_item.customizations.set(valid_customizations)

                    cart_item.save()  # Save the updated cart item
                    updated_cart_items.append(cart_item)

                except CartItem.DoesNotExist:
                    payload['message'] = f"Cart item with ID {item_id} not found."
                    return Response(payload, status=status.HTTP_404_NOT_FOUND)

            # If it's a new item to be added to the cart
            else:
                # Ensure the dish ID is provided and is valid
                dish_id = item_data.get('dish', None)
                quantity = item_data.get('quantity', 1)
                special_notes = item_data.get('special_notes', "")
                customizations = item_data.get('customizations', [])

                if not dish_id:
                    payload['message'] = "Dish ID is required for new items."
                    return Response(payload, status=status.HTTP_400_BAD_REQUEST)

                try:
                    # Assuming `Dish` model exists with an `id` field
                    dish = Dish.objects.get(id=dish_id)
                except Dish.DoesNotExist:
                    payload['message'] = "Dish not found."
                    return Response(payload, status=status.HTTP_404_NOT_FOUND)

                # Create new CartItem and link to the current cart
                new_cart_item = CartItem.objects.create(
                    cart=cart,
                    dish=dish,
                    quantity=quantity,
                    special_notes=special_notes,
                )

                # Add customizations if provided
                if customizations:
                    valid_customizations = []
                    for customization_id in customizations:
                        try:
                            customization = CustomizationValue.objects.get(id=customization_id)
                            valid_customizations.append(customization)
                        except CustomizationValue.DoesNotExist:
                            raise ValidationError(f"Invalid customization ID: {customization_id}")
                    new_cart_item.customizations.set(valid_customizations)

                new_cart_item.save()  # Save the new cart item
                updated_cart_items.append(new_cart_item)

        # Remove any cart items if 'remove_items' are provided
        for item_id in request.data.get('remove_items', []):
            try:
                cart_item = CartItem.objects.get(id=item_id, cart=cart)
                cart_item.delete()
            except CartItem.DoesNotExist:
                payload['message'] = f"Cart item with ID {item_id} not found for removal."
                return Response(payload, status=status.HTTP_404_NOT_FOUND)

        # Prepare the updated cart data to return in the response
        cart_data = {
            'cart_id': cart.id,
            'created_at': cart.created_at,
            'cart_items': [],
            'cart_total': 0,
        }

        # Calculate the total price of the cart after update
        for cart_item in updated_cart_items:
            item_data = {
                'id': cart_item.id,
                'dish': cart_item.dish.name,
                'quantity': cart_item.quantity,
                'special_notes': cart_item.special_notes,
                'customizations': [cv.value for cv in cart_item.customizations.all()],
                'total_price': cart_item.total_price(),
            }
            cart_data['cart_items'].append(item_data)
            cart_data['cart_total'] += cart_item.total_price()

        payload['message'] = "Cart updated successfully"
        payload['data'] = cart_data
        return Response(payload, status=status.HTTP_200_OK)

    except Cart.DoesNotExist:
        payload['message'] = "Cart not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        payload['message'] = str(e)
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)




@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_cart_item_view(request, cart_id, item_id):
    """
    View to edit an existing cart item, allowing users to update:
    - Quantity
    - Special notes
    - Customizations for the cart item
    """
    payload = {}

    try:
        # Retrieve the cart based on the cart_id (URL parameter)
        cart = Cart.objects.get(id=cart_id)

        # Ensure the cart belongs to the authenticated user
        if cart.client.user != request.user:
            payload['message'] = "You do not have permission to edit this cart."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Retrieve the specific cart item based on the item_id
        cart_item = CartItem.objects.get(id=item_id, cart=cart)

        # Validate and update the cart item fields
        quantity = request.data.get('quantity', None)
        special_notes = request.data.get('special_notes', None)
        customizations = request.data.get('customizations', [])

        # If quantity is provided, validate and update it
        if quantity is not None:
            if not isinstance(quantity, int) or quantity <= 0:
                payload['message'] = "Quantity must be a positive integer."
                return Response(payload, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = quantity

        # If special_notes is provided, update it
        if special_notes is not None:
            cart_item.special_notes = special_notes

        # If customizations are provided, validate and update them
        if customizations:
            valid_customizations = []
            for customization_id in customizations:
                try:
                    customization = CustomizationValue.objects.get(id=customization_id)
                    valid_customizations.append(customization)
                except CustomizationValue.DoesNotExist:
                    raise ValidationError(f"Invalid customization ID: {customization_id}")
            cart_item.customizations.set(valid_customizations)

        # Save the updated cart item
        cart_item.save()

        # Prepare the response data
        updated_cart_item_data = {
            "id": cart_item.id,
            "dish": cart_item.dish.name,
            "quantity": cart_item.quantity,
            "special_notes": cart_item.special_notes,
            "customizations": [cv.value for cv in cart_item.customizations.all()],
            "total_price": str(cart_item.total_price())
        }

        payload['message'] = "Cart item updated successfully."
        payload['data'] = updated_cart_item_data
        return Response(payload, status=status.HTTP_200_OK)

    except Cart.DoesNotExist:
        payload['message'] = "Cart not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    except CartItem.DoesNotExist:
        payload['message'] = "Cart item not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

    except ValidationError as e:
        payload['message'] = str(e)
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_cart_view(request, cart_id):
    """
    View to delete a cart and all its associated cart items.
    """
    payload = {}

    try:
        # Retrieve the cart based on the cart_id (URL parameter)
        cart = Cart.objects.get(id=cart_id)

        # Ensure the cart belongs to the authenticated user
        if cart.client.user != request.user:
            payload['message'] = "You do not have permission to delete this cart."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Delete all cart items associated with this cart
        CartItem.objects.filter(cart=cart).delete()

        # Delete the cart itself
        cart.delete()

        payload['message'] = "Cart deleted successfully."
        return Response(payload, status=status.HTTP_204_NO_CONTENT)

    except Cart.DoesNotExist:
        payload['message'] = "Cart not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)



@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_cart_item_view(request, cart_id, item_id):
    """
    View to delete a specific cart item from the cart.
    """
    payload = {}

    try:
        # Retrieve the cart based on the cart_id (URL parameter)
        cart = Cart.objects.get(id=cart_id)

        # Ensure the cart belongs to the authenticated user
        if cart.client.user != request.user:
            payload['message'] = "You do not have permission to delete items from this cart."
            return Response(payload, status=status.HTTP_403_FORBIDDEN)

        # Retrieve the cart item based on the item_id
        cart_item = CartItem.objects.get(id=item_id, cart=cart)

        # Delete the cart item
        cart_item.delete()

        payload['message'] = "Cart item deleted successfully."
        return Response(payload, status=status.HTTP_204_NO_CONTENT)

    except Cart.DoesNotExist:
        payload['message'] = "Cart not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)
    except CartItem.DoesNotExist:
        payload['message'] = "Cart item not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)

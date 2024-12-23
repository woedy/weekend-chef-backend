
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.forms import ValidationError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication


from activities.models import AllActivity
from chef.models import ChefProfile
from clients.models import Client
from food.api.serializers import AllFoodCategorysSerializer
from food.models import Dish, FoodCategory
from orders.models import Cart, CartItem, CustomizationOption, CustomizationValue

User = get_user_model()





@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def add_cart_item(request):
    payload = {}
    errors = {}

    if request.method == 'POST':
        # Extract fields from the request body
        client_id = request.data.get('client_id')
        chef_id = request.data.get('chef_id')
        dish_id = request.data.get('dish_id')
        quantity = request.data.get('quantity')
        is_custom = request.data.get('is_custom', False)
        special_notes = request.data.get('special_notes', '')
        customizations = request.data.get('customizations', [])

        # Perform initial validation
        if not dish_id:
            errors['dish_id'] = ['Dish ID is required.']
        if not client_id:
            errors['client_id'] = ['Client ID is required.']
        if not chef_id:
            errors['chef_id'] = ['Chef ID is required.']

        if not quantity or quantity <= 0:
            errors['quantity'] = ['Quantity must be greater than 0.']

        if not isinstance(is_custom, bool):
            errors['is_custom'] = ['Is custom must be a boolean value.']

        if is_custom and not customizations:
            errors['customizations'] = ['Customizations are required when the item is custom.']

        # Validate the existence of client, chef, and dish
        try:
            client = Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            errors['client_id'] = ['Client does not exist.']

        try:
            chef = ChefProfile.objects.get(chef_id=chef_id)
        except ChefProfile.DoesNotExist:
            errors['chef_id'] = ['Chef does not exist.']

        try:
            dish = Dish.objects.get(dish_id=dish_id)
        except Dish.DoesNotExist:
            errors['dish_id'] = ['Dish does not exist.']

        if errors:
            payload['message'] = "Validation Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Create or get the client's cart
        cart, created = Cart.objects.get_or_create(client=client)

        # Create CartItem object
        cart_item = CartItem(
            cart=cart,
            dish=dish,
            chef=chef,
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
                    # Extract customization details
                    custom_option_id = customization.get('custom_option_id')
                    custom_quantity = customization.get('quantity', 1)  # Default to 1 if no quantity is provided

                    # Ensure customization quantity is valid
                    if custom_quantity <= 0:
                        raise ValidationError("Customization quantity must be greater than 0.")

                    # Fetch the CustomizationOption object
                    try:
                        customization_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
                    except CustomizationOption.DoesNotExist:
                        raise ValidationError(f"Customization option with ID {custom_option_id} does not exist.")

                    # Create a CustomizationValue for this customization option
                    customization_value = CustomizationValue(
                        customization_option=customization_option,
                        quantity=custom_quantity
                    )

                    # Ensure customization_value is valid before adding
                    if not customization_value.customization_option or customization_value.quantity <= 0:
                        raise ValidationError("Invalid customization value.")

                    # Save the customization value before appending to the list
                    customization_value.save()
                    customization_values.append(customization_value)

                # Assign customizations to the cart item
                if customization_values:
                    cart_item.customizations.set(customization_values)

            except CustomizationOption.DoesNotExist:
                cart_item.delete()  # Clean up if error occurs
                return Response({
                    'message': "Customization Error",
                    'errors': {'customizations': ['One or more customizations not found.']},
                }, status=status.HTTP_404_NOT_FOUND)

            except ValidationError as e:
                cart_item.delete()  # Clean up if validation fails
                return Response({
                    'message': "Invalid Customization Quantity",
                    'errors': {'customizations': [str(e)]},
                }, status=status.HTTP_400_BAD_REQUEST)

        # Prepare response data
        data = {
            "id": cart_item.id,
            "dish": cart_item.dish.name,
            "quantity": cart_item.quantity,
            "special_notes": cart_item.special_notes,
            "customizations": [
                {"customization": cv.customization_option.name, "quantity": cv.quantity}
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
    View to retrieve all carts with optional search by client and pagination.
    """
    payload = {}
    data = {}
    errors = {}

    # Get search, client_id, and pagination parameters from query parameters
    search_query = request.query_params.get('search', '')
    client_id = request.query_params.get('client_id', None)
    page_number = request.query_params.get('page', 1)
    page_size = 10  # You can adjust the page size as needed

    # Start with all carts, if no client filter is provided
    carts = Cart.objects.all()

    # If a client_id is provided, filter carts by client
    if client_id:
        try:
            client = Client.objects.get(client_id=client_id)
            carts = carts.filter(client=client)
        except Client.DoesNotExist:
            errors['client_id'] = ['Client not found.']
            payload['message'] = "Client not found."
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_404_NOT_FOUND)

    # Apply search query if provided
    if search_query:
        carts = carts.filter(
            Q(client__user__first_name__icontains=search_query) |  # Assuming searching by client's first name
            Q(client__user__last_name__icontains=search_query)   # Searching by client's last name
        ).distinct()

    # Pagination
    paginator = Paginator(carts, page_size)

    try:
        paginated_carts = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_carts = paginator.page(1)
    except EmptyPage:
        paginated_carts = paginator.page(paginator.num_pages)

    # Prepare data for response
    cart_data = []
    for cart in paginated_carts:
        cart_items = CartItem.objects.filter(cart=cart)

        cart_item_data = []
        for item in cart_items:
            cart_item_data.append({
                'id': item.id,
                'dish': item.dish.name,
                'quantity': item.quantity,
                'special_notes': item.special_notes,
                'customizations': [cv.quantity for cv in item.customizations.all()],
                'total_price': item.total_price()
            })

        cart_data.append({
            'cart_id': cart.id,
            'created_at': cart.created_at,
            'cart_items': cart_item_data
        })

    # Constructing pagination info
    data['carts'] = cart_data
    data['pagination'] = {
        'page_number': paginated_carts.number,
        'total_pages': paginator.num_pages,
        'next': paginated_carts.next_page_number() if paginated_carts.has_next() else None,
        'previous': paginated_carts.previous_page_number() if paginated_carts.has_previous() else None,
    }

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
def cart_item_detail_view(request):
    """
    View to retrieve the details of a specific cart item by its ID.
    """
    payload = {}
    
    item_id = request.query_params.get('item_id', None)

    try:
        # Retrieve the CartItem by its ID
        cart_item = CartItem.objects.get(id=item_id)
        
        # Prepare the data to return in the response
        cart_item_data = {
            'id': cart_item.id,
            'dish': cart_item.dish.name,  # Assuming dish has a 'name' field
            'quantity': cart_item.quantity,
            'special_notes': cart_item.special_notes,
            'customizations': [
                {
                    'customization_option': cv.customization_option.name,
                    'quantity': cv.quantity,
                }
                for cv in cart_item.customizations.all()
            ],
            'total_price': cart_item.total_price()  # Assuming total_price method exists in CartItem
        }

        payload['message'] = "Cart Item retrieved successfully."
        payload['data'] = cart_item_data
        return Response(payload, status=status.HTTP_200_OK)
    
    except CartItem.DoesNotExist:
        # Handle the case where the CartItem is not found
        payload['message'] = "CartItem not found."
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




@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def edit_cart_item_view(request):
    payload = {}
    errors = {}

    if request.method == 'POST':
        # Extract fields from the request body
        cart_item_id = request.data.get('cart_item_id')
        quantity = request.data.get('quantity')
        special_notes = request.data.get('special_notes', '')
        customizations = request.data.get('customizations', [])

        # Perform initial validation
        if not cart_item_id:
            errors['cart_item_id'] = ['Cart Item ID is required.']
        
        if quantity is None or quantity <= 0:
            errors['quantity'] = ['Quantity must be greater than 0.']

        if errors:
            payload['message'] = "Validation Errors"
            payload['errors'] = errors
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Locate the cart item by ID
        try:
            cart_item = CartItem.objects.get(id=cart_item_id)
        except CartItem.DoesNotExist:
            return Response({
                'message': "Cart Item Not Found",
                'errors': {'cart_item_id': ['Cart item with the provided ID does not exist.']}
            }, status=status.HTTP_404_NOT_FOUND)

        # Update cart item fields
        cart_item.quantity = quantity
        cart_item.special_notes = special_notes

        # Handle customizations if provided
        if customizations:
            try:
                # Remove existing customizations first
                cart_item.customizations.clear()

                customization_values = []
                for customization in customizations:
                    # Extract customization details
                    custom_option_id = customization.get('custom_option_id')
                    custom_quantity = customization.get('quantity', 1)

                    # Validate customization quantity
                    if custom_quantity <= 0:
                        raise ValidationError("Customization quantity must be greater than 0.")

                    try:
                        customization_option = CustomizationOption.objects.get(custom_option_id=custom_option_id)
                    except CustomizationOption.DoesNotExist:
                        raise ValidationError(f"Customization option with ID {custom_option_id} does not exist.")

                    # Create and save CustomizationValue
                    customization_value = CustomizationValue(
                        customization_option=customization_option,
                        quantity=custom_quantity
                    )
                    customization_value.save()
                    customization_values.append(customization_value)

                # Assign new customizations
                if customization_values:
                    cart_item.customizations.set(customization_values)

            except CustomizationOption.DoesNotExist:
                return Response({
                    'message': "Customization Error",
                    'errors': {'customizations': ['One or more customizations not found.']},
                }, status=status.HTTP_404_NOT_FOUND)

            except ValidationError as e:
                return Response({
                    'message': "Invalid Customization Quantity",
                    'errors': {'customizations': [str(e)]},
                }, status=status.HTTP_400_BAD_REQUEST)

        # Save the updated cart item
        cart_item.save()

        # Prepare the updated response data
        data = {
            "id": cart_item.id,
            "dish": cart_item.dish.name,
            "quantity": cart_item.quantity,
            "special_notes": cart_item.special_notes,
            "customizations": [
                {"customization": cv.customization_option.name, "quantity": cv.quantity}
                for cv in cart_item.customizations.all()
            ],
            "total_price": cart_item.total_price()  # Recalculate total price
        }

        # Return success response
        return Response({
            'message': "Cart item updated successfully.",
            'data': data
        }, status=status.HTTP_200_OK)


@api_view(['POST'])
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

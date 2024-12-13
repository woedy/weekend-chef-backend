from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import CustomizationOption
from django.core.exceptions import ValidationError

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def create_customization_option(request):
    """
    Create a new customization option.
    """
    payload = {}
    data = {}

    # Get data from the request body
    option_type = request.data.get('option_type', '')
    name = request.data.get('name', '')
    description = request.data.get('description', '')
    price = request.data.get('price', 0)

    if not option_type or not name:
        payload['message'] = 'Option Type and Name are required.'
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Validate price (it should be a positive number)
    try:
        price = float(price)
        if price < 0:
            raise ValidationError("Price cannot be negative.")
    except ValueError:
        payload['message'] = 'Invalid price.'
        return Response(payload, status=status.HTTP_400_BAD_REQUEST)

    # Create a new CustomizationOption object
    customization_option = CustomizationOption.objects.create(
        option_type=option_type,
        name=name,
        description=description,
        price=price
    )

    data['id'] = customization_option.id
    data['option_type'] = customization_option.option_type
    data['name'] = customization_option.name
    data['description'] = customization_option.description
    data['price'] = customization_option.price

    payload['message'] = "Customization option created successfully."
    payload['data'] = data
    return Response(payload, status=status.HTTP_201_CREATED)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_all_customization_options(request):
    """
    Get all customization options.
    """
    payload = {}
    data = []

    # Fetch all customization options
    customization_options = CustomizationOption.objects.all()

    # Prepare data to send back
    for option in customization_options:
        option_data = {
            'id': option.id,
            'option_type': option.option_type,
            'name': option.name,
            'description': option.description,
            'price': str(option.price),
        }
        data.append(option_data)

    payload['message'] = "Customization options retrieved successfully."
    payload['data'] = data
    return Response(payload, status=status.HTTP_200_OK)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def get_customization_option(request, option_id):
    """
    Get a specific customization option by its ID.
    """
    payload = {}

    try:
        # Fetch the customization option by ID
        customization_option = CustomizationOption.objects.get(id=option_id)

        # Prepare the data to send back
        data = {
            'id': customization_option.id,
            'option_type': customization_option.option_type,
            'name': customization_option.name,
            'description': customization_option.description,
            'price': str(customization_option.price),
        }

        payload['message'] = "Customization option retrieved successfully."
        payload['data'] = data
        return Response(payload, status=status.HTTP_200_OK)

    except CustomizationOption.DoesNotExist:
        payload['message'] = "Customization option not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def update_customization_option(request, option_id):
    """
    Update an existing customization option by its ID.
    """
    payload = {}

    try:
        # Fetch the customization option by ID
        customization_option = CustomizationOption.objects.get(id=option_id)

        # Get new data from the request body
        option_type = request.data.get('option_type', customization_option.option_type)
        name = request.data.get('name', customization_option.name)
        description = request.data.get('description', customization_option.description)
        price = request.data.get('price', customization_option.price)

        # Validate price
        try:
            price = float(price)
            if price < 0:
                raise ValidationError("Price cannot be negative.")
        except ValueError:
            payload['message'] = 'Invalid price.'
            return Response(payload, status=status.HTTP_400_BAD_REQUEST)

        # Update the customization option fields
        customization_option.option_type = option_type
        customization_option.name = name
        customization_option.description = description
        customization_option.price = price

        # Save the updated customization option
        customization_option.save()

        # Prepare the updated data to return
        data = {
            'id': customization_option.id,
            'option_type': customization_option.option_type,
            'name': customization_option.name,
            'description': customization_option.description,
            'price': str(customization_option.price),
        }

        payload['message'] = "Customization option updated successfully."
        payload['data'] = data
        return Response(payload, status=status.HTTP_200_OK)

    except CustomizationOption.DoesNotExist:
        payload['message'] = "Customization option not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)






@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@authentication_classes([TokenAuthentication])
def delete_customization_option(request, option_id):
    """
    Delete a customization option by its ID.
    """
    payload = {}

    try:
        # Fetch the customization option by ID
        customization_option = CustomizationOption.objects.get(id=option_id)

        # Delete the customization option
        customization_option.delete()

        payload['message'] = "Customization option deleted successfully."
        return Response(payload, status=status.HTTP_204_NO_CONTENT)

    except CustomizationOption.DoesNotExist:
        payload['message'] = "Customization option not found."
        return Response(payload, status=status.HTTP_404_NOT_FOUND)
